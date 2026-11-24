"""Train on the 15 PhysDrive RGB/BVP/HR packs, one full session at a time."""
import argparse
import copy
import hashlib
import io
import json
import os
import random
import re
import shutil
import tempfile
import time
from collections import Counter
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from zipfile import ZipFile

import cv2
import numpy as np
import torch
from scipy.io import loadmat

from dl_common import CHUNK, build_model, chunk_starts, hr_from_bvp, predict_video, to_input
from dl_prepare import crop_video
from dl_train import neg_pearson

SUFFIXES = ("Video/RGB.mp4", "Label/BVP.mat", "Label/HR.mat")
# SHA-256 of the sorted session IDs, component names and original byte lengths.
INVENTORY = "ce76dc5c25257e903bb169eff61424768081970df146fd51145909fb4d0d3069"
PACK_PATTERN = re.compile(r"PhysDrive_RGB_BVP_HR_(\d{2})_of_15\.zip$", re.I)
PERSON = re.compile(r"[ABC][FM][A-Z]\d+")


@dataclass(frozen=True)
class Session:
    source: Path
    prefix: str = ""  # For a ZIP, internal path to the session. Otherwise source is the session folder.


def fingerprint(value):
    data = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(data).hexdigest()


def discover(root):
    found, sizes = {}, {}

    def add(person, scene, source, lengths):
        key = f"{person}/{scene}"
        if key in found and found[key] != source:
            if sizes[key] != lengths or bool(source.prefix) == bool(found[key].prefix):
                raise ValueError(f"Çakışan oturum {key}: {found[key]} / {source}")
            if source.prefix:  # The same files are also accessible as an expanded input.
                return
        found[key], sizes[key] = source, lengths

    slots = set()
    for path in sorted(root.rglob("*_of_15.zip")):
        match = PACK_PATTERN.fullmatch(path.name)
        if not match:
            continue
        slot = int(match[1])
        if slot not in range(1, 16):
            raise ValueError(f"Beklenmeyen paket: {path.name}")
        slots.add(slot)
        path = path.resolve()
        with ZipFile(path) as z:
            for name in z.namelist():
                if not name.endswith("/Video/RGB.mp4") or "__MACOSX" in PurePosixPath(name).parts:
                    continue
                prefix = name.removesuffix("/Video/RGB.mp4")
                person, scene = PurePosixPath(prefix).parts[-2:]
                lengths = {s.split("/")[-1]: z.getinfo(f"{prefix}/{s}").file_size for s in SUFFIXES}
                add(person, scene, Session(path, prefix), lengths)
    for rgb in root.rglob("RGB.mp4"):
        if rgb.parent.name != "Video" or "__MACOSX" in rgb.parts:
            continue
        folder = rgb.parents[1]
        if not PERSON.fullmatch(folder.parent.name) or not re.fullmatch("[ABC][ST]", folder.name):
            continue
        lengths = {s.split("/")[-1]: (folder / s).stat().st_size for s in SUFFIXES}
        add(folder.parent.name, folder.name, Session(folder.resolve()), lengths)
    if fingerprint(sizes) != INVENTORY:
        raise ValueError(f"Girdi eksik veya farklı. {len(found)}/283 oturum, "
                         f"ZIP olarak görülen paketler: {sorted(slots)}. "
                         "Açılmış klasörler de sayıldı. Add Input ile 15 paketin hepsini bağlayın.")
    return found


@contextmanager
def session_files(session):
    if not session.prefix:
        yield tuple(session.source / s for s in SUFFIXES)
        return
    with tempfile.TemporaryDirectory(prefix="physdrive_") as tmp, ZipFile(session.source) as z:
        rgb = Path(tmp, "RGB.mp4")
        with z.open(session.prefix + "/" + SUFFIXES[0]) as src, rgb.open("wb") as dst:
            shutil.copyfileobj(src, dst, length=1024 * 1024)
        yield (rgb, *(io.BytesIO(z.read(session.prefix + "/" + s)) for s in SUFFIXES[1:]))


class UnusableSession(ValueError):
    """Only documented data-quality exclusions may skip a session."""


