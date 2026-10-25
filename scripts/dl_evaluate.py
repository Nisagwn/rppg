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

from dl_common import CHUNK, PRETRAINED, ROOT, build_model, hr_from_bvp, predict_video, reference_hr, video_hr


CAMERA_NAMES = {"IriunWebcam": "telefon", "USBVideo": "USB"}


VIPL_CAMERAS = {}  # kaynak -> kamera eşlemesi bu kopyada belgelenmemiş; gruplar kaynak adıyla raporlanır


def group_of(meta):
    src = str(meta["source"])
    if src == "ubfc":
        return "UBFC"
    if src == "mmpd":
        return "MMPD (telefon)"
    if src == "vipl":
        return f"VIPL ({VIPL_CAMERAS.get(str(meta['camera']), str(meta['camera']))})"
    if src == "cohface":
        return "COHFACE"
    if src == "dlcn":
        return "DLCN gece " + str(meta["step"]).split("_")[0]
    if src == "own":  # uygulamanın veri kaydı (scripts/import_own.py)
        return "Kendi kayıt (" + {"telefon_on": "ön kamera", "telefon_arka": "arka kamera"}.get(str(meta["camera"]), "telefon") + ")"
    if src == "ubfcphys":  # T1 dinlenme, T2 konuşma, T3 aritmetik (bilek sensörü)
        return "UBFC-Phys " + {"T1": "dinlenme", "T2": "konuşma", "T3": "aritmetik"}.get(str(meta["step"]), str(meta["step"]))
    g = "MCD dinlenme" if str(meta["step"]) == "before" else "MCD egzersiz"
    cam = CAMERA_NAMES.get(str(meta["camera"]))
    return f"{g} ({cam})" if cam else g


def pos_crop(frames, fs=30.0):
    """Klasik taban çizgisi: modelle aynı 72x72 yüz kırpıntısının ortasında POS (her test kümesinde ölçülebilir)."""
    from rppg.methods import pos
    rgb = np.concatenate([np.asarray(frames[i:i + 600, 15:57, 15:57], dtype=np.float32).mean((1, 2))
                          for i in range(0, len(frames), 600)])  # parça parça: memory-map'i belleğe almadan
    return pos(rgb.astype(float), fs)


MIN_FACE = 0.5  # eğitimdeki kural: yüzün karelerin yarısından azında bulunduğu video kırpıntısı anlamsız


def test_videos(test_dir):
    return [p for p in sorted(glob.glob(os.path.join(test_dir, "*.npz"))) if float(np.load(p)["face_rate"]) >= MIN_FACE]


def video_name(p):
    """Test kümelerinde dosya adı <kaynak>_<video> (mcd_1020_..., ubfc_subject1); eğitim klasörlerinde önek yok
    (ubfc/subject10). Standart protokol testi eğitim klasörünü de kullandığı için ikisi de desteklenir."""
    s = os.path.basename(p)[:-4]
    return s.split("_", 1)[1] if "_" in s else s


def evaluate(model, device, test_dir, label, **predict_kw):
    """model: FactorizePhys ya da "POS" (pos_crop). predict_kw: predict_video'ya (hop, flip)."""
    rows = []
    for p in test_videos(test_dir):
        meta = np.load(p)
        frames = np.load(p[:-4] + ".npy", mmap_mode="r")
        pred = pos_crop(frames) if model == "POS" else predict_video(model, np.asarray(frames), device, **predict_kw)
        c, hr_a, hr_v = hr_from_bvp(pred)
        ref = reference_hr(meta["bvp"], c)
        name = video_name(p)
        verr = abs(video_hr(pred) - video_hr(meta["bvp"]))   # video düzeyi (literatürle karşılaştırma için)
        for suffix, hr in (("", hr_a), ("+Viterbi", hr_v)):
            err = np.abs(hr - ref)
            rows.append({"grup": group_of(meta), "video": name, "yöntem": label + suffix,
                         "MAE": float(err.mean()), "p5": float(100 * np.mean(err <= 5)), "video_hata": verr})
    return rows


