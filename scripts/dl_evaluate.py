#!/usr/bin/env python
"""
İnce ayarlı FactorizePhys'i önceki karşılaştırmanın 28 test videosunda (UBFC 8 + MCD önden webcam 20)
ön-eğitimli (PURE) model ve klasik POS hattıyla karşılaştırır.

BVP -> detrend + Butterworth -> 10 s pencere / 1 s adım -> argmax veya Viterbi.
Referans: parmak PPG'sinden pencere başına spektral tepe.
POS satırları results/derin_ogrenme/tum_sonuclar.csv'den (aynı videolar) alınır.

    python scripts/dl_evaluate.py --model results/derin_ogrenme/egitim/best.pth
"""
import argparse
import glob
import json
import os

import numpy as np
import pandas as pd

from dl_common import PRETRAINED, ROOT, build_model, hr_from_bvp, predict_video, reference_hr


def group_of(meta):
    if str(meta["source"]) == "ubfc":
        return "UBFC"
    return "MCD dinlenme" if str(meta["step"]) == "before" else "MCD egzersiz"


def evaluate(model, device, test_dir, label):
    rows = []
    for p in sorted(glob.glob(os.path.join(test_dir, "*.npz"))):
        meta = np.load(p)
        frames = np.load(p[:-4] + ".npy", mmap_mode="r")
        pred = predict_video(model, np.asarray(frames), device)
        c, hr_a, hr_v = hr_from_bvp(pred)
        ref = reference_hr(meta["bvp"], c)
        name = os.path.basename(p)[:-4].split("_", 1)[1]
        for suffix, hr in (("", hr_a), ("+Viterbi", hr_v)):
            err = np.abs(hr - ref)
            rows.append({"grup": group_of(meta), "video": name, "yöntem": label + suffix,
                         "MAE": float(err.mean()), "p5": float(100 * np.mean(err <= 5))})
    return rows


def table(df):
    order = ["UBFC", "MCD dinlenme", "MCD egzersiz"]
    g = df.pivot_table(index="yöntem", columns="grup", values="MAE", aggfunc="mean").reindex(columns=order)
    g["Hepsi"] = df.groupby("yöntem")["MAE"].mean()
    g["≤5 BPM %"] = df.groupby("yöntem")["p5"].mean()
    g["Medyan"] = df.groupby("yöntem")["MAE"].median()
    return g.sort_values("Hepsi")


def main():
    import torch
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=os.path.join(ROOT, "results/derin_ogrenme/egitim/best.pth"))
    ap.add_argument("--test", default=os.path.join(ROOT, "data/dl/test"))
    ap.add_argument("--prev", default=os.path.join(ROOT, "results/derin_ogrenme/tum_sonuclar.csv"))
    ap.add_argument("--out", default=os.path.join(ROOT, "results/derin_ogrenme/egitim"))
    a = ap.parse_args()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    rows = evaluate(build_model(device, PRETRAINED), device, a.test, "FactorizePhys PURE (hazır)")
    rows += evaluate(build_model(device, a.model), device, a.test, "FactorizePhys ince ayarlı")
    last = os.path.join(os.path.dirname(a.model), "last.pth")
    if os.path.exists(last) and os.path.abspath(last) != os.path.abspath(a.model):
        rows += evaluate(build_model(device, last), device, a.test, "FactorizePhys ince ayarlı (son epoch)")
    df = pd.DataFrame(rows)
    if os.path.exists(a.prev):
        prev = pd.read_csv(a.prev)
        prev = prev[prev["yöntem"].str.startswith("POS")]
        df = pd.concat([df, prev[prev.video.isin(df.video)]], ignore_index=True)

    os.makedirs(a.out, exist_ok=True)
    df.to_csv(os.path.join(a.out, "test_sonuclari.csv"), index=False)
    t = table(df)
    t.round(2).to_csv(os.path.join(a.out, "test_ozet.csv"))
    print(t.round(2).to_string())

    # video bazında: ince ayarlı + Viterbi vs POS tüm yüz + Viterbi
    w = df.pivot_table(index="video", columns="yöntem", values="MAE")
    a_, b_ = "FactorizePhys ince ayarlı+Viterbi", "POS tüm yüz+Viterbi"
    if a_ in w and b_ in w:
        d = w[a_] - w[b_]
        info = {"esit_0.5": int((d.abs() <= 0.5).sum()), "dl_daha_iyi": int((d < -0.5).sum()),
                "dl_daha_kotu": int((d > 0.5).sum()), "n": int(d.notna().sum())}
        json.dump(info, open(os.path.join(a.out, "video_karsilastirma.json"), "w"), indent=1)
        print(info)
    else:
        info = None
    write_report(a, t, info, w)