def read_session(session):
    with session_files(session) as (video, bvp_file, hr_file):
        bvp = np.asarray(loadmat(bvp_file)["BVP"], dtype=np.float32).ravel()
        hr = np.asarray(loadmat(hr_file)["HR"], dtype=np.float32).ravel()
        cap = cv2.VideoCapture(str(video))
        try:
            if not cap.isOpened():
                raise OSError(f"RGB video açılamadı: {video}")
            fps, n = cap.get(cv2.CAP_PROP_FPS), int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        finally:
            cap.release()
        if not np.isfinite(fps) or abs(fps - 30) > 0.05 or max(n, len(bvp), len(hr)) - min(n, len(bvp), len(hr)) > 30:
            raise UnusableSession(f"zamanlama: fps={fps:.3f}, RGB={n}, BVP={len(bvp)}, HR={len(hr)}")
        n = min(n, len(bvp), len(hr))
        if n < 300:
            raise UnusableSession(f"10 saniyeden kısa: {n} kare")
        frames, rate = crop_video(str(video), max_frames=n, det_scale=2)
        if len(frames) != n:
            raise OSError(f"Çözülen RGB kare sayısı {len(frames)}, beklenen {n}")
        if rate < 0.5:
            raise UnusableSession(f"yüz tespit oranı {rate:.3f} < 0.50")
    return frames, bvp[:n], hr[:n], rate


def splits(sessions):
    people = sorted({k.split("/")[0] for k in sessions})
    random.Random(42).shuffle(people)
    by_person = {p: "test" if i < 8 else "val" if i < 16 else "train" for i, p in enumerate(people)}
    return {k: by_person[k.split("/")[0]] for k in sorted(sessions)}


def fit_session(model, opt, frames, bvp, batch_size, seed):
    device = next(model.parameters()).device
    starts = chunk_starts(len(frames), CHUNK)
    random.Random(seed).shuffle(starts)
    valid = [s for s in starts if np.isfinite(bvp[s:s+CHUNK]).all() and bvp[s:s+CHUNK].std() > 1e-6]
    if not valid:
        raise UnusableSession("Geçerli BVP penceresi yok")
    model.train()
    total_loss = 0.0
    for i in range(0, len(valid), batch_size):
        starts_batch = valid[i:i+batch_size]
        x = to_input(np.stack([frames[s:s+CHUNK] for s in starts_batch]), device)
        y = torch.as_tensor(np.stack([bvp[s:s+CHUNK] for s in starts_batch]), device=device)
        opt.zero_grad(set_to_none=True)
        loss = neg_pearson(model(x)[0], y)
        if not torch.isfinite(loss):
            raise FloatingPointError("Sonlu olmayan eğitim kaybı")
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0, error_if_nonfinite=True)
        opt.step()
        total_loss += loss.item() * len(starts_batch)
    return {"windows": len(valid), "excluded_windows": len(starts)-len(valid), "loss": total_loss/len(valid)}


def score_session(model, frames, hr, batch_size):
    pred = predict_video(model, frames, next(model.parameters()).device, batch=batch_size)
    if not np.isfinite(pred).all():
        raise FloatingPointError("Sonlu olmayan model tahmini")
    centers, estimates, _ = hr_from_bvp(pred, fs=30.0)
    errors = []
    for center, bpm in zip(centers, estimates):
        left = round(center * 30) - 150
        ref = hr[left:left+300]
        valid = np.isfinite(ref) & (ref > 0)
        if valid.sum() >= 150 and np.isfinite(bpm):
            errors.append(abs(float(bpm) - float(np.median(ref[valid]))))
    if not errors:
        raise UnusableSession("Değerlendirme için geçerli HR penceresi yok")
    return {"windows": len(errors), "mae_bpm": float(np.mean(errors))}


def atomic_save(value, path, writer):
    tmp = path.with_suffix(path.suffix + ".part")
    writer(value, tmp)
    os.replace(tmp, path)


def write_json(value, path):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")


