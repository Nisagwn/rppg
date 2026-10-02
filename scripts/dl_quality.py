#!/usr/bin/env python
"""
Eğitim verisinin etiket kalitesi: her video için dl_common.label_quality ölçütlerini hesaplar, <ad>.kal
(kare başına iyi/kötü maskesi + ölçütler) yazar ve veri seti bazında özet tablo basar.

dl_train.py .kal dosyası olan videolarda kötü videoları atar ve kötü bölümlerden parça seçmez;
dosya yoksa kalite eğitim sırasında hesaplanır (Kaggle'da hazırlama sürerken gelen videolar için).

    python scripts/dl_quality.py --data data/dl --workers 4
"""
import argparse
import csv
import glob
import os
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np

from dl_common import label_quality, video_decision

SOURCES = ("mcd", "ubfc", "pure", "ubfcphys", "mpu", "test")
FIELDS = ("ok_frac", "snr_med", "agree_frac", "agree_ok_frac", "r0", "lag_best", "r_best", "lag_pos", "r_pos")


def kal_path(npz):
    return npz[:-4] + ".kal"  # .npz değil: "*.npz" ile video arayan betiklere karışmasın


def compute(npz, force=False):
    """Bir video için kalite; varsa ve günceldeyse diskteki sonucu okur."""
    out = kal_path(npz)
    if not force and os.path.exists(out) and os.path.getmtime(out) >= os.path.getmtime(npz):
        q = dict(np.load(out))
        if all(k in q for k in FIELDS):
            return {k: q[k].item() for k in FIELDS}
    npy = npz[:-4] + ".npy"
    if not os.path.exists(npy):
        return None
    m = np.load(npz)
    q = label_quality(np.load(npy, mmap_mode="r"), m["bvp"], float(m["fs"]))
    with open(out + ".part", "wb") as f:
        np.savez(f, **q)
    os.replace(out + ".part", out)
    return {k: q[k] for k in FIELDS}


def _job(npz):
    try:
        return npz, compute(npz), None
    except Exception as e:  # noqa: BLE001
        return npz, None, repr(e)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/dl")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--sources", nargs="*", default=list(SOURCES))
    a = ap.parse_args()

    files = sorted(p for s in a.sources for p in glob.glob(os.path.join(a.data, s, "*.npz")))
    print(f"{len(files)} video", flush=True)
    rows, t0 = [], time.time()
    with ProcessPoolExecutor(a.workers) as ex:
        for i, (npz, q, err) in enumerate(ex.map(_job, files, chunksize=4), 1):
            if err:
                print(f"  HATA {npz}: {err}", flush=True)
            elif q is not None:
                src = os.path.basename(os.path.dirname(npz))
                rows.append({"source": src, "video": os.path.basename(npz)[:-4], **q,
                             "keep": int(video_decision(q, src))})
            if i % 200 == 0:
                print(f"  {i}/{len(files)}  ({time.time() - t0:.0f} s)", flush=True)

    with open(os.path.join(a.data, "kalite.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["source", "video", *FIELDS, "keep"])
        w.writeheader()
        w.writerows(rows)

    print(f"\n{'veri':9s} {'video':>6s} {'tutulan':>8s} {'iyi kare %':>10s} {'SNR dB':>7s} "
          f"{'POS uyumu %':>11s} {'r(0)':>6s} {'|gecikme|>4':>11s}")
    for src in sorted({r["source"] for r in rows}):
        rr = [r for r in rows if r["source"] == src]
        col = lambda k: np.array([r[k] for r in rr], dtype=float)  # noqa: E731
        print(f"{src:9s} {len(rr):6d} {int(col('keep').sum()):8d} {100 * col('ok_frac').mean():10.1f} "
              f"{np.median(col('snr_med')):7.1f} {100 * np.median(col('agree_ok_frac')):11.1f} "
              f"{np.median(col('r0')):+6.2f} {int((np.abs(col('lag_best')) > 4).sum()):11d}")
    print(f"\nsüre {time.time() - t0:.0f} s -> {os.path.join(a.data, 'kalite.csv')}")


if __name__ == "__main__":
    main()
