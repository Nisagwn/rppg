#!/usr/bin/env python
"""
FactorizePhys (rPPG-Toolbox, NeurIPS 2024) ince ayarı: PURE ön-eğitimli ağırlıklardan başlayıp
MCD-rPPG (3 kamera, dinlenme + egzersiz) ve UBFC-rPPG'nin test DIŞI kişileriyle eğitir.

* Veri: scripts/dl_prepare.py çıktıları (data/dl/mcd, data/dl/ubfc). Kişi bazında ayrım:
  kişilerin ~%10'u doğrulama, geri kalanı eğitim. Test kişileri zaten hiç işlenmemiştir.
* Her epoch: videolardan rastgele başlangıçlı 160 karelik parçalar (uzunlukla orantılı örnekleme).
* Artırma: yatay çevirme, hız değişimi (0.8–1.25x; HR dağılımını genişletir), parlaklık ölçeği.
* Kayıp: örnek başına negatif Pearson. MCD etiketi ters çevrilir (bkz. ChunkSampler).
* Seçim: doğrulama videolarında pencere MAE (argmax, 10 s) en düşük epoch -> best.pth
* Dayanıklılık: her epoch sonunda last.pth (model + optimizer + zamanlayıcı); tekrar çalıştırınca devam eder.
  --deadline "2026-09-28 04:15" verilirse o saatte güvenle durur.

    python scripts/dl_train.py --epochs 30 --steps 600 --deadline "2026-09-28 04:15"
"""
import argparse
import glob
import json
import os
import time
import zlib
from datetime import datetime

import numpy as np

from dl_common import CHUNK, build_model, hr_from_bvp, predict_video, reference_hr, to_input


def list_videos(root, min_face=0.5):
    vids = []
    for p in sorted(glob.glob(os.path.join(root, "mcd", "*.npz")) + glob.glob(os.path.join(root, "ubfc", "*.npz"))):
        m = np.load(p)
        if float(m["face_rate"]) < min_face or int(m["n"]) < CHUNK * 2:
            continue
        vids.append({"npz": p, "npy": p[:-4] + ".npy", "n": int(m["n"]), "person": str(m["person"]),
                     "source": str(m["source"]), "camera": str(m["camera"])})
    return vids


def is_val(person):
    return zlib.crc32(person.encode()) % 10 == 0


class ChunkSampler:
    def __init__(self, vids):
        self.vids = vids
        w = np.array([v["n"] for v in vids], dtype=float)
        self.p = w / w.sum()
        self.cache = {}

    def _frames(self, v):
        item = self.cache.get(v["npy"])
        if item is None:  # iş parçacıkları arasında güvenli: çift tek seferde yazılır
            bvp = np.load(v["npz"])["bvp"]
            # MCD parmak PPG'si UBFC/PURE'a göre ters işaretli (ön-eğitimli modelle korelasyon ~ -0.75, gecikme ~0)
            item = (np.load(v["npy"], mmap_mode="r"), -bvp if v["source"] == "mcd" else bvp)
            self.cache[v["npy"]] = item
        return item

    def sample(self, rng):
        v = self.vids[rng.choice(len(self.vids), p=self.p)]
        frames, bvp = self._frames(v)
        speed = rng.uniform(0.8, 1.25) if rng.random() < 0.5 else 1.0
        span = int(np.ceil(CHUNK * speed)) + 1
        span = min(span, len(frames))
        s = rng.integers(0, len(frames) - span + 1)
        clip = np.asarray(frames[s:s + span], dtype=np.float32)
        lab = np.asarray(bvp[s:s + span], dtype=np.float32)
        if speed != 1.0:  # zaman ekseninde yeniden örnekle -> nabız speed katına çıkar
            pos = np.arange(CHUNK) * speed
            pos = np.minimum(pos, len(clip) - 1.001)
            j = pos.astype(int)
            w = (pos - j)[:, None, None, None]
            clip = clip[j] * (1 - w) + clip[j + 1] * w
            lab = np.interp(pos, np.arange(len(lab)), lab)
        else:
            clip, lab = clip[:CHUNK], lab[:CHUNK]
        if rng.random() < 0.5:
            clip = clip[:, :, ::-1]
        clip = np.clip(clip * rng.uniform(0.8, 1.2), 0, 255)
        lab = (lab - lab.mean()) / (lab.std() + 1e-8)
        return clip, lab

    def batch(self, bs, seed):
        rng = np.random.default_rng(seed)  # iş parçacığı başına ayrı üreteç
        xs, ys = zip(*(self.sample(rng) for _ in range(bs)))
        return np.stack(xs), np.stack(ys).astype(np.float32)


