#!/usr/bin/env python
"""
MCD-rPPG veri seti üzerinde değerlendirme: yöntem ablasyonu + kamera x durum (dinlenme/egzersiz sonrası).

MCD-rPPG (Egorov vd., ACM MM 2025, CC-BY-4.0): 600 kişi x {dinlenme, egzersiz sonrası} x 3 kamera
    FullHDwebcam (önden webcam), USBVideo (sol yandan USB kamera), IriunWebcam (sağ yandan cep telefonu)
ve karelere hizalı parmak PPG referansı. Bu betik Hugging Face'teki erişime açık kopyadan
(akramic/mcd_rppg) istenen sayıda kişiyi indirir ve değerlendirir.

    python scripts/evaluate_mcd.py --download 10                # 10 kişiyi indir (~2.5 GB) ve değerlendir
    python scripts/evaluate_mcd.py                              # yalnızca inmiş olanları değerlendir
    python scripts/evaluate_mcd.py --cameras IriunWebcam --methods pos,chrom

İzler results/mcd/cache altında önbelleğe alınır.
"""
import argparse
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from rppg.evaluation import METHOD_LIST, config_grid, evaluate, summary  # noqa: E402
from rppg.io_utils import gt_window_hr, iter_frames, load_mcd_item  # noqa: E402
from rppg.metrics import summarize  # noqa: E402
from rppg.pipeline import Config, estimate  # noqa: E402
from rppg.plotting import plot_bland_altman, plot_heatmap  # noqa: E402
from rppg.roi import FaceTracker  # noqa: E402
from rppg.signals import Traces, extract_traces  # noqa: E402

HF_REPO = "akramic/mcd_rppg"
HF_BASE = f"https://huggingface.co/datasets/{HF_REPO}/resolve/main/"
CAMERA_TR = {"FullHDwebcam": "webcam (önden)", "USBVideo": "USB kamera (sol)", "IriunWebcam": "telefon (sağ)"}
STEP_TR = {"before": "dinlenme", "after": "egzersiz sonrası"}

PROPOSED = Config("pos", ("forehead", "left_cheek", "right_cheek", "full"), "snr", "viterbi", True)
CLASSIC = Config("pos", ("full",), "mean", "argmax", False)


# ------------------------------------------------------------------ indirme
def _fetch(rel, root):
    import requests
    dst = os.path.join(root, rel)
    if os.path.exists(dst) and os.path.getsize(dst) > 0:
        return True
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with requests.get(HF_BASE + rel, stream=True, timeout=60) as r:
        if r.status_code != 200:
            return False
        with open(dst + ".part", "wb") as f:
            for chunk in r.iter_content(1 << 20):
                f.write(chunk)
    os.replace(dst + ".part", dst)
    return True


def _available_videos():
    """Hugging Face kopyasında gerçekten bulunan video dosyaları (sayfalı liste)."""
    import requests
    url = f"https://huggingface.co/api/datasets/{HF_REPO}/tree/main/video"
    out = set()
    while url:
        r = requests.get(url, timeout=60)
        r.raise_for_status()
        out |= {f["path"] for f in r.json()}
        url = r.links.get("next", {}).get("url")
    return out


def download(db, root, n_people, cameras, steps):
    avail = _available_videos()
    rows = db[db.video.isin(avail) & db.camera.isin(cameras) & db.step.isin(steps)]
    people = rows.patient_id.drop_duplicates().tolist()[:n_people]
    rows = rows[rows.patient_id.isin(people)]
    print(f"{len(people)} kişi, {len(rows)} video indiriliyor ({HF_REPO})...")
    for i, r in enumerate(rows.itertuples(), 1):
        ok = all(_fetch(rel, root) for rel in (r.ppg_sync, r.meta, r.video))
        print(f"  [{i}/{len(rows)}] {r.video} {'' if ok else '-> BULUNAMADI'}")


