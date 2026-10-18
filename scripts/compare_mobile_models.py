#!/usr/bin/env python
"""
Mobil uygulamada çalışan modellerin gerçek veri doğrulamasını (validate_mobile.py --models) karşılaştırır.

Kamera başına: kesit başına uygulama MAE'sinin ortalaması ve kapsama (üretilen pencere / kesit × 25; 40 s'lik
kesitte ısınmadan sonra en fazla ~25 saniyelik ölçüm çıkar). Model çiftleri yalnızca iki modelin de pencere ürettiği
kesitlerde, kesit başına MAE üzerinde iki yönlü eşleştirilmiş Wilcoxon işaretli sıra testiyle karşılaştırılır.

    python scripts/compare_mobile_models.py results/mobil_dogrulama_modeller tur3 tur5 7E
"""
import argparse
import itertools
import os

import pandas as pd
from scipy.stats import wilcoxon

MAX_WIN = 25


def load(root, names):
    out = {}
    for n in names:
        d = pd.read_csv(os.path.join(root, n, "kesitler.csv"))
        out[n] = d.set_index("ad")
    return out


def summary(dfs):
    rows = []
    for n, d in dfs.items():
        for cam, g in list(d.groupby("kamera")) + [("hepsi", d)]:
            rows.append({"model": n, "kamera": cam, "kesit": len(g), "pencereli_kesit": int((g.pencere > 0).sum()),
                         "kapsama_%": 100 * g.pencere.sum() / (len(g) * MAX_WIN),
                         "MAE": g.uygulama_MAE.mean(), "≤5BPM_%": g["uygulama_≤5BPM%"].mean(),
                         "model_ms_medyan": g.model_ms.median() if "model_ms" in g else float("nan")})
    return pd.DataFrame(rows)


def pairs(dfs):
    rows = []
    for a, b in itertools.combinations(dfs, 2):
        da, db = dfs[a], dfs[b]
        for cam in sorted(da.kamera.unique()) + ["hepsi"]:
            idx = da.index if cam == "hepsi" else da.index[da.kamera == cam]
            x, y = da.loc[idx, "uygulama_MAE"], db.reindex(idx)["uygulama_MAE"]
            m = x.notna() & y.notna()
            x, y = x[m], y[m]
            d = x - y
            p = wilcoxon(x, y).pvalue if len(d) >= 2 and d.abs().sum() > 0 else float("nan")
            pw = da.loc[idx, "pencere"], db.reindex(idx)["pencere"]
            pp = wilcoxon(pw[0], pw[1]).pvalue if (pw[0] - pw[1]).abs().sum() > 0 else float("nan")
            rows.append({"A": a, "B": b, "kamera": cam, "ortak_kesit": int(m.sum()), "A_MAE": x.mean(),
                         "B_MAE": y.mean(), "A_iyi(>0.5)": int((d < -0.5).sum()), "B_iyi(>0.5)": int((d > 0.5).sum()),
                         "p_MAE": p, "A_pencere": int(pw[0].sum()), "B_pencere": int(pw[1].sum()), "p_pencere": pp})
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("names", nargs="+")
    ap.add_argument("--out", help="markdown çıktısı (varsayılan: <root>/KARSILASTIRMA.md)")
    a = ap.parse_args()
    dfs = load(a.root, a.names)
    s, p = summary(dfs).round(2), pairs(dfs).round(3)
    lines = ["# Mobil Uygulama — Model Karşılaştırması (gerçek veri, tarayıcıda)", "",
             "Kapsama: üretilen pencere / (kesit × 25). MAE: kesit başına ortalama (pencere üretmeyen kesit hariç).", "",
             "## Kamera başına", "", s.to_markdown(index=False), "",
             "## Eşleştirilmiş Wilcoxon (kesit başına; MAE yalnızca iki modelin de pencere ürettiği kesitlerde)", "",
             p.to_markdown(index=False), ""]
    out = a.out or os.path.join(a.root, "KARSILASTIRMA.md")
    open(out, "w", encoding="utf-8").write("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
