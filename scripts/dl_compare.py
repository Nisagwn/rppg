#!/usr/bin/env python
"""
İki yöntemin aynı test videolarındaki hatasını eşleştirilmiş olarak karşılaştırır (makale/rapor için anlamlılık).

Girdi: dl_evaluate.py'nin test_sonuclari.csv'si (video × yöntem MAE). Video başına MAE farkı üzerinde iki yönlü
Wilcoxon işaretli sıra testi; ayrıca fark > 0.5 BPM olan video sayıları. 28 videoluk ana testte ±0.1 BPM'lik ortalama
farklar genellikle anlamlı değildir (ör. 7. tur B ile 5. tur: 1.13 / 1.10, p = 0.074).

    python scripts/dl_compare.py results/derin_ogrenme/kaggle_tur7_B/test_sonuclari.csv \\
        "MMRPhys sıfırdan (7. tur)+Viterbi" "5. tur+Viterbi"
    python scripts/dl_compare.py results/derin_ogrenme/kaggle_tur7_B/test_sonuclari.csv --list   # yöntem adları
"""
import argparse

import pandas as pd
from scipy.stats import wilcoxon


def compare(df, a, b):
    w = df.pivot_table(index="video", columns="yöntem", values="MAE")
    x, y = w[a], w[b]
    m = x.notna() & y.notna()
    x, y = x[m], y[m]
    d = x - y
    p = wilcoxon(x, y).pvalue if d.abs().sum() > 0 else 1.0
    return {"n": int(m.sum()), "a": float(x.mean()), "b": float(y.mean()), "a_iyi": int((d < -0.5).sum()),
            "b_iyi": int((d > 0.5).sum()), "p": float(p)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("a", nargs="?")
    ap.add_argument("b", nargs="?")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    df = pd.read_csv(a.csv)
    if a.list or not (a.a and a.b):
        print("\n".join(sorted(df["yöntem"].unique())))
        return
    r = compare(df, a.a, a.b)
    print(f"{r['n']} video | {a.a}: {r['a']:.2f} BPM | {a.b}: {r['b']:.2f} BPM | "
          f">0.5 BPM daha iyi: {r['a_iyi']} / {r['b_iyi']} video | Wilcoxon p = {r['p']:.3f}")


if __name__ == "__main__":
    main()