class Prefetcher:
    """Batch'leri arka plan iş parçacıklarında önden hazırlar (numpy GIL'i bırakır; GPU ile örtüşür)."""
    def __init__(self, sampler, bs, seed, threads=3, depth=6):
        from collections import deque
        from concurrent.futures import ThreadPoolExecutor
        self.sampler, self.bs, self.seed = sampler, bs, seed
        self.ex = ThreadPoolExecutor(threads)
        self.q = deque(self._submit() for _ in range(depth))

    def _submit(self):
        self.seed += 1
        return self.ex.submit(self.sampler.batch, self.bs, self.seed)

    def next(self):
        f = self.q.popleft()
        self.q.append(self._submit())
        return f.result()

    def close(self):
        self.ex.shutdown(wait=False, cancel_futures=True)


def neg_pearson(pred, lab):
    import torch
    p = pred - pred.mean(dim=1, keepdim=True)
    y = lab - lab.mean(dim=1, keepdim=True)
    r = (p * y).sum(1) / (torch.sqrt((p ** 2).sum(1) * (y ** 2).sum(1)) + 1e-8)
    return (1 - r).mean()


def validate(model, vids, device, max_frames=1800):
    """Doğrulama videolarının ilk 60 s'sinde pencere MAE (argmax)."""
    errs = []
    for v in vids:
        frames = np.load(v["npy"], mmap_mode="r")[:max_frames]
        bvp = np.load(v["npz"])["bvp"][:max_frames]
        pred = predict_video(model, np.asarray(frames), device)
        if pred is None:
            continue
        c, hr_a, _ = hr_from_bvp(pred)
        errs.append(np.mean(np.abs(hr_a - reference_hr(bvp, c))))
    return float(np.mean(errs)) if errs else float("nan")


