#!/usr/bin/env python
"""
Solunum hızı denemesi: model nabız dalgasından ve yüz kırpıntısından solunum tahmini, MCD-rPPG'nin klinik solunum
sayımıyla (db.csv "respiratory", dakikada nefes; kayıt başına tek değer) karşılaştırma.

Yöntemler (Karlen vd. 2013; Charlton vd. 2016): solunum nabız dalgasını üç yoldan modüle eder
  RIIV  taban çizgisi (yoğunluk): ham dalganın 0.1–0.5 Hz bileşeni
  RIAV  genlik: atım tepelerinin yükseklik dizisi
  RIFV  frekans: atımlar arası süre dizisi (solunumsal sinüs aritmisi)
  yeşil yüz kırpıntısının ortasındaki yeşil kanal ortalamasının 0.1–0.5 Hz bileşeni (göğüs/baş hareketi + kan hacmi)
  füzyon RIAV/RIFV/RIIV medyanı
Her dizinin 4 Hz'e enterpolasyonu, 6–30 nefes/dk aralığında spektral tepe (bütün kayıt). Taban çizgisi: herkese sabit
değer (testteki ölçümlerin medyanı; yöntemlerin buna göre avantajı olmalı).

    python scripts/resp_experiment.py --cache <dalgalar_test> --test data/dl/test --out results/solunum
"""
import argparse
import glob
import os

import numpy as np
import pandas as pd
from scipy.signal import butter, filtfilt, find_peaks, welch

FS, FR, LO, HI = 30.0, 4.0, 0.1, 0.5


def peak_rate(x, fs):
    x = np.asarray(x, float) - np.mean(x)
    f, p = welch(x, fs, nperseg=min(len(x), int(fs * 64)), nfft=int(fs * 512))
    m = (f >= LO) & (f <= HI)
    return 60 * f[m][np.argmax(p[m])]


def band(x, fs, lo=LO, hi=HI):
    b, a = butter(2, [lo / (fs / 2), hi / (fs / 2)], "band")
    return filtfilt(b, a, np.asarray(x, float) - np.mean(x))


def rates(bvp, green):
    t = np.arange(len(bvp)) / FS
    x = band(bvp, FS, 0.7, 3.0)
    pk, _ = find_peaks(x, distance=int(FS / 3.5))
    grid = np.arange(t[pk[1]], t[pk[-1]], 1 / FR)
    riav = np.interp(grid, t[pk], x[pk])
    rifv = np.interp(grid, t[pk[1:]], np.diff(t[pk]))
    out = {"RIIV": peak_rate(band(bvp, FS)[::int(FS / FR)], FR), "RIAV": peak_rate(riav, FR), "RIFV": peak_rate(rifv, FR)}
    out["füzyon"] = float(np.median([out["RIIV"], out["RIAV"], out["RIFV"]]))
    if green is not None:
        out["yeşil (kırpıntı)"] = peak_rate(band(green, FS)[::int(FS / FR)], FR)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", nargs="+", required=True, help="dl_ensemble.py dalga önbelleği klasör(ler)i")
    ap.add_argument("--test", nargs="+", required=True, help="kırpıntıların test klasör(ler)i")
    ap.add_argument("--model", default="5._tur")
    ap.add_argument("--db", default="data/MCD/db.csv")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    db = pd.read_csv(a.db)
    db["ad"] = db.video.str.replace("video/", "").str.replace(".avi", "")
    resp = dict(zip(db.ad, db.respiratory))
    npy = {os.path.basename(p)[4:-4]: p for d in a.test for p in glob.glob(os.path.join(d, "mcd_*.npy"))}
    rows = []
    for d in a.cache:
        for f in sorted(glob.glob(os.path.join(d, f"{a.model}__düz__mcd_*.npy"))):
            ad = os.path.basename(f).split("__")[-1][4:-4]
            if ad not in resp or not np.isfinite(resp[ad]):
                continue
            green = None
            if ad in npy:
                fr = np.load(npy[ad], mmap_mode="r")
                green = np.concatenate([np.asarray(fr[i:i + 600, 20:52, 20:52, 1], np.float32).mean((1, 2))
                                        for i in range(0, len(fr), 600)])
            r = rates(np.load(f), green)
            cam = ad.split("_")[1]
            rows.append({"video": ad, "kamera": cam, "durum": ad.split("_")[2], "gercek": resp[ad], **r})
    df = pd.DataFrame(rows).drop_duplicates("video")
    const = df.gercek.median()
    df["sabit (medyan)"] = const
    meth = ["RIIV", "RIAV", "RIFV", "füzyon", "yeşil (kırpıntı)", "sabit (medyan)"]
    meth = [m for m in meth if m in df]
    tab = pd.DataFrame({m: {"MAE": (df[m] - df.gercek).abs().mean(), "±3 nefes %": 100 * ((df[m] - df.gercek).abs() <= 3).mean(),
                            "korelasyon": df[m].corr(df.gercek) if df[m].std() > 0 else np.nan} for m in meth}).T.round(2)
    os.makedirs(a.out, exist_ok=True)
    df.round(2).to_csv(os.path.join(a.out, "solunum.csv"), index=False)
    tab.to_csv(os.path.join(a.out, "solunum_ozet.csv"))
    print(f"{len(df)} video, gerçek solunum {df.gercek.min():g}–{df.gercek.max():g} (medyan {const:g})")
    print(tab.to_string())


if __name__ == "__main__":
    main()
