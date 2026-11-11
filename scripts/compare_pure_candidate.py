#!/usr/bin/env python
"""Bir model adayını mevcut uygulama modeliyle aynı işlenmiş test kayıtlarında karşılaştır (varsayılan CPU)."""
import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd
from scipy.stats import wilcoxon
import torch

from dl_common import build_model
from dl_evaluate import evaluate, test_videos, video_name


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--candidate", default="results/derin_ogrenme/pure_weiqian_s1_seed42/best.pth")
    ap.add_argument("--baseline", default="results/derin_ogrenme/kaggle_tur5/last.pth")
    ap.add_argument("--candidate-name", default="PURE S1 best")
    ap.add_argument("--baseline-name", default="Uygulama tur5")
    ap.add_argument("--candidate-config", help="Adayın model ayarlarını içeren JSON (md_config, dropout, arch)")
    ap.add_argument("--device", choices=("cpu", "auto", "cuda"), default="cpu")
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--hops", nargs="+", type=int, choices=(80, 160), default=[160, 80])
    ap.add_argument("--baseline-cache", help="Aynı testlerin önceki temel model sonuç CSV'si")
    ap.add_argument("--baseline-cache-provenance", help="Önceki temel modelin checkpoint_sha256 değerini içeren JSON")
    ap.add_argument("--sets", nargs="+", default=["ana=data/dl/test", "kamera=data/dl/test_kamera"])
    ap.add_argument("--out", default="results/derin_ogrenme/pure_weiqian_s1_seed42/karsilastirma")
    a = ap.parse_args()
    if a.candidate_name == a.baseline_name:
        raise ValueError("Aday ve temel model adları farklı olmalı")
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    torch.manual_seed(42)
    if a.threads < 1:
        raise ValueError("CPU iş parçacığı sayısı pozitif olmalı")
    torch.set_num_threads(a.threads)
    device = torch.device(("cuda" if torch.cuda.is_available() else "cpu") if a.device == "auto" else a.device)
    cache, cache_settings = None, {}
    if a.baseline_cache:
        if not a.baseline_cache_provenance:
            raise ValueError("Önbellek için checkpoint SHA-256 kanıtı gerekli")
        proof = json.loads(Path(a.baseline_cache_provenance).read_text(encoding="utf-8"))
        if proof["checkpoint_sha256"] != hashlib.sha256(Path(a.baseline).read_bytes()).hexdigest():
            raise ValueError("Önbelleğin temel model ağırlıkları farklı")
        cache = pd.read_csv(a.baseline_cache)
        cache_settings = json.loads(Path(a.baseline_cache).with_name("ayarlar.json").read_text(encoding="utf-8"))
        if Path(cache_settings["baseline"]).resolve() != Path(a.baseline).resolve():
            raise ValueError("Önbelleğin temel model yolu farklı")
    profile = json.loads(Path(a.candidate_config).read_text(encoding="utf-8")) if a.candidate_config else {}
    candidate_kw = {k: profile[k] for k in ("md_config", "dropout", "arch") if k in profile}
    rows, inventory, loads = [], {}, {}
    for group in a.sets:
        name, folder = group.split("=", 1)
        paths = test_videos(folder)
        if not paths:
            raise RuntimeError(f"Test kaydı yok: {folder}")
        inventory[name] = [Path(p).name for p in paths]
        for label, checkpoint in [(a.candidate_name, a.candidate), (a.baseline_name, a.baseline)]:
            if label == a.baseline_name and cache is not None:
                if set(cache_settings["test_files"].get(name, [])) != set(inventory[name]):
                    raise ValueError("Önbelleğin kaynak dosya listesi farklı")
                expected = {video_name(p) for p in paths}
                selected = cache[(cache["test"] == name) & cache["hop"].isin(a.hops)
                                 & cache["yöntem"].isin([label, label + "+Viterbi"])].copy()
                if selected.duplicated(["hop", "video", "yöntem"]).any():
                    raise ValueError("Temel model önbelleğinde tekrarlanan satırlar var")
                for hop in a.hops:
                    for method in [label, label + "+Viterbi"]:
                        if set(selected[(selected.hop == hop) & (selected["yöntem"] == method)].video) != expected:
                            raise ValueError("Temel model önbelleğinin test dosyaları farklı")
                rows.extend(selected.to_dict("records"))
                loads[label] = {"checkpoint_sha256": proof["checkpoint_sha256"],
                                "cached_results": a.baseline_cache, "device": cache_settings.get("device", "bilinmiyor"),
                                "recomputed_in_this_run": False}
                continue
            model = build_model(device, checkpoint, **(candidate_kw if label == a.candidate_name else {}))
            loads[label] = {"md_config": model.md_config, "load_report": getattr(model, "load_report", {}),
                            "checkpoint_sha256": hashlib.sha256(Path(checkpoint).read_bytes()).hexdigest()}
            # Aynı kırpıntı, ön işleme, örnekleme ve tahmin birleştirme iki modelde de kullanılır.
            for hop in a.hops:
                print(f"{name}: {label}, hop={hop}, {len(paths)} video, {device}", flush=True)
                for i, path in enumerate(paths, 1):
                    for row in evaluate(model, device, folder, label, files=[path], hop=hop):
                        rows.append({"test": name, "hop": hop, **row})
                    pd.DataFrame(rows).to_csv(out / "kismi_sonuclar.csv", index=False)
                    if i % 5 == 0 or i == len(paths):
                        print(f"  {i}/{len(paths)} video tamamlandı", flush=True)
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
         "test_files": inventory, "hop": a.hops, "candidate_profile": profile,
         "model_loads": loads}, ensure_ascii=False, indent=2), encoding="utf-8")
    report = [f"# {a.candidate_name} ve {a.baseline_name}", "",
              "Her iki model aynı yerel test kayıtları ve aynı 72×72 yüz kırpıntıları üzerinde yeniden çalıştırıldı.",
              "Kullanılan kümeler: " + "; ".join(f"{name}: {len(files)} video" for name, files in inventory.items()) + ".",
              "Dosya listeleri ayarlar.json'dadır. Yüz kalitesi filtresinden geçen gerçek sayılar tabloda verilir.",
              "Hop 80 uygulamadaki %50 örtüşmeye karşılık gelir; hop 160 önceki çevrimdışı protokoldür.",
              "Pencere MAE: her videonun pencere hatası hesaplanıp videolar eşit ağırlıkla ortalanır.",
              "Video MAE: bütün kaydın spektral tepesinin mutlak hatasıdır; Viterbi bu sütunu değiştirmez.",
              "Bu ölçüm telefon tarayıcısının hızını veya canlı kullanıcı performansını ölçmez.", "",
              f"Yeni çıkarım aygıtı: {device}. Temel model önbelleği: {a.baseline_cache or 'yok; aynı koşuda yeniden ölçüldü'}.", "",
              "Ağ ayarları ve yüklenmeyen ağırlıklar ayarlar.json'da kayıtlıdır. Ortak yüz kırpıntıları kullanıldığı için bu sonuçlar yazarların tüm ön işleme hattının yeniden üretimi değildir.", "",
              summary.round(3).to_markdown(index=False), "", "## Eşleştirilmiş video karşılaştırması", "",
              "Negatif fark aday lehine. p değerleri çoklu karşılaştırma düzeltmesi yapılmadan, keşif amaçlı verilmiştir.", "",
              pairs.round(5).to_markdown(index=False), ""]
    (out / "SONUCLAR.md").write_text("\n".join(report), encoding="utf-8")
    print(summary.round(3).to_string(index=False), flush=True)


if __name__ == "__main__":
    main()