def main():
    import torch
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/dl")
    ap.add_argument("--out", default="results/derin_ogrenme/egitim")
    ap.add_argument("--epochs", type=int, default=30)
    ap.add_argument("--steps", type=int, default=600, help="epoch başına adım")
    ap.add_argument("--bs", type=int, default=8)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--deadline", default="", help='"YYYY-MM-DD HH:MM": bu saatte güvenle dur')
    ap.add_argument("--val-max", type=int, default=40, help="doğrulamada en çok kaç video")
    a = ap.parse_args()
    deadline = datetime.strptime(a.deadline, "%Y-%m-%d %H:%M").timestamp() if a.deadline else float("inf")

    os.makedirs(a.out, exist_ok=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    vids = list_videos(a.data)
    train = [v for v in vids if not is_val(v["person"])]
    val = [v for v in vids if is_val(v["person"])]
    val = [val[i] for i in np.linspace(0, len(val) - 1, min(a.val_max, len(val))).astype(int)] if val else []
    print(f"eğitim {len(train)} video ({len({v['person'] for v in train})} kişi), "
          f"doğrulama {len(val)} video, cihaz {device}", flush=True)
    if not train:
        raise SystemExit("Eğitim verisi yok: önce scripts/dl_prepare.py --mcd N")

    model = build_model(device)
    opt = torch.optim.AdamW(model.parameters(), lr=a.lr, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=a.epochs * a.steps, eta_min=a.lr / 50)
    state = {"epoch": 0, "best": None, "history": []}
    last = os.path.join(a.out, "last.pth")
    if os.path.exists(last):
        ck = torch.load(last, map_location=device)
        model.load_state_dict(ck["model"])
        opt.load_state_dict(ck["opt"])
        sched.load_state_dict(ck["sched"])
        state = ck["state"]
        print(f"devam: epoch {state['epoch']}", flush=True)
        names = sorted(v["npz"] for v in val)
        if val and state.get("val_set") != names:  # doğrulama kümesi değişti: en iyiyi yeni kümede yeniden ölç
            best_model = build_model(device, os.path.join(a.out, "best.pth"))
            state["best"]["val_mae"] = validate(best_model, val, device)
            del best_model
            print(f"  doğrulama kümesi değişti ({len(val)} video); en iyi (epoch {state['best']['epoch']}) "
                  f"yeniden ölçüldü: {state['best']['val_mae']:.2f} BPM", flush=True)
    elif val:
        mae0 = validate(model, val, device)
        print(f"ön-eğitimli (PURE) doğrulama MAE: {mae0:.2f} BPM", flush=True)
        state["history"].append({"epoch": 0, "val_mae": mae0, "loss": None})
        state["best"] = {"epoch": 0, "val_mae": mae0}
        torch.save({"model": model.state_dict()}, os.path.join(a.out, "best.pth"))
    state["val_set"] = sorted(v["npz"] for v in val)

    sampler = ChunkSampler(train)
    epoch_time = None
    while state["epoch"] < a.epochs:
        if time.time() > deadline or (epoch_time and time.time() + epoch_time > deadline):
            print("süre sınırı: eğitim durduruldu", flush=True)
            break
        t0 = time.time()
        new = [v for v in list_videos(a.data) if not is_val(v["person"])]  # indirme sürerken yeni gelenler
        if len(new) > len(train):
            train = new
            sampler = ChunkSampler(train)
            print(f"  eğitim kümesi: {len(train)} video ({len({v['person'] for v in train})} kişi)", flush=True)
        model.train()
        losses = []
        pf = Prefetcher(sampler, a.bs, seed=100000 * state["epoch"] + 1234)
        for step in range(a.steps):
            x, y = pf.next()
            x = to_input(x, device)
            y = torch.as_tensor(y, device=device)
            pred = model(x)[0]
            loss = neg_pearson(pred, y)
            if not torch.isfinite(loss):
                continue
            opt.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
            opt.step()
            sched.step()
            losses.append(loss.item())
            if (step + 1) % 100 == 0:
                print(f"  epoch {state['epoch'] + 1} adım {step + 1}/{a.steps} kayıp {np.mean(losses[-100:]):.4f}",
                      flush=True)
        pf.close()
        state["epoch"] += 1
        mae = validate(model, val, device) if val else float("nan")
        state["history"].append({"epoch": state["epoch"], "val_mae": mae, "loss": float(np.mean(losses))})
        if state["best"] is None or mae < state["best"]["val_mae"]:
            state["best"] = {"epoch": state["epoch"], "val_mae": mae}
            torch.save({"model": model.state_dict()}, os.path.join(a.out, "best.pth"))
        torch.save({"model": model.state_dict(), "opt": opt.state_dict(), "sched": sched.state_dict(),
                    "state": state}, last + ".part")
        os.replace(last + ".part", last)
        epoch_time = time.time() - t0
        print(f"epoch {state['epoch']}: kayıp {np.mean(losses):.4f}, doğrulama MAE {mae:.2f} BPM, "
              f"en iyi {state['best']['val_mae']:.2f} (epoch {state['best']['epoch']}), {epoch_time:.0f} s", flush=True)
        json.dump(state, open(os.path.join(a.out, "gecmis.json"), "w"), indent=1)
    print("bitti", flush=True)


if __name__ == "__main__":
    main()
