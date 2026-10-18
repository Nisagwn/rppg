#!/usr/bin/env python
"""
Mobil yüz dedektörü karşılaştırması: kamera başına kapsama (pencere / 25), sonuç verilen pencerelerde MAE,
sonuçsuz kesit sayısı; iki koşuda da pencere veren kesitlerde eşleştirilmiş Wilcoxon (MAE).
Teşhis sütunları (yuz_kare%, sn_*) varsa ölçümün nerede durduğu da özetlenir.

    python scripts/compare_mobile_face.py results/mobil_dogrulama_v12 results/mobil_dogrulama_yuz_pico results/mobil_dogrulama_yuz
"""
import os
import sys

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

WIN = 25   # 40 s kesitte en çok pencere sayısı (t = 10 .. 34+); kapsama = pencere / 25

runs = sys.argv[1:]
dfs = {os.path.basename(r.rstrip("/\\")): pd.read_csv(os.path.join(r, "kesitler.csv")) for r in runs}
cams = ["webcam (önden)", "telefon", "USB (yan)"]

print("## Kamera başına\n")
print("| koşu | kamera | kesit | kapsama % | sonuçsuz kesit | MAE (pencere veren kesitler) | ≤5 BPM % |")
print("|:--|:--|--:|--:|--:|--:|--:|")
for name, d in dfs.items():
    for cam in cams + ["tümü"]:
        g = d if cam == "tümü" else d[d.kamera == cam]
        print(f"| {name} | {cam} | {len(g)} | {100 * g.pencere.mean() / WIN:.0f} | {(g.pencere == 0).sum()} | "
              f"{g.uygulama_MAE.mean():.2f} | {g['uygulama_≤5BPM%'].mean():.0f} |")

if any("sn_yuz_yok" in d for d in dfs.values()):
    print("\n## Teşhis: ölçümsüz saniyelerin nedeni (t ≥ 10 s, kamera başına toplam)\n")
    print("| koşu | kamera | yüz kutusu olan kare % | yüz yok (s) | ısınma (s) | model ısınma (s) | ölçüm (s) |")
    print("|:--|:--|--:|--:|--:|--:|--:|")
    for name, d in dfs.items():
        if "sn_yuz_yok" not in d:
            continue
        for cam in cams:
            g = d[d.kamera == cam]
            print(f"| {name} | {cam} | {g['yuz_kare%'].mean():.0f} | {g.sn_yuz_yok.sum()} | {g.sn_isinma.sum()} | "
                  f"{g.sn_model_isinma.sum()} | {g.sn_olcum.sum()} |")

names = list(dfs)
print("\n## Eşleştirilmiş karşılaştırma (iki koşuda da pencere veren kesitler, kesit MAE'si)\n")
print("| A | B | kamera | n | MAE A | MAE B | Wilcoxon p | pencere A | pencere B | Wilcoxon p (pencere, tüm kesitler) |")
print("|:--|:--|:--|--:|--:|--:|--:|--:|--:|--:|")
for i in range(len(names)):
    for j in range(i + 1, len(names)):
        a, b = dfs[names[i]].set_index("ad"), dfs[names[j]].set_index("ad")
        common = a.index.intersection(b.index)
        for cam in cams + ["tümü"]:
            idx = [k for k in common if cam == "tümü" or a.loc[k, "kamera"] == cam]
            both = [k for k in idx if a.loc[k, "pencere"] > 0 and b.loc[k, "pencere"] > 0]
            ma, mb = a.loc[both, "uygulama_MAE"].values, b.loc[both, "uygulama_MAE"].values
            p = wilcoxon(ma, mb).pvalue if len(both) >= 5 and np.any(ma != mb) else float("nan")
            pa, pb = a.loc[idx, "pencere"].values, b.loc[idx, "pencere"].values
            pp = wilcoxon(pa, pb).pvalue if len(idx) >= 5 and np.any(pa != pb) else float("nan")
            print(f"| {names[i]} | {names[j]} | {cam} | {len(both)} | {ma.mean():.2f} | {mb.mean():.2f} | {p:.3f} | "
                  f"{pa.mean():.1f} | {pb.mean():.1f} | {pp:.4f} |")
