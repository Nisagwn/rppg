#!/usr/bin/env python
"""
UBFC-rPPG veri seti üzerinde tam ablasyon değerlendirmesi.

Veri setini indirip (bkz. docs/03_veri_seti_indirme.md) şu yapıda açın:
    data/UBFC/DATASET_2/subject1/vid.avi
    data/UBFC/DATASET_2/subject1/ground_truth.txt
    ...

Kullanım:
    python scripts/evaluate_ubfc.py --root data/UBFC --out results/ubfc
    python scripts/evaluate_ubfc.py --root data/UBFC --max-subjects 5 --methods pos,chrom

İzler (ROI RGB ortalamaları) önbelleğe alınır; ikinci çalıştırmada video
yeniden işlenmez, yalnızca konfigürasyonlar değerlendirilir.
"""
import argparse
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from rppg.evaluation import METHOD_LIST, config_grid, evaluate, summary  # noqa: E402
from rppg.io_utils import find_ubfc_subjects, gt_window_hr, iter_frames, load_ubfc_gt, video_info  # noqa: E402
from rppg.pipeline import Config, estimate  # noqa: E402
from rppg.plotting import plot_bland_altman, plot_heatmap, plot_result  # noqa: E402
from rppg.roi import FaceTracker  # noqa: E402
from rppg.signals import Traces, extract_traces  # noqa: E402


def _extract(args):
    subj, root, cache_dir, resize = args
    name = os.path.relpath(subj, root).replace(os.sep, "_")
    path = os.path.join(cache_dir, name + ".npz")
    if not os.path.exists(path):
        vid = os.path.join(subj, "vid.avi")
        fps, *_ = video_info(vid)
        tr = extract_traces(iter_frames(vid, resize_width=resize), fps, FaceTracker())
        tr.save(path)
    return subj, name, path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--out", default="results/ubfc")
    ap.add_argument("--max-subjects", type=int)
    ap.add_argument("--methods", default=",".join(METHOD_LIST))
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    ap.add_argument("--resize", type=int, default=640)
    a = ap.parse_args()

    subjects = find_ubfc_subjects(a.root)
    if not subjects:
        sys.exit(f"'{a.root}' altında vid.avi + ground_truth.txt/gtdump.xmp içeren klasör bulunamadı.")
    if a.max_subjects:
        subjects = subjects[:a.max_subjects]
    os.makedirs(a.out, exist_ok=True)
    cache = os.path.join(a.out, "cache")
    figs = os.path.join(a.out, "figures")
    os.makedirs(cache, exist_ok=True)
    os.makedirs(figs, exist_ok=True)

    t0 = time.time()
    print(f"[1/3] {len(subjects)} denek için izler çıkarılıyor...")
    with ProcessPoolExecutor(a.workers) as ex:
        items = list(ex.map(_extract, [(s, a.root, cache, a.resize) for s in subjects]))
    print(f"      {time.time() - t0:.0f} s")

    videos = []
    for subj, name, path in items:
        videos.append({"name": name, "dataset": "DATASET_1" if "DATASET_1" in subj else "DATASET_2",
                       "traces": Traces.load(path), "gt": load_ubfc_gt(subj)})

    print("[2/3] Konfigürasyonlar değerlendiriliyor...")
    df = evaluate(videos, config_grid(a.methods.split(",")))
    df.to_csv(os.path.join(a.out, "tum_sonuclar.csv"), index=False)
    summ = summary(df)
    summ.to_csv(os.path.join(a.out, "konfigurasyon_ozeti.csv"), index=False)

    print("[3/3] Tablolar ve şekiller...")
    lines = ["# UBFC-rPPG Sonuçları", "", f"Denek sayısı: {len(videos)}", "",
             "## En iyi 20 konfigürasyon (pencere düzeyi, 10 s)", "",
             summ.head(20).round(2).to_markdown(index=False), ""]
    pv = df[df.takip == "viterbi"].pivot_table(index="yöntem", columns="roi", values="MAE", aggfunc="mean")
    plot_heatmap(pv, os.path.join(figs, "yontem_roi_mae.png"), "UBFC: yöntem x ROI (Viterbi) MAE")
    lines += ["## Yöntem x ROI (Viterbi takip)", "", pv.round(2).to_markdown(), ""]

    best = Config("pos", ("forehead", "left_cheek", "right_cheek", "full"), "snr", "viterbi", True)
    ests, refs = [], []
    for v in videos:
        r = estimate(v["traces"], best)
        ref = gt_window_hr(v["gt"], r.centers, best.win_sec)
        ests.append(r.hr)
        refs.append(ref)
    plot_bland_altman(np.concatenate(ests), np.concatenate(refs), os.path.join(figs, "bland_altman.png"),
                      "UBFC — önerilen yöntem")
    worst = int(np.argmax([np.mean(np.abs(e - r)) for e, r in zip(ests, refs)]))
    wr = estimate(videos[worst]["traces"], best)
    plot_result(wr, videos[worst]["traces"], refs[worst], os.path.join(figs, "en_kotu_denek.png"),
                f"En zor denek: {videos[worst]['name']}")
    with open(os.path.join(a.out, "SONUCLAR.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("\n".join(lines))
    print(f"Toplam: {time.time() - t0:.0f} s -> {a.out}")


if __name__ == "__main__":
    main()
