#!/usr/bin/env python
"""
Tarayıcı testinin (mobile/test/e2e.mjs --log) pencere bazında hatası.

e2e.mjs y4m dosyasını Chrome'a sahte kamera olarak verir; Chrome videoyu başa sararak tekrar oynatır. Uygulamanın
her nabız değeri (log.t = ilk kareden beri geçen süre, son 10 s'ye ait) videonun aynı 10 s'sindeki parmak PPG
nabzıyla karşılaştırılır. Başa sarma noktasını içeren pencereler sayılmaz. Bu ölçüm, son 15 pencerenin medyanını
videonun ortalama nabzıyla kıyaslamaktan daha doğrudur: MCD egzersiz videolarında nabız ilk dakikada ~15 BPM düşer.

    python scripts/e2e_hata.py --log gunluk.json --npz data/dl/test/mcd_1107_FullHDwebcam_after.npz --frames 1350
"""
import argparse
import json

import numpy as np

from dl_common import reference_hr

WIN = 10.0


def window_errors(log, bvp, n_frames, fs=30.0):
    """Başa sarmayı içermeyen pencerelerin (uygulama nabzı, referans nabız) çiftleri."""
    period = n_frames / fs
    pairs = []
    for r in log:
        t1 = r["t"]
        t0 = t1 - WIN
        if t0 < 0 or np.floor(t0 / period) != np.floor(t1 / period):
            continue
        center = (t0 % period) + WIN / 2
        ref = float(reference_hr(bvp[:n_frames], np.array([center]), fs, WIN)[0])
        pairs.append((r["hr"], ref))
    return np.array(pairs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", nargs="+", required=True)
    ap.add_argument("--npz", required=True, help="aynı videonun test kümesindeki etiketi")
    ap.add_argument("--frames", type=int, required=True, help="y4m'deki kare sayısı (başa sarma periyodu)")
    ap.add_argument("--skip", type=float, default=20.0, help="ilk kaç saniyenin değerleri sayılmasın (oturma süresi)")
    a = ap.parse_args()
    bvp = np.load(a.npz)["bvp"]
    for path in a.log:
        log = [r for r in json.load(open(path, encoding="utf-8")) if r["t"] >= a.skip]
        p = window_errors(log, bvp, a.frames)
        if len(p) == 0:
            print(f"{path}: pencere yok")
            continue
        e = np.abs(p[:, 0] - p[:, 1])
        print(f"{path}: {len(p)} pencere, MAE {e.mean():.2f} BPM, ≤5 BPM %{100 * np.mean(e <= 5):.0f}")


if __name__ == "__main__":
    main()
