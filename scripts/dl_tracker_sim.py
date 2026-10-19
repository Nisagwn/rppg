#!/usr/bin/env python
"""
Uygulamadaki çevrimiçi takipçinin (rppg.hr.OnlineHRTracker, mobile/dsp.js ile aynı) model dalgası üzerinde
çevrimdışı benzetimi: sıçrama payı (jump) seçimi ve "tek seferlik ölçüm" (bütün klip, Viterbi) ile karşılaştırma.

Dalgalar scripts/dl_ensemble.py'nin önbelleğinden okunur (yeniden çıkarım yok). Her saniye son 10 s'nin
spektrumu takipçiye verilir (uygulamadaki gibi; hareket güveni 1). Hata ölçümü:
  - çevrimiçi: ilk 10 penceresi (ısınma) hariç, her pencere
  - tek seferlik: uygulamanın ölçüm süresine denk 20 / 30 s'lik klipler, klip sonunda Viterbi ile tek değer
    (klibin ortalama nabzı) ve referansın aynı klipteki ortalaması

    python scripts/dl_tracker_sim.py --test data/dl/test --cache <dalgalar_test> --model "5._tur"
"""
import argparse
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))
from rppg.filtering import preprocess_bvp  # noqa: E402
from rppg.hr import BPM_GRID, OnlineHRTracker, spectrogram, viterbi_track  # noqa: E402
from dl_common import reference_hr  # noqa: E402
from dl_evaluate import group_of, test_videos  # noqa: E402

FS, WIN, STEP, WARM = 30.0, 10.0, 1.0, 10


def online(S, jump):
    trk = OnlineHRTracker(BPM_GRID, 4.0, jump)
    return np.array([trk.update(S[t], STEP, 1.0) for t in range(len(S))])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", required=True)
    ap.add_argument("--cache", required=True)
    ap.add_argument("--model", default="5._tur", help="önbellekteki model adı (boşluklar _)")
    ap.add_argument("--var", default="düz")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    jumps = (0.0, 0.005, 0.01, 0.02, 0.05)
    rows = []
    for p in test_videos(a.test):
        v = os.path.basename(p)[:-4]
        f = os.path.join(a.cache, f"{a.model}__{a.var}__{v}.npy")
        if not os.path.exists(f):
            continue
        meta = np.load(p)
        x = preprocess_bvp(np.load(f), FS)
        c, S = spectrogram(x, FS, WIN, STEP)
        ref = reference_hr(meta["bvp"], c)
        base = {"grup": group_of(meta), "video": v.split("_", 1)[1]}
        for j in jumps:
            e = np.abs(online(S, j) - ref)[WARM:]
            rows.append({**base, "yöntem": f"çevrimiçi jump={j:g}", "MAE": float(e.mean()),
                         "p5": float(100 * np.mean(e <= 5))})
        e = np.abs(viterbi_track(S, BPM_GRID, STEP) - ref)
        rows.append({**base, "yöntem": "Viterbi (bütün video)", "MAE": float(e.mean()), "p5": float(100 * np.mean(e <= 5))})
        for L in (20, 30):   # tek seferlik ölçüm: art arda L saniyelik klipler, her biri tek sayı
            n = int(L / STEP) - int(WIN / STEP) + 1           # klipteki pencere sayısı
            errs = {"tek seferlik": []}
            for s0 in range(0, len(S) - n + 1, n):
                sl = slice(s0, s0 + n)
                hv = viterbi_track(S[sl], BPM_GRID, STEP)
                r = float(np.mean(ref[sl]))
                errs["tek seferlik"].append(abs(float(np.median(hv)) - r))
            for k, e in errs.items():
                if e:
                    e = np.array(e)
                    rows.append({**base, "yöntem": f"{k} {L} s", "MAE": float(e.mean()),
                                 "p5": float(100 * np.mean(e <= 5))})
    df = pd.DataFrame(rows)
    os.makedirs(a.out, exist_ok=True)
    df.to_csv(os.path.join(a.out, "takipci.csv"), index=False)
    t = df.groupby("yöntem").agg(MAE=("MAE", "mean"), medyan=("MAE", "median"), p5=("p5", "mean"),
                                 en_kotu=("MAE", "max"), n=("video", "count")).round(2).sort_values("MAE")
    print(t.to_string())
    t.to_csv(os.path.join(a.out, "takipci_ozet.csv"))


if __name__ == "__main__":
    main()
