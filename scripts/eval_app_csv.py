#!/usr/bin/env python
"""
Telefonda yapılan ölçümlerin referans cihazla (oksimetre / akıllı saat) karşılaştırması.

Uygulamanın "Oturumu CSV indir" dosyasındaki ikinci tablo kullanılır: her "Kaydet" bir satır
(zaman, tur, kamera, uygulama_bpm, cihaz_bpm, fark, guvenilir, snr_db).

    python scripts/eval_app_csv.py indirilenler/rppg_oturum_*.csv
    python scripts/eval_app_csv.py *.csv --hepsi        # güvenilmez işaretli ölçümler de dahil

Çıktı: tur × kamera başına ölçüm sayısı, MAE, ±5 BPM içindeki oran, ortalama yüzde hata (tüketici nabız ölçerleri için
kullanılan ölçüt: %10'un altı) ve Bland–Altman (ortalama fark ± 1.96 SS). Güvenilmez işaretli (uygulamanın "tekrar
ölçün" dediği) ölçümlerin oranı ayrıca verilir: kullanıcıya gösterilmeyen sonuçlar hatadan düşülürse bu oranla birlikte
raporlanmalı.
"""
import argparse
import io
import sys

import numpy as np
import pandas as pd


def read_refs(path):
    text = open(path, encoding="utf-8").read()
    if "zaman,tur,kamera,uygulama_bpm" not in text:
        return pd.DataFrame()
    part = text[text.index("zaman,tur,kamera,uygulama_bpm"):]
    df = pd.read_csv(io.StringIO(part))
    df["dosya"] = path
    return df


def summary(g):
    e = g.uygulama_bpm - g.cihaz_bpm
    a = e.abs()
    return pd.Series({"n": len(g), "MAE": a.mean(), "±5 BPM %": 100 * (a <= 5).mean(),
                      "yüzde hata %": 100 * (a / g.cihaz_bpm).mean(), "BA ort. fark": e.mean(),
                      "BA ±1.96 SS": 1.96 * e.std(ddof=1) if len(g) > 1 else np.nan})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", nargs="+")
    ap.add_argument("--hepsi", action="store_true", help="güvenilmez işaretli ölçümleri de say")
    a = ap.parse_args()
    df = pd.concat([read_refs(p) for p in a.csv], ignore_index=True)
    if df.empty:
        sys.exit("Dosyalarda cihazla karşılaştırma tablosu yok (uygulamada ölçümden sonra cihaz değeri kaydedilmemiş).")
    print(f"{len(df)} ölçüm, {df.dosya.nunique()} dosya; güvenilmez işaretli: {int((df.guvenilir == 0).sum())} "
          f"(%{100 * (df.guvenilir == 0).mean():.0f})")
    use = df if a.hepsi else df[df.guvenilir == 1]
    if use.empty:
        sys.exit("Güvenilir işaretli ölçüm yok; --hepsi ile deneyin.")
    t = use.groupby(["tur", "kamera"]).apply(summary, include_groups=False)
    t.loc[("hepsi", ""), :] = summary(use)
    print(t.round(2).to_string())


if __name__ == "__main__":
    main()