# ------------------------------------------------------------ değerlendirme
def _extract(args):
    root, row, cache_dir, resize = args
    name = os.path.splitext(os.path.basename(row["video"]))[0]
    path = os.path.join(cache_dir, name + ".npz")
    item = load_mcd_item(root, row["video"], row["meta"], row["ppg_sync"])
    if not os.path.exists(path):
        try:
            tr = extract_traces(iter_frames(item["video"], resize_width=resize), 30.0, FaceTracker())
        except RuntimeError as e:  # ör. yan açıda Haar yüz bulamadı
            return name, None, str(e)
        tr.save(path)
    return name, path, item


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="data/MCD")
    ap.add_argument("--out", default="results/mcd")
    ap.add_argument("--download", type=int, default=0, help="Hugging Face'ten indirilecek kişi sayısı")
    ap.add_argument("--cameras", default="FullHDwebcam,USBVideo,IriunWebcam")
    ap.add_argument("--steps", default="before,after")
    ap.add_argument("--methods", default=",".join(METHOD_LIST))
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    ap.add_argument("--resize", type=int, default=640)
    a = ap.parse_args()
    cameras, steps = a.cameras.split(","), a.steps.split(",")

    os.makedirs(a.root, exist_ok=True)
    db_path = os.path.join(a.root, "db.csv")
    if not os.path.exists(db_path) and not _fetch("db.csv", a.root):
        sys.exit("db.csv indirilemedi; internet bağlantısını kontrol edin.")
    db = pd.read_csv(db_path)
    if a.download:
        download(db, a.root, a.download, cameras, steps)

    have = db[db.camera.isin(cameras) & db.step.isin(steps)
              & db.video.map(lambda p: os.path.exists(os.path.join(a.root, p)))
              & db.ppg_sync.map(lambda p: os.path.exists(os.path.join(a.root, p)))
              & db.meta.map(lambda p: os.path.exists(os.path.join(a.root, p)))]
    if have.empty:
        sys.exit(f"'{a.root}' altında video yok. Önce: python scripts/evaluate_mcd.py --download 5")

    cache, figs = os.path.join(a.out, "cache"), os.path.join(a.out, "figures")
    os.makedirs(cache, exist_ok=True)
    os.makedirs(figs, exist_ok=True)

    t0 = time.time()
    print(f"[1/3] {len(have)} video ({have.patient_id.nunique()} kişi) için izler çıkarılıyor...")
    jobs = [(a.root, r._asdict(), cache, a.resize) for r in have[["video", "meta", "ppg_sync"]].itertuples(index=False)]
    with ProcessPoolExecutor(a.workers) as ex:
        items = list(ex.map(_extract, jobs))
    print(f"      {time.time() - t0:.0f} s")

    videos, skipped = [], []
    for (name, path, item), r in zip(items, have.itertuples()):
        if path is None:
            skipped.append(name)
            print(f"  ! {name} atlandı: {item}")
            continue
        tr = Traces.load(path)
        m = min(tr.n, len(item["timestamps"]))
        tr = tr.slice(0, m).resampled(item["timestamps"][:m], 30.0)
        videos.append({"name": name, "kişi": int(r.patient_id), "kamera": CAMERA_TR.get(r.camera, r.camera),
                       "durum": STEP_TR.get(r.step, r.step), "traces": tr, "gt": item["gt"]})

    print("[2/3] Konfigürasyonlar değerlendiriliyor...")
    df = evaluate(videos, config_grid(a.methods.split(",")))
    df.to_csv(os.path.join(a.out, "tum_sonuclar.csv"), index=False)
    summ = summary(df)
    summ.to_csv(os.path.join(a.out, "konfigurasyon_ozeti.csv"), index=False)

    print("[3/3] Tablolar ve şekiller...")
    lines = ["# MCD-rPPG Sonuçları", "",
             f"Kişi: {len({v['kişi'] for v in videos})}, video: {len(videos)} "
             f"(kaynak: Hugging Face `{HF_REPO}`, CC-BY-4.0). Pencere: 10 s. "
             "Referans: karelere hizalı parmak PPG'sinden pencere başına spektral tepe.", "",
             "> Not: kamera ve bakış açısı bu veri setinde birbirine bağlıdır "
             "(webcam önden, USB kamera soldan, telefon sağdan). Kamera farkı açı farkını da içerir.", "",
             *([f"Yüz bulunamadığı için atlanan videolar ({len(skipped)}): " + ", ".join(skipped), ""]
               if skipped else []),
             "## En iyi 20 konfigürasyon", "", summ.head(20).round(2).to_markdown(index=False), ""]

    # önerilen vs klasik: kamera x durum
    per = []
    for v in videos:
        for label, cfg in (("klasik", CLASSIC), ("önerilen", PROPOSED)):
            r = estimate(v["traces"], cfg)
            ref = gt_window_hr(v["gt"], r.centers, cfg.win_sec)
            per.append({"kamera": v["kamera"], "durum": v["durum"], "hat": label,
                        "ref_ort": float(np.mean(ref)), "est": r.hr, "ref": ref, **summarize(r.hr, ref)})
    per = pd.DataFrame(per)
    for hat in ("klasik", "önerilen"):
        pv = per[per.hat == hat].pivot_table(index="kamera", columns="durum", values="MAE", aggfunc="mean")
        plot_heatmap(pv, os.path.join(figs, f"kamera_durum_{'onerilen' if hat == 'önerilen' else hat}.png"), f"MCD-rPPG: kamera x durum MAE (POS, {hat})")
        lines += [f"## Kamera x durum — MAE (BPM), POS {hat} hat", "", pv.round(2).to_markdown(), ""]
    ref_hr = per[per.hat == "önerilen"].groupby("durum").ref_ort.mean().round(1)
    lines += ["Ortalama referans nabız: " + ", ".join(f"{k} {v} BPM" for k, v in ref_hr.items()), ""]

    pv = df[df.takip == "viterbi"].pivot_table(index="yöntem", columns="kamera", values="MAE", aggfunc="mean")
    plot_heatmap(pv, os.path.join(figs, "yontem_kamera_mae.png"), "MCD-rPPG: yöntem x kamera (Viterbi) MAE")
    lines += ["## Yöntem x kamera (Viterbi takip, tüm ROI setleri ortalaması)", "", pv.round(2).to_markdown(), ""]

    prop = per[per.hat == "önerilen"]
    plot_bland_altman(np.concatenate(prop.est.tolist()), np.concatenate(prop.ref.tolist()),
                      os.path.join(figs, "bland_altman.png"), "MCD-rPPG — önerilen yöntem")

    with open(os.path.join(a.out, "SONUCLAR.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("\n".join(lines))
    print(f"Toplam: {time.time() - t0:.0f} s -> {a.out}")


if __name__ == "__main__":
    main()