def run(sessions, split, args):
    device = torch.device(args.device)
    if device.type == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("Kaggle ayarlarından Accelerator → GPU seçip oturumu yeniden başlatın.")
    name = torch.cuda.get_device_name(device) if device.type == "cuda" else "CPU"
    print(f"Model cihazı: {device} ({name})", flush=True)
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    torch.set_num_threads(min(4, os.cpu_count() or 1))
    torch.manual_seed(42)
    cfg = {"version": 1, "inventory": INVENTORY, "split": split, "epochs": args.epochs,
           "batch": args.batch, "lr": 5e-5, "arch": "factorizephys"}
    checkpoint = out / "physdrive_full_resume.pth"
    resume_from = checkpoint if checkpoint.is_file() else args.resume
    # FactorizePhys registers bias1 as a parameter only when constructed on CPU.
    # Move it afterwards so CPU and CUDA checkpoints share the optimizer layout.
    model = build_model(torch.device("cpu")).to(device)
    for module in model.modules():
        if isinstance(getattr(module, "device", None), torch.device):
            module.device = device  # FSAM uses this attribute when allocating its bases.
    opt = torch.optim.AdamW(model.parameters(), lr=cfg["lr"], weight_decay=1e-4)
    state = {"cfg": cfg, "phase": 0, "next": 0, "rows": [], "scores": [],
             "best_mae": None, "best": None, "last_train": None}
    if resume_from:
        state = torch.load(resume_from, map_location="cpu", weights_only=True)
        if state["cfg"] != cfg:
            raise ValueError("Devam dosyasının deney ayarları farklı")
        model.load_state_dict(state["model"])
        opt.load_state_dict(state["optimizer"])
        torch.set_rng_state(state["rng"])
        if device.type == "cuda" and state.get("cuda_rng") is not None:
            torch.cuda.set_rng_state(state["cuda_rng"], device)
    phases = [(0, "val")]
    for epoch in range(1, args.epochs + 1):
        phases.extend([(epoch, "train"), (epoch, "val")])
    phases.append((args.epochs, "test"))

    def save():
        state.update(model=model.state_dict(), optimizer=opt.state_dict(), rng=torch.get_rng_state())
        state["cuda_rng"] = torch.cuda.get_rng_state(device) if device.type == "cuda" else None
        atomic_save(state, checkpoint, torch.save)
        atomic_save({"phase_index": state["phase"], "next_session": state["next"],
                     "completed": state["phase"] == len(phases), "scores": state["scores"],
                     "sessions": state["rows"]}, out / "rapor.json", write_json)

    def export_weights():
        for key, name in (("best", "best.pth"), ("last_train", "last.pth")):
            if state[key] is not None:
                atomic_save({"arch": cfg["arch"], "model": state[key]}, out / name, torch.save)

    if resume_from:
        export_weights()
        save()
    end = time.monotonic() + args.hours * 3600
    while state["phase"] < len(phases):
        epoch, phase = phases[state["phase"]]
        keys = [k for k in split if split[k] == phase]
        if phase == "train":
            random.Random(42 + epoch).shuffle(keys)
        if phase == "test":
            model.load_state_dict(state["best"])
        for index in range(state["next"], len(keys)):
            if time.monotonic() >= end:
                save()
                print("Süre doldu. Bu çıktıyı sonraki oturuma bağlayarak devam edin.", flush=True)
                return
            key = keys[index]
            row = {"epoch": epoch, "split": phase, "session": key}
            try:
                frames, bvp, hr, rate = read_session(sessions[key])
                row.update(frames=len(frames), face_rate=rate)
                metrics = (fit_session(model, opt, frames, bvp, args.batch, epoch*1000+index)
                           if phase == "train" else score_session(model, frames, hr, args.batch))
                row.update(metrics)
                del frames
            except UnusableSession as exc:
                row["excluded"] = str(exc)
            state["rows"].append(row)
            state["next"] = index + 1
            save()
            print(f"{phase} epoch {epoch} [{index+1}/{len(keys)}] {key} {row}", flush=True)
        rows = [r for r in state["rows"] if r["epoch"] == epoch and r["split"] == phase and "excluded" not in r]
        if not rows:
            raise RuntimeError(f"{phase} için kullanılabilir oturum yok. rapor.json dosyasını inceleyin.")
        metric = "loss" if phase == "train" else "mae_bpm"
        mean = float(np.mean([r[metric] for r in rows]))
        state["scores"].append({"epoch": epoch, "split": phase, metric: mean, "used": len(rows), "total": len(keys)})
        if phase == "val" and (state["best_mae"] is None or mean < state["best_mae"]):
            state["best_mae"], state["best"] = mean, copy.deepcopy(model.state_dict())
        if phase == "train":
            state["last_train"] = copy.deepcopy(model.state_dict())
        export_weights()
        state["phase"] += 1
        state["next"] = 0
        save()
        print(state["scores"][-1], flush=True)
    print("Tamamlandı.", out, flush=True)


def main():
    p = argparse.ArgumentParser(__doc__)
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--out", type=Path, default=Path("/kaggle/working/physdrive_full"))
    p.add_argument("--inventory-only", action="store_true")
    p.add_argument("--device", choices=("cpu", "cuda"), default="cpu")
    p.add_argument("--resume", type=Path)
    p.add_argument("--epochs", type=int, default=3)
    p.add_argument("--batch", type=int, default=2)
    p.add_argument("--hours", type=float, default=9)
    args = p.parse_args()
    if args.epochs < 1 or args.batch < 1 or args.hours <= 0:
        p.error("epochs, batch ve hours pozitif olmalı")
    sessions = discover(args.input)
    split = splits(sessions)
    print("Doğrulanan oturumlar:", len(sessions), dict(Counter(split.values())), flush=True)
    if not args.inventory_only:
        run(sessions, split, args)


if __name__ == "__main__":
    main()

