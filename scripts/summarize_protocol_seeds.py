#!/usr/bin/env python
"""Standart protokolün açılmış çıktı klasörlerini tohum bazında birleştir.

python scripts/summarize_protocol_seeds.py results/derin_ogrenme/pure_weiqian_s1_seed42 --out results/standart_tekrarlar
Her klasörde gecmis.json ve test_*/test_ozet.csv, test_ozet_video.csv beklenir.
"""
import argparse
import json
from pathlib import Path

import pandas as pd


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    rows, seen = [], set()
    for folder in a.runs:
        root = Path(folder)
        hist = json.loads((root / "gecmis.json").read_text())
        settings = hist["ayarlar"]
        if hist["epoch"] < settings["epochs"]:
            raise ValueError(f"Eğitim henüz tamamlanmamış: {root}")
        source = settings["source_weights"]
        if source not in ("pure=1", "ubfc=1") or not settings["scratch"]:
            raise ValueError(f"Standart protokol değil: {root}")
        protocol = "S1" if source == "pure=1" else "S2"
        key = protocol, settings["seed"]
        if key in seen:
            raise ValueError(f"Aynı deney/tohum iki kez verildi: {key}")
        seen.add(key)
        tables = list(root.glob("test_*/test_ozet.csv"))
        if len(tables) != 1:
            raise ValueError(f"Tek hedef test özeti bekleniyor: {root}")
        summary = pd.read_csv(tables[0]).set_index("yöntem")
        video = pd.read_csv(tables[0].with_name("test_ozet_video.csv")).set_index("yöntem")
        for role, name in [("best", "En iyi epoch")]:
            rows.append({"protocol": protocol, "seed": settings["seed"], "checkpoint": role,
                         "epoch": hist["best"]["epoch"], "completed_epochs": hist["epoch"],
                         "window_MAE": summary.loc[name, "Hepsi"], "video_MAE": video.loc[name, "video_MAE"],
                         "video_RMSE": video.loc[name, "video_RMSE"], "n_test": video.loc[name, "n"], "run": str(root)})
    runs = pd.DataFrame(rows)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    runs.to_csv(out / "kosular.csv", index=False)
    aggregate = runs.groupby("protocol").agg(
        n_seeds=("seed", "nunique"), window_MAE_mean=("window_MAE", "mean"), window_MAE_std=("window_MAE", "std"),
        video_MAE_mean=("video_MAE", "mean"), video_MAE_std=("video_MAE", "std")).reset_index()
    aggregate.to_csv(out / "ozet.csv", index=False)
    report = ["# Standart protokol tekrarları", "",
              "Her koşuda checkpoint PURE/UBFC eğitim kaynağının doğrulama kişilerine göre seçilir; hedef teste göre seçilmez.",
              "Tek tohumla standart sapma hesaplanmaz. Başlangıç planı: her protokol için 42, 43, 44.",
              "Bu tablo yalnızca verilen ve tamamlanmış koşuları içerir; eksik eğitimler yapılmış sayılmaz.", "",
              runs.round(4).to_markdown(index=False), "", aggregate.round(4).to_markdown(index=False), ""]
    (out / "SONUCLAR.md").write_text("\n".join(report), encoding="utf-8")
    print(runs.to_string(index=False))


if __name__ == "__main__":
    main()
