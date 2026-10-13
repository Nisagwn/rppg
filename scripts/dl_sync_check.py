#!/usr/bin/env python
"""
Etiket-video senkronu ve işaretini eğitilmiş modelle denetler (POS'un zayıf kaldığı telefon/düşük çözünürlük için).

dl_quality'deki POS tabanlı ölçüm MMPD (80x60) ve VIPL source2'de güvenilmez: POS orada nabzı bulamıyor.
Eğitilmiş model (5. tur, telefon/USB testinde 1.6 BPM) çok daha güçlü bir referans. Her video için:
  * r[k] = corr(model tahmini k kare kaydırılmış, etiket), k = -30..30 (r[k] > 0 ve tepe k ~ referans: senkron ve
    işaret doğru; tepe negatifse etiket ters; tepe referanstan uzaksa etiket kayık)
  * nabız uyumu: modelin ve etiketin pencere nabızları (işaret ve kaymadan bağımsız) -> etiket bu videoya mı ait
Referans tepe, senkronu bilinen ana test videolarında (UBFC + MCD önden webcam, MCD etiketi ters çevrilerek) ölçülür.

    python scripts/dl_sync_check.py                       # HF'teki rppg-veri deposundan kamera başına 60 video
    python scripts/dl_sync_check.py --write --data /tmp/dl --subs vipl dlcn   # eğitim öncesi: her videoya <ad>.snk

--write: dl_train.py MODEL_SYNC kaynaklarında etiketi .snk'deki kaymayla hizalar ve hizalı korelasyonu zayıf
videoları çıkarır (dl_common.video_decision). Test klasörlerine yazılmaz: test etiketleri olduğu gibi kalır.
"""
import argparse
import csv
import glob
import os
import re
import time

import numpy as np

from dl_common import ROOT, build_model, hr_from_bvp, predict_video, reference_hr
from rppg.filtering import preprocess_bvp

LAGS = np.arange(-45, 46)  # VIPL'de -30 sınırına dayanan videolar vardı (±1.5 s)
TRIM = 50  # np.roll'un sardığı uçlar korelasyona girmesin (> en büyük kayma)
MAX_FRAMES = 1800  # ilk 60 s


def group_of(path):
    name = os.path.basename(path)
    if name.startswith("vipl_"):
        return "vipl/" + re.search(r"(source\d)", name).group(1)
    return name.split("_")[0]


def lag_curve(pred, label, fs=30.0):
    p, b = preprocess_bvp(pred, fs), preprocess_bvp(label, fs)
    return np.array([np.corrcoef(np.roll(p, k)[TRIM:-TRIM], b[TRIM:-TRIM])[0, 1] for k in LAGS])


def analyze(model, device, npz, mult=1.0):
    frames = np.asarray(np.load(npz[:-4] + ".npy", mmap_mode="r")[:MAX_FRAMES])
    bvp = mult * np.load(npz)["bvp"][:len(frames)].astype(float)
    pred = predict_video(model, frames, device)
    if pred is None or len(frames) < 300 or np.std(bvp) < 1e-8:
        return None
    r = lag_curve(pred, bvp)
    c, hr_a, _ = hr_from_bvp(pred)
    err = np.abs(hr_a - reference_hr(bvp, c))
    i = int(np.argmax(np.abs(r)))
    return {"video": os.path.basename(npz)[:-4], "group": group_of(npz), "lag_peak": int(LAGS[i]),
            "r_peak": float(r[i]), "lag_pos": int(LAGS[np.argmax(r)]), "r_pos": float(r.max()),
            "hr_mae": float(err.mean()), "hr_ok": float((err <= 5).mean()), "curve": r}


def sample_from_hub(repo, cache, per_group, subs=("mmpd", "vipl")):
    """Kamera başına eşit aralıklı per_group video seçip (npz + npy) indirir; yerel npz yollarını döndürür."""
    from huggingface_hub import HfApi, snapshot_download
    files = HfApi().list_repo_files(repo, repo_type="dataset")
    have_npy = {f[:-4] for f in files if f.endswith(".npy")}
    groups = {}
    for f in sorted(files):
        if f.endswith(".npz") and f.split("/")[0] in subs and f[:-4] in have_npy:
            groups.setdefault(group_of(f), []).append(f)
    pick = []
    for g, fs in sorted(groups.items()):
        idx = np.linspace(0, len(fs) - 1, min(per_group, len(fs))).astype(int)
        pick += [fs[i] for i in idx]
        print(f"  {g}: {len(fs)} videodan {len(idx)}", flush=True)
    snapshot_download(repo, repo_type="dataset", local_dir=cache, max_workers=8,
                      allow_patterns=[p for f in pick for p in (f, f[:-4] + ".npy")])
    return [os.path.join(cache, f) for f in pick]


