#!/usr/bin/env python
"""PURE adayını mevcut uygulama modeliyle aynı işlenmiş test kayıtlarında karşılaştır."""
import argparse
import json
from pathlib import Path

import pandas as pd
from scipy.stats import wilcoxon
import torch

from dl_common import build_model
from dl_evaluate import evaluate, test_videos


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--candidate", default="results/derin_ogrenme/pure_weiqian_s1_seed42/best.pth")
    ap.add_argument("--baseline", default="results/derin_ogrenme/kaggle_tur5/last.pth")
    ap.add_argument("--candidate-name", default="PURE S1 best")
    ap.add_argument("--baseline-name", default="Uygulama tur5")
    ap.add_argument("--sets", nargs="+", default=["ana=data/dl/test", "kamera=data/dl/test_kamera"])
    ap.add_argument("--out", default="results/derin_ogrenme/pure_weiqian_s1_seed42/karsilastirma")
    a = ap.parse_args()
    if a.candidate_name == a.baseline_name:
        raise ValueError("Aday ve temel model adları farklı olmalı")
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    torch.manual_seed(42)
    torch.set_num_threads(4)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    rows, inventory = [], {}
    for group in a.sets:
        name, folder = group.split("=", 1)
        paths = test_videos(folder)
        if not paths:
            raise RuntimeError(f"Test kaydı yok: {folder}")
        inventory[name] = [Path(p).name for p in paths]
        for label, checkpoint in [(a.candidate_name, a.candidate), (a.baseline_name, a.baseline)]:
            model = build_model(device, checkpoint)
            # Aynı kırpıntı, ön işleme, örnekleme ve tahmin birleştirme iki modelde de kullanılır.
            for hop in (160, 80):
                print(f"{name}: {label}, hop={hop}, {len(paths)} video, {device}", flush=True)
                for row in evaluate(model, device, folder, label, hop=hop):
                    rows.append({"test": name, "hop": hop, **row})
            del model
    df = pd.DataFrame(rows)
    df.to_csv(out / "test_sonuclari.csv", index=False)
    summary = df.groupby(["test", "hop", "yöntem"]).agg(
        video=("video", "nunique"), pencere_MAE=("MAE", "mean"),
        video_MAE=("video_hata", "mean"), p5=("p5", "mean")).reset_index()
    summary.to_csv(out / "ozet.csv", index=False)
    pairs = []
    for (name, hop), g in df.groupby(["test", "hop"]):
        for suffix in ("", "+Viterbi"):
            w = g.pivot(index="video", columns="yöntem", values="MAE")
            w = w[[a.candidate_name + suffix, a.baseline_name + suffix]].dropna()
            x, y = w.iloc[:, 0], w.iloc[:, 1]
            delta = x - y
            pairs.append({"test": name, "hop": hop, "takip": suffix or "argmax", "n": len(w),
                          "aday_MAE": x.mean(), "mevcut_MAE": y.mean(),
                          "fark_aday_eksi_mevcut": delta.mean(),
                          "p_Wilcoxon": wilcoxon(x, y).pvalue if delta.abs().sum() else 1.0})
    pairs = pd.DataFrame(pairs)
    pairs.to_csv(out / "eslestirilmis.csv", index=False)
    (out / "ayarlar.json").write_text(json.dumps(
        {"candidate": a.candidate, "baseline": a.baseline, "candidate_name": a.candidate_name,
         "baseline_name": a.baseline_name, "device": str(device),
         "test_files": inventory, "hop": [160, 80]}, ensure_ascii=False, indent=2), encoding="utf-8")
    report = [f"# {a.candidate_name} ve {a.baseline_name}", "",
              "Her iki model aynı yerel test kayıtları ve aynı 72×72 yüz kırpıntıları üzerinde yeniden çalıştırıldı.",
              "Kullanılan kümeler: " + "; ".join(f"{name}: {len(files)} video" for name, files in inventory.items()) + ".",
              "Dosya listeleri ayarlar.json'dadır. Yüz kalitesi filtresinden geçen gerçek sayılar tabloda verilir.",
              "Hop 80 uygulamadaki %50 örtüşmeye karşılık gelir; hop 160 önceki çevrimdışı protokoldür.",
              "Pencere MAE: her videonun pencere hatası hesaplanıp videolar eşit ağırlıkla ortalanır.",
              "Video MAE: bütün kaydın spektral tepesinin mutlak hatasıdır; Viterbi bu sütunu değiştirmez.",
              "Bu ölçüm telefon tarayıcısının hızını veya canlı kullanıcı performansını ölçmez.", "",
              summary.round(3).to_markdown(index=False), "", "## Eşleştirilmiş video karşılaştırması", "",
              "Negatif fark aday lehine. p değerleri çoklu karşılaştırma düzeltmesi yapılmadan, keşif amaçlı verilmiştir.", "",
              pairs.round(5).to_markdown(index=False), ""]
    (out / "SONUCLAR.md").write_text("\n".join(report), encoding="utf-8")
    print(summary.round(3).to_string(index=False), flush=True)


if __name__ == "__main__":
    main()