def table(df):
    order = ["UBFC", "MCD dinlenme", "MCD egzersiz"]
    order = [c for c in order if c in set(df.grup)] + sorted(set(df.grup) - set(order))
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
    ap.add_argument("--data", default=os.path.join(ROOT, "data/dl"), help="eğitim verisi (rapordaki özet için)")
    ap.add_argument("--history", default="", help="gecmis.json (varsayılan: modelin klasörü)")
    ap.add_argument("--name", default="FactorizePhys ince ayarlı", help="eğitilen modelin tablodaki adı")
    ap.add_argument("--compare", nargs="*", default=[], metavar="AD=YOL",
                    help="aynı test videolarında ayrıca ölçülecek modeller (ör. önceki tur)")
    ap.add_argument("--tta", action="store_true",
                    help="ince ayarlı modeli ayrıca örtüşmeli parçalarla (%%50, mobil uygulamadaki gibi) ve yatay çevirmeyle de ölç "
                         "(yeniden eğitim gerektirmeyen çıkarım iyileştirmesi; ek satırlar)")
    a = ap.parse_args()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    n_all = len(glob.glob(os.path.join(a.test, "*.npz")))
    n_test = len(test_videos(a.test))
    if n_all > n_test:
        print(f"{n_all - n_test} video yüz bulunma oranı <%{100 * MIN_FACE:.0f} olduğu için dışarıda", flush=True)
    if n_test == 0:
        raise SystemExit(f"Test klasöründe video yok: {a.test} (önce scripts/dl_prepare.py --test ya da --test-download)")
    print(f"test: {n_test} video", flush=True)

    rows = evaluate("POS", device, a.test, "POS (yüz kırpıntısı)")
    rows += evaluate(build_model(device, PRETRAINED), device, a.test, "FactorizePhys PURE (hazır)")
    tuned = build_model(device, a.model)
    rows += evaluate(tuned, device, a.test, a.name)
    if a.tta:
        rows += evaluate(tuned, device, a.test, a.name + " (örtüşmeli)", hop=CHUNK // 2)
        rows += evaluate(tuned, device, a.test, a.name + " (örtüşmeli+çevirme)", hop=CHUNK // 2, flip=True)
    del tuned
    last = os.path.join(os.path.dirname(a.model), "last.pth")
    if os.path.exists(last) and os.path.abspath(last) != os.path.abspath(a.model):
        rows += evaluate(build_model(device, last), device, a.test, f"{a.name} (son epoch)")
    for item in a.compare:
        name, path = item.split("=", 1)
        if os.path.exists(path):
            rows += evaluate(build_model(device, path), device, a.test, name)
    df = pd.DataFrame(rows)
    if os.path.exists(a.prev):
        prev = pd.read_csv(a.prev)
        prev = prev[prev["yöntem"].str.startswith("POS")]
        df = pd.concat([df, prev[prev.video.isin(df.video)]], ignore_index=True)

    os.makedirs(a.out, exist_ok=True)
    df.to_csv(os.path.join(a.out, "test_sonuclari.csv"), index=False)
    t = table(df)
    t.round(2).to_csv(os.path.join(a.out, "test_ozet.csv"))
    if "video_hata" in df:   # video düzeyi MAE/RMSE (bütün videonun spektral tepesi; literatür tablolarıyla aynı tür)
        v = df[~df["yöntem"].str.endswith("+Viterbi")].groupby("yöntem")["video_hata"]
        tv = pd.DataFrame({"video_MAE": v.mean(), "video_RMSE": v.apply(lambda e: float(np.sqrt(np.mean(e ** 2)))),
                           "n": v.count()}).sort_values("video_MAE")
        tv.round(2).to_csv(os.path.join(a.out, "test_ozet_video.csv"))
        print("\nvideo düzeyi:\n" + tv.round(2).to_string())
    print(t.round(2).to_string())

    # Referans etiketi temiz test videoları (dl_quality: etiketin ≥%80'i iyi). Ana tablo değişmez; bu ek bilgi:
    # bazı test videolarında hatanın kaynağı modelden çok referans sensörün kendisi.
    from dl_quality import compute as quality
    ref_q = {}
    for p in test_videos(a.test):
        q = quality(p)
        if q:
            ref_q[video_name(p)] = q
    clean = [v for v, q in ref_q.items() if q["ok_frac"] >= 0.8]
    t_clean = table(df[df.video.isin(clean)]) if clean else None
    if t_clean is not None:
        t_clean.round(2).to_csv(os.path.join(a.out, "test_ozet_temiz_referans.csv"))
        print(f"\nreferansı temiz {len(clean)} video:\n" + t_clean.round(2).to_string())

    # video bazında: ince ayarlı + Viterbi vs POS tüm yüz + Viterbi
    w = df.pivot_table(index="video", columns="yöntem", values="MAE")
    a_, b_ = f"{a.name}+Viterbi", "POS tüm yüz+Viterbi"
    if a_ in w and b_ in w:
        d = w[a_] - w[b_]
        info = {"esit_0.5": int((d.abs() <= 0.5).sum()), "dl_daha_iyi": int((d < -0.5).sum()),
                "dl_daha_kotu": int((d > 0.5).sum()), "n": int(d.notna().sum())}
        json.dump(info, open(os.path.join(a.out, "video_karsilastirma.json"), "w"), indent=1)
        print(info)
    else:
        info = None
    write_report(a, t, info, w, t_clean, ref_q)


def md_header(t):
    return ["| Yöntem | " + " | ".join(t.columns) + " |", "|---|" + "---:|" * len(t.columns)]


def training_lines(cfg, loss_name="negatif Pearson"):
    """Rapordaki artırma/kayıp/seçim satırları; gecmis.json'daki eğitim ayarlarından (eski turlarda yok: varsayılanlar).
    loss_name: mimariye göre varsayılan kayıp (write_report); ayarlarda --loss verilmişse o yazılır."""
    cfg = cfg or {}
    lo, hi = cfg.get("speed", [0.8, 1.25])
    aug = f"- Artırma: yatay çevirme, hız {lo:g}–{hi:g}× (HR aralığını genişletir), parlaklık ×0.8–1.2"
    if cfg.get("phone_aug"):
        aug += "; telefon bozulmaları (el titremesi, düşük çözünürlük, renk sıcaklığı, loş ışık + gürültü)"
    if cfg.get("box_jitter", 0) > 0:
        aug += f"; yüz kutusu kayması ±%{100 * cfg['box_jitter']:.0f}"
    if cfg.get("hr_balance", 0) > 1:
        aug += f"; nabız dengeli örnekleme (seyrek nabız aralıkları en fazla {cfg['hr_balance']:g}×)"
    names = {"pearson": "negatif Pearson", "smoothl1": "SmoothL1 (standartlaştırılmış tahmin ve etiket)"}
    loss = f"- Kayıp: {names.get(cfg.get('loss') or '', loss_name)}"
    if cfg.get("spec_loss", 0) > 0:
        loss += f" + {cfg['spec_loss']:g} × spektral KL (nabız bandı)"
    loss += "; AdamW, cosine öğrenme oranı"
    if cfg.get("amp"):
        loss += ", karışık hassasiyet (float16)"
    sel = "Viterbi" if cfg.get("val_viterbi") else "argmax"
    sel = f"- Seçim: en iyi epoch doğrulama kişilerinde pencere MAE ({sel}) ile"
    if cfg.get("ema", 0) > 0:
        sel += f"; ağırlıkların EMA'sı ({cfg['ema']:g}) doğrulandı ve kaydedildi"
    return [aug, loss, sel]


def write_report(a, t, info, w, t_clean=None, ref_q=None):
    """results/derin_ogrenme/egitim/SONUCLAR.md"""
    hist_path = a.history or os.path.join(os.path.dirname(a.model), "gecmis.json")
    hist = json.load(open(hist_path)) if os.path.exists(hist_path) else None
    data = a.data
    subs = ("mcd", "ubfc", "pure", "vipl", "dlcn", "cohface", "ubfcphys")
    metas = [np.load(p) for sub in subs for p in glob.glob(os.path.join(data, sub, "*.npz"))]
    used = [m for m in metas if float(m["face_rate"]) >= 0.5]
    people = {str(m["person"]) for m in used}
    hours = sum(int(m["n"]) for m in used) / 30 / 3600

    import torch
    ck = torch.load(a.model, map_location="cpu")
    arch = ck.get("arch", "factorizephys") if isinstance(ck, dict) else "factorizephys"
    init = ck.get("init") if isinstance(ck, dict) else None  # dl_train kaydeder; eski kontrol noktalarında yok
    if arch == "mmrphys":
        what = (f"MMRPhys (Joshi ve Cho 2025) `{init}` ağırlıklarından başlatılarak eğitildi" if init else
                "MMRPhys (Joshi ve Cho 2025) **rastgele başlatılarak (sıfırdan)** eğitildi; hiçbir hazır ağırlık "
                "kullanılmadı")
        loss = "SmoothL1 (standartlaştırılmış tahmin ve etiket; TSFM eğitimde etiketi kısıt olarak kullanır)"
    else:
        what = "FactorizePhys (rPPG-Toolbox) eğitildi (başlangıç ağırlıkları eğitim günlüğünde)"
        loss = "negatif Pearson"
    L = [f"# {a.name} — Test Sonuçları", "",
         f"{what}. Eğitimde yalnızca test **dışı** kişiler kullanıldı; test kümesi `{os.path.basename(a.test)}`. "
         "Test kişileri eğitim ve doğrulamada hiç kullanılmadı.", "",
         "## Eğitim verisi", "",
         f"- {len(used)} video, {len(people)} kişi, {hours:.1f} saat (yüz bulunma oranı <%50 olan "
         f"{len(metas) - len(used)} video çıkarıldı)",
         f"- MCD: {sum(str(m['source']) == 'mcd' for m in used)} video (3 kamera: önden webcam, sol USB, sağ telefon; "
         "dinlenme + egzersiz sonrası), video başına ilk "
         f"{np.median([int(m['n']) for m in used if str(m['source']) == 'mcd'] or [0]) / 30:.0f} s",
         f"- UBFC: {sum(str(m['source']) == 'ubfc' for m in used)} denek",
         f"- PURE: {sum(str(m['source']) == 'pure' for m in used)} oturum (10 kişi × 6 hareket senaryosu; HF kopyası)",
         *[f"- {name}: {sum(str(m['source']) == src for m in used)} video (etiket model tabanlı video başına hizalandı; "
           "hizalı korelasyonu zayıf olanlar eğitimde çıkarıldı)"
           for src, name in (("vipl", "VIPL-HR (source1/3)"), ("dlcn", "DLCN"), ("cohface", "COHFACE"),
                             ("ubfcphys", "UBFC-Phys (bilek sensörü)"))
           if any(str(m['source']) == src for m in used)],
         "- Ön işleme toolbox ile aynı (Haar ×1.5, 30 karede bir tespit, 72×72, ham kare); hepsi 30 fps'e yeniden örneklendi",
         "- MCD parmak PPG'si UBFC/PURE'a göre ters işaretli (ön-eğitimli model çıktısıyla korelasyon ≈ −0.75, "
         "gecikme ≈ 0); eğitimde ters çevrildi",
         *training_lines(hist.get("ayarlar") if hist else None, loss), ""]
    if hist:
        h = [x for x in hist["history"] if x.get("val_mae") is not None]
        L += [f"Eğitim: {hist['epoch']} epoch (500 adım × 8 parça). Doğrulama MAE: başlangıç "
              f"{h[0]['val_mae']:.2f} → en iyi {hist['best']['val_mae']:.2f} BPM (epoch {hist['best']['epoch']}).", ""]
    L += [f"## Ortalama MAE (BPM) — {len(w)} test videosu", "", *md_header(t)]
    for name, r in t.iterrows():
        L.append(f"| {name} | " + " | ".join(f"{v:.2f}" if v == v else "–" for v in r.values) + " |")
    if info:
        L += ["", "## Video bazında (ince ayarlı + Viterbi vs POS tüm yüz + Viterbi)", "",
              f"- {info['n']} videonun {info['esit_0.5']}'inde fark ≤0.5 BPM, {info['dl_daha_iyi']}'inde ince ayarlı "
              f"model daha iyi, {info['dl_daha_kotu']}'inde daha kötü."]
        worst = w["POS tüm yüz+Viterbi"].sort_values(ascending=False).head(5)
        L += ["", "En zor 5 video (POS'a göre):", "", f"| Video | POS+Viterbi | PURE hazır+Viterbi | {a.name}+Viterbi |",
              "|---|---:|---:|---:|"]
        for v in worst.index:
            L.append(f"| {v} | {w.loc[v, 'POS tüm yüz+Viterbi']:.2f} | "
                     f"{w.loc[v, 'FactorizePhys PURE (hazır)+Viterbi']:.2f} | "
                     f"{w.loc[v, a.name + '+Viterbi']:.2f} |")
    if t_clean is not None:
        bad = {v: q for v, q in ref_q.items() if q["ok_frac"] < 0.8}
        L += ["", f"## Referans etiketi temiz test videoları ({len(ref_q) - len(bad)}/{len(ref_q)})", "",
              "Referans sensör sinyalinin ≥%80'i iyi olan videolar (`scripts/dl_quality.py`: SNR ≥ 0 dB, nabız 40–180, "
              "sıçrama yok). Çıkarılanlar: " + ", ".join(f"{v} (iyi %{100 * q['ok_frac']:.0f}, SNR {q['snr_med']:.1f} dB)"
                                                       for v, q in bad.items()) + ".", "",
              *md_header(t_clean)]
        for name, r in t_clean.iterrows():
            L.append(f"| {name} | " + " | ".join(f"{v:.2f}" if v == v else "–" for v in r.values) + " |")
    L += ["", "Ayrıntı: `test_sonuclari.csv` (video × yöntem), `test_ozet.csv`, `gecmis.json` (epoch geçmişi).",
          "Yeniden üretmek: `scripts/dl_prepare.py` → `scripts/dl_train.py` → `scripts/dl_evaluate.py` "
          "(ya da hepsi: `scripts/dl_pipeline.py`)."]
    open(os.path.join(a.out, "SONUCLAR.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("rapor:", os.path.join(a.out, "SONUCLAR.md"))


if __name__ == "__main__":
    main()
