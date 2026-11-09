#!/usr/bin/env python
"""Onaylı HF hesabıyla WeiQian98/PURE indir -> işle -> ham oturumu sil.

python scripts/dl_prepare_pure.py --out /tmp/dl --raw /tmp/dl_raw
--limit 1: ilk oturumda deneme. Tam koşu depodaki gerçek oturum listesini kullanır.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import re
import shutil
import tempfile

from dl_prepare import process_pure_folder

REPO = "WeiQian98/PURE"


def prepare(out, raw, limit=0, workers=8):
    from huggingface_hub import HfApi, hf_hub_download

    token = os.environ.get("HF_TOKEN")
    if not token:
        raise RuntimeError("HF_TOKEN yok: Kaggle Secrets erişimini etkinleştirin")
    api = HfApi(token=token)
    revision = api.repo_info(REPO, repo_type="dataset").sha
    sessions = sorted(x.path for x in api.list_repo_tree(REPO, repo_type="dataset", revision=revision)
                      if re.fullmatch(r"\d{2}-\d{2}", x.path))
    if limit:
        sessions = sessions[:limit]
    if not sessions:
        raise RuntimeError("PURE oturum listesi boş; eğitim başlatılmadı")
    target = Path(out) / "pure"
    target.mkdir(parents=True, exist_ok=True)
    Path(raw).mkdir(parents=True, exist_ok=True)
    print(f"PURE: {len(sessions)} oturum, kaynak {REPO}@{revision}", flush=True)
    for i, session in enumerate(sessions, 1):
        dst = target / (session + ".npz")
        # NPZ en son taşınır: düşük yüz kalitesinde NPY bilerek üretilmez.
        if dst.exists():
            print(f"[{i}/{len(sessions)}] {session}: hazır", flush=True)
            continue
        entries = list(api.list_repo_tree(REPO, path_in_repo=session, recursive=True,
                                          repo_type="dataset", revision=revision))
        files = [x.path for x in entries if x.path.endswith((".png", ".json"))]
        labels = [p for p in files if p.endswith(".json")]
        if len(labels) != 1 or not any(p.endswith(".png") for p in files):
            raise RuntimeError(f"{session}: PNG/PPG dosyaları eksik")
        with tempfile.TemporaryDirectory(prefix="pure_", dir=raw) as tmp:
            def download(path):
                return hf_hub_download(REPO, path, repo_type="dataset", revision=revision,
                                       token=token, local_dir=tmp)
            # Yetki ve etiket kontrolü: binlerce kareyi indirmeden önce.
            meta = json.loads(Path(download(labels[0])).read_text())
            if not meta.get("/FullPackage") or "waveform" not in meta["/FullPackage"][0]["Value"]:
                raise RuntimeError(f"{session}: PPG waveform etiketi yok")
            file_set = set(files)
            required = sum(x.size or 0 for x in entries if x.path in file_set)
            if shutil.disk_usage(raw).free < required + 2_000_000_000:
                raise RuntimeError("Ham oturum ve işlenmiş kareler için boş disk yetersiz")
            with ThreadPoolExecutor(max_workers=workers) as pool:
                list(pool.map(download, [p for p in files if p.endswith(".png")]))
            # Yalnızca tamamlanan oturumu eğitim klasörüne taşı.
            staged = Path(tmp) / "processed.npz"
            n, rate = process_pure_folder(Path(tmp) / session, str(staged),
                                          person="pure_" + session[:2], camera="PURE",
                                          step=session[3:], source="pure")
            if staged.with_suffix(".npy").exists():
                os.replace(staged.with_suffix(".npy"), dst.with_suffix(".npy"))
            os.replace(staged, dst)
        print(f"[{i}/{len(sessions)}] {session}: {n} kare, yüz %{rate * 100:.0f}; ham veri silindi", flush=True)
    (target / "manifest.json").write_text(json.dumps(
        {"repo": REPO, "revision": revision, "sessions": sessions}, indent=2))
    return sessions


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="/tmp/dl")
    parser.add_argument("--raw", default="/tmp/dl_raw")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()
    prepare(args.out, args.raw, args.limit, args.workers)