def write_report(a, t, info, w):
    """results/derin_ogrenme/egitim/SONUCLAR.md"""
    hist_path = os.path.join(os.path.dirname(a.model), "gecmis.json")
    hist = json.load(open(hist_path)) if os.path.exists(hist_path) else None
    data = os.path.join(ROOT, "data", "dl")
    metas = [np.load(p) for sub in ("mcd", "ubfc", "pure") for p in glob.glob(os.path.join(data, sub, "*.npz"))]
    used = [m for m in metas if float(m["face_rate"]) >= 0.5]
    people = {str(m["person"]) for m in used}
    hours = sum(int(m["n"]) for m in used) / 30 / 3600

    L = ["# İnce Ayarlı FactorizePhys — Test Sonuçları", "",
         "PURE'da ön-eğitimli FactorizePhys (rPPG-Toolbox) MCD-rPPG + UBFC-rPPG'nin **test dışı** kişileriyle "
         "ince ayarlandı ve önceki karşılaştırmanın aynı 28 videosunda (UBFC 8 denek + MCD önden webcam 20 video, "
         "10 kişi) test edildi. Test kişileri eğitim ve doğrulamada hiç kullanılmadı.", "",
         "## Eğitim verisi", "",
         f"- {len(used)} video, {len(people)} kişi, {hours:.1f} saat (yüz bulunma oranı <%50 olan "
         f"{len(metas) - len(used)} video çıkarıldı)",
         f"- MCD: {sum(str(m['source']) == 'mcd' for m in used)} video (3 kamera: önden webcam, sol USB, sağ telefon; "
         "dinlenme + egzersiz sonrası), ilk 45 s (disk için; kişi çeşitliliği süreden önemli)",
         f"- UBFC: {sum(str(m['source']) == 'ubfc' for m in used)} denek",
         f"- PURE: {sum(str(m['source']) == 'pure' for m in used)} oturum (10 kişi × 6 hareket senaryosu; HF kopyası)",
         "- Ön işleme toolbox ile aynı (Haar ×1.5, 30 karede bir tespit, 72×72, ham kare); hepsi 30 fps'e yeniden örneklendi",
         "- MCD parmak PPG'si UBFC/PURE'a göre ters işaretli (ön-eğitimli model çıktısıyla korelasyon ≈ −0.75, "
         "gecikme ≈ 0); eğitimde ters çevrildi",
         "- Artırma: yatay çevirme, hız 0.8–1.25× (HR aralığını genişletir), parlaklık ×0.8–1.2",
         "- Kayıp: negatif Pearson; AdamW, cosine öğrenme oranı; en iyi epoch doğrulama kişilerinde pencere MAE ile seçildi", ""]
    if hist:
        h = [x for x in hist["history"] if x.get("val_mae") is not None]
        L += [f"Eğitim: {hist['epoch']} epoch (500 adım × 8 parça). Doğrulama MAE: ön-eğitimli "
              f"{h[0]['val_mae']:.2f} → en iyi {hist['best']['val_mae']:.2f} BPM (epoch {hist['best']['epoch']}).", ""]
    L += ["## Ortalama MAE (BPM) — 28 test videosu", "",
          "| Yöntem | UBFC | MCD dinlenme | MCD egzersiz | Hepsi | ≤5 BPM % | Medyan |",
          "|---|---:|---:|---:|---:|---:|---:|"]
    for name, r in t.iterrows():
        L.append(f"| {name} | " + " | ".join(f"{v:.2f}" if v == v else "–" for v in r.values) + " |")
    if info:
        L += ["", "## Video bazında (ince ayarlı + Viterbi vs POS tüm yüz + Viterbi)", "",
              f"- {info['n']} videonun {info['esit_0.5']}'inde fark ≤0.5 BPM, {info['dl_daha_iyi']}'inde ince ayarlı "
              f"model daha iyi, {info['dl_daha_kotu']}'inde daha kötü."]
        worst = w["POS tüm yüz+Viterbi"].sort_values(ascending=False).head(5)
        L += ["", "En zor 5 video (POS'a göre):", "", "| Video | POS+Viterbi | PURE hazır+Viterbi | İnce ayarlı+Viterbi |",
              "|---|---:|---:|---:|"]
        for v in worst.index:
            L.append(f"| {v} | {w.loc[v, 'POS tüm yüz+Viterbi']:.2f} | "
                     f"{w.loc[v, 'FactorizePhys PURE (hazır)+Viterbi']:.2f} | "
                     f"{w.loc[v, 'FactorizePhys ince ayarlı+Viterbi']:.2f} |")
    L += ["", "Ayrıntı: `test_sonuclari.csv` (video × yöntem), `test_ozet.csv`, `gecmis.json` (epoch geçmişi).",
          "Yeniden üretmek: `scripts/dl_prepare.py` → `scripts/dl_train.py` → `scripts/dl_evaluate.py` "
          "(ya da hepsi: `scripts/dl_pipeline.py`)."]
    open(os.path.join(a.out, "SONUCLAR.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("rapor:", os.path.join(a.out, "SONUCLAR.md"))


if __name__ == "__main__":
    main()