def summarize(rows, title):
    print(f"\n{title}")
    print(f"{'grup':14s} {'video':>5s} {'nabız uyumu %':>13s} {'ort. eğri tepesi':>16s} {'r':>6s} "
          f"{'tepe ters %':>11s} {'video tepe kayma (10/50/90 %)':>30s}")
    out = {}
    for g in sorted({r["group"] for r in rows}):
        rr = [r for r in rows if r["group"] == g]
        mean = np.mean([r["curve"] for r in rr], axis=0)
        k = int(np.argmax(np.abs(mean)))
        ok = [r for r in rr if abs(r["r_peak"]) >= 0.3]  # kayma yalnızca belirgin tepeli videolarda anlamlı
        q = np.percentile([r["lag_peak"] for r in ok], [10, 50, 90]) if ok else [np.nan] * 3
        neg = 100 * np.mean([r["r_peak"] < 0 for r in ok]) if ok else np.nan
        print(f"{g:14s} {len(rr):5d} {100 * np.median([r['hr_ok'] for r in rr]):13.0f} {LAGS[k]:+16d} "
              f"{mean[k]:+6.2f} {neg:11.0f} {'%+.0f / %+.0f / %+.0f' % tuple(q):>30s}  ({len(ok)} belirgin)")
        out[g] = int(LAGS[k])
    return out


def write_all(model, device, data, subs):
    """Her videoya <ad>.snk yazar (varsa ve güncelse atlar). Hizalanan/çıkarılan sayısını basar."""
    from dl_common import SYNC_R_MIN
    files = [p for s in subs for p in sorted(glob.glob(os.path.join(data, s, "*.npz")))
             if os.path.exists(p[:-4] + ".npy")]
    kept, t0 = {}, time.time()
    for i, npz in enumerate(files, 1):
        out = npz[:-4] + ".snk"
        if not (os.path.exists(out) and os.path.getmtime(out) >= os.path.getmtime(npz)):
            r = analyze(model, device, npz)
            if r is None:
                continue
            with open(out + ".part", "wb") as f:
                np.savez(f, **{k: r[k] for k in ("lag_pos", "r_pos", "lag_peak", "r_peak", "hr_ok")})
            os.replace(out + ".part", out)
        s = dict(np.load(out))
        g = group_of(npz)
        n, k = kept.get(g, (0, 0))
        kept[g] = (n + 1, k + int(s["r_pos"] >= SYNC_R_MIN))
        if i % 200 == 0:
            print(f"  {i}/{len(files)} ({time.time() - t0:.0f} s)", flush=True)
    for g, (n, k) in sorted(kept.items()):
        print(f"  {g}: {n} video, hizalı korelasyon >= {SYNC_R_MIN}: {k} (%{100 * k / max(n, 1):.0f})", flush=True)


def main():
    import torch
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=os.path.join(ROOT, "results/derin_ogrenme/kaggle_tur5/last.pth"))
    ap.add_argument("--repo", default="", help="varsayılan: <hesap>/rppg-veri")
    ap.add_argument("--cache", default=os.path.join(ROOT, "data/dl/_senkron"))
    ap.add_argument("--per-group", type=int, default=60)
    ap.add_argument("--test", default=os.path.join(ROOT, "data/dl/test"))
    ap.add_argument("--out", default=os.path.join(ROOT, "results/derin_ogrenme/senkron_model.csv"))
    ap.add_argument("--write", action="store_true", help="--data/--subs altındaki her videoya .snk yaz")
    ap.add_argument("--data", default=os.path.join(ROOT, "data/dl"))
    ap.add_argument("--subs", nargs="*", default=["vipl", "dlcn", "cohface"])
    a = ap.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = build_model(device, a.model)
    if a.write:
        assert not any(s.startswith("test") for s in a.subs), "test etiketleri hizalanmaz"
        write_all(model, device, a.data, a.subs)
        return
    rows = []
    for npz in sorted(glob.glob(os.path.join(a.test, "*.npz"))):  # referans: senkronu bilinen videolar
        src = str(np.load(npz)["source"])
        r = analyze(model, device, npz, mult=-1.0 if src == "mcd" else 1.0)  # MCD etiketi ters (eğitimdeki gibi)
        if r:
            r["group"] = f"ref/{src}"
            rows.append(r)
    ref = summarize(rows, "Referans (ana test videoları, senkron ve işaret doğru)")

    if not a.repo:
        from huggingface_hub import HfApi
        a.repo = f"{HfApi().whoami()['name']}/rppg-veri"
    print(f"\n{a.repo} deposundan örnek indiriliyor -> {a.cache}", flush=True)
    for i, npz in enumerate(sample_from_hub(a.repo, a.cache, a.per_group), 1):
        r = analyze(model, device, npz)
        if r:
            rows.append(r)
        if i % 40 == 0:
            print(f"  {i} video", flush=True)
    summarize([r for r in rows if not r["group"].startswith("ref/")], "Yeni veri setleri (etiket olduğu gibi)")
    print(f"\nreferans tepe: {ref}  (bunlardan farklı tepe = etiket kayık; negatif r = etiket ters)")

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    keys = ["video", "group", "lag_peak", "r_peak", "lag_pos", "r_pos", "hr_mae", "hr_ok"]
    with open(a.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys + [f"r{k:+d}" for k in LAGS])
        w.writeheader()
        for r in rows:
            w.writerow({**{k: r[k] for k in keys}, **{f"r{k:+d}": round(float(v), 4) for k, v in zip(LAGS, r["curve"])}})
    print(f"-> {a.out}")


if __name__ == "__main__":
    main()
