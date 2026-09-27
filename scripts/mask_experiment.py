#!/usr/bin/env python
"""
Deney: Cilt maskesi türünün aydınlatma titremesine dayanıklılığa etkisi.

Gerçek bir yüz fotoğrafından (kendi selfie'niz olabilir) YARI-SENTETİK video
üretilir: fotoğrafa bilinen HR'de nabız rengi, nabız bandına düşen beyaz ışık
titremesi ve baş ötelemesi eklenir. Ardından üç maske modu karşılaştırılır:
    none   : maske yok (tüm ROI)
    binary : her karede ikili YCrCb maskesi (klasik)
    soft   : zamanda yumuşatılmış ağırlıklı maske (önerilen)

    python scripts/mask_experiment.py --image yuz.jpg
    python scripts/mask_experiment.py --image yuz.jpg --trials 10 --out results/maske_deneyi

Yüz, Haar ile otomatik bulunur (fotoğrafta tek, önden, net bir yüz olmalı).
"""
import argparse
import os
import sys

import cv2
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from rppg.pipeline import Config, estimate  # noqa: E402
from rppg.plotting import plot_heatmap  # noqa: E402
from rppg.roi import FaceTracker  # noqa: E402
from rppg.signals import extract_traces  # noqa: E402

FS = 30.0
PV_BGR = np.array([0.53, 0.77, 0.33], np.float32)


def make_frames(img, hr, illum, f_illum, motion, noise, n, seed):
    rng = np.random.default_rng(seed)
    t = np.arange(n) / FS
    pulse = np.sin(2 * np.pi * hr / 60 * t)
    H, W = img.shape[:2]
    for i in range(n):
        f = img * (1 + 0.003 * PV_BGR * pulse[i]) * (1 + illum * np.sin(2 * np.pi * f_illum * t[i]))
        if motion:
            M = np.float32([[1, 0, motion * np.sin(2 * np.pi * 0.2 * t[i])],
                            [0, 1, 0.5 * motion * np.sin(2 * np.pi * 0.13 * t[i])]])
            f = cv2.warpAffine(f, M, (W, H), borderMode=cv2.BORDER_REFLECT)
        f = f + rng.normal(0, noise, f.shape)
        yield np.clip(f, 0, 255).astype(np.uint8)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", help="yüz fotoğrafı (tek, önden, net)")
    ap.add_argument("--from-csv", help="deneyi yeniden koşmadan var olan CSV'den tablo üret")
    ap.add_argument("--trials", type=int, default=6)
    ap.add_argument("--seconds", type=float, default=20)
    ap.add_argument("--out", default="results/maske_deneyi")
    a = ap.parse_args()
    if a.from_csv:
        report(pd.read_csv(a.from_csv), a.out, "?", "?")
        return
    if not a.image:
        ap.error("--image gerekli")
    img = cv2.imread(a.image)
    if img is None:
        sys.exit(f"Görüntü okunamadı: {a.image}")
    s = 360 / max(img.shape[:2])
    img = cv2.resize(img, (int(img.shape[1] * s), int(img.shape[0] * s))).astype(np.float32)
    os.makedirs(a.out, exist_ok=True)
    rng = np.random.default_rng(0)
    rows = []
    n = int(a.seconds * FS)
    conditions = [("titreme", 0.01, 0), ("titreme+hareket", 0.01, 6), ("güçlü titreme+hareket", 0.02, 6)]
    for trial in range(a.trials):
        hr = float(rng.uniform(60, 100))
        f_il = float(rng.uniform(0.9, 2.5))
        while abs(f_il * 60 - hr) < 12:          # titreme nabızdan ayırt edilebilir olsun
            f_il = float(rng.uniform(0.9, 2.5))
        for cname, il, mo in conditions:
            for mode in ["none", "binary", "soft"]:
                tr = extract_traces(make_frames(img, hr, il, f_il, mo, 2.0, n, trial), FS, FaceTracker(),
                                    respiration=False, mask_mode=mode, use_skin_mask=(mode != "none"))
                for cfg in [Config("pos", ("full",), "mean", "argmax", False), Config("pos")]:
                    r = estimate(tr, cfg)
                    rows.append({"deneme": trial, "koşul": cname, "maske": mode,
                                 "hat": "klasik (tüm yüz)" if cfg.fusion == "mean" else "önerilen (füzyon+Viterbi)",
                                 "hata": abs(r.hr_mean - hr), "titremeye_kilitlendi": abs(r.hr_mean - f_il * 60) < 3})
        print(f"deneme {trial + 1}/{a.trials} bitti")
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(a.out, "maske_deneyi.csv"), index=False)
    report(df, a.out, a.trials, a.seconds)


MODE_TR = {"none": "maskesiz", "binary": "ikili (klasik)", "soft": "yumuşak (önerilen)"}
COND_ORDER = ["titreme", "titreme+hareket", "güçlü titreme+hareket"]


def report(df, out, trials, seconds):
    df = df.copy()
    df["maske"] = df["maske"].map(lambda m: MODE_TR.get(m, m))
    if trials == "?":
        trials, seconds = df["deneme"].nunique(), 20
    order = [MODE_TR[m] for m in ["none", "binary", "soft"]]

    def piv(col, scale=1.0):
        t = df.pivot_table(index=["hat", "maske"], columns="koşul", values=col, aggfunc="mean")[COND_ORDER] * scale
        t = t.reindex(pd.MultiIndex.from_product([sorted(df["hat"].unique()), order]))
        t.index = [f"{h} / {m}" for h, m in t.index]
        return t

    t1, t2 = piv("hata"), piv("titremeye_kilitlendi", 100)
    md = ["# Maske Deneyi (yarı-sentetik, gerçek yüz fotoğrafı)", "",
          f"Deneme sayısı: {trials}, süre: {seconds} s, HR ~ U(60,100) BPM, titreme frekansı ~ U(0.9, 2.5) Hz, "
          "titreme genliği %1 (güçlü: %2), baş ötelemesi 6 px", "",
          "## Ortalama mutlak hata (BPM)", "", t1.round(2).to_markdown(), "",
          "## Titreme frekansına kilitlenme oranı (%)", "", t2.round(0).to_markdown(), ""]
    open(os.path.join(out, "SONUCLAR.md"), "w", encoding="utf-8").write("\n".join(md))
    pv = t1.loc[[i for i in t1.index if i.startswith("klasik")]]
    pv.index = [i.split(" / ")[1] for i in pv.index]
    plot_heatmap(pv, os.path.join(out, "maske_hata.png"), "Maske türü x koşul — ortalama hata (POS, tüm yüz)")
    print("\n".join(md))


if __name__ == "__main__":
    main()
