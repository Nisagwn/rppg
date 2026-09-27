#!/usr/bin/env python
"""
Sentetik benchmark: her senaryo x tohum için video üretir, izleri çıkarır,
tüm yöntem/ROI/füzyon/takip konfigürasyonlarını değerlendirir; tablolar ve
şekiller üretir.

Kullanım:
    python scripts/synthetic_benchmark.py --seeds 3 --duration 60 --out results/synthetic
    python scripts/synthetic_benchmark.py --quick        # hızlı deneme
"""
import argparse
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from rppg.evaluation import METHOD_LIST, ROI_SETS, config_grid, evaluate, summary  # noqa: E402
from rppg.io_utils import gt_window_hr  # noqa: E402
from rppg.pipeline import Config, estimate  # noqa: E402
from rppg.plotting import plot_bars, plot_bland_altman, plot_heatmap, plot_result, plot_roi_weights  # noqa: E402
from rppg.respiration import respiration_rate  # noqa: E402
from rppg.roi import FaceTracker  # noqa: E402
from rppg.signals import Traces, extract_traces  # noqa: E402
from rppg.synthetic import SCENARIO_NAMES_TR, SCENARIOS, make_scenario, write_video  # noqa: E402


def _job(args):
    scen, seed, duration, cache_dir = args
    path = os.path.join(cache_dir, f"{scen}_s{seed}.npz")
    v = make_scenario(scen, seed=seed, duration=duration)
    gt = v.ground_truth()
    if os.path.exists(path):
        tr = Traces.load(path)
    else:
        tr = extract_traces(v.frames(), v.cfg.fps, FaceTracker(use_haar=False, initial_bbox=v.face_bbox()))
        tr.save(path)
    return scen, seed, tr, gt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--duration", type=float, default=60.0)
    ap.add_argument("--out", default="results/synthetic")
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    ap.add_argument("--quick", action="store_true", help="1 tohum, 30 s, az konfigürasyon")
    ap.add_argument("--save-example-video", action="store_true")
    a = ap.parse_args()
    if a.quick:
        a.seeds, a.duration = 1, 30.0
    os.makedirs(a.out, exist_ok=True)
    fig_dir = os.path.join(a.out, "figures")
    cache = os.path.join(a.out, "cache")
    os.makedirs(fig_dir, exist_ok=True)
    os.makedirs(cache, exist_ok=True)

    scen_list = list(SCENARIOS.keys())
    jobs = [(s, k, a.duration, cache) for s in scen_list for k in range(a.seeds)]
    t0 = time.time()
    print(f"[1/4] {len(jobs)} sentetik video üretiliyor ve izler çıkarılıyor ({a.workers} işçi)...")
    with ProcessPoolExecutor(a.workers) as ex:
        res = list(ex.map(_job, jobs))
    print(f"      bitti: {time.time() - t0:.1f} s")
    videos = [{"name": f"{s}_s{k}", "senaryo": s, "traces": tr, "gt": gt} for s, k, tr, gt in res]

    print("[2/4] Konfigürasyonlar değerlendiriliyor...")
    methods = ["green", "chrom", "pos"] if a.quick else METHOD_LIST
    configs = config_grid(methods)
    df = evaluate(videos, configs)
    df.to_csv(os.path.join(a.out, "tum_sonuclar.csv"), index=False)
    print(f"      {len(df)} satır, {time.time() - t0:.1f} s")

    print("[3/4] Özet tablolar...")
    lines = ["# Sentetik Benchmark Sonuçları", "",
             f"- Senaryo sayısı: {len(scen_list)}, tohum: {a.seeds}, video süresi: {a.duration:.0f} s",
             "- Pencere: 10 s, adım: 1 s. Metrikler pencere düzeyinde, video ve tohumlar üzerinden ortalama.", ""]

    # (A) Klasik referans: yöntem x senaryo (tüm yüz, argmax)
    base = df[(df.roi == "tüm_yüz") & (df.takip == "argmax")]
    piv = base.pivot_table(index="yöntem", columns="senaryo", values="MAE", aggfunc="mean")[scen_list]
    piv.columns = [SCENARIO_NAMES_TR[c] for c in piv.columns]
    piv.index = [i.upper() for i in piv.index]
    plot_heatmap(piv, os.path.join(fig_dir, "A_yontem_senaryo_mae.png"),
                 "Klasik yöntemler: senaryo bazında MAE (tüm yüz ROI, argmax)", vmax=min(40, np.nanmax(piv.values)))
    lines += ["## A. Klasik yöntemler — senaryo bazında MAE (BPM), tüm yüz ROI + argmax", "",
              piv.round(2).to_markdown(), ""]

    # (B) Özgün katkıların ablasyonu (POS ile)
    pos = df[df.yöntem == "pos"]
    variants = [
        ("Tüm yüz + argmax (klasik)", (pos.roi == "tüm_yüz") & (pos.takip == "argmax")),
        ("Alın + argmax", (pos.roi == "alın") & (pos.takip == "argmax")),
        ("3 ROI ortalama + argmax", (pos.roi == "alın+yanaklar") & (pos.füzyon == "mean") & (pos.takip == "argmax")),
        ("3 ROI SNR füzyon + argmax", (pos.roi == "alın+yanaklar") & (pos.füzyon == "snr") & (pos.takip == "argmax")),
        ("3 ROI ortalama + Viterbi", (pos.roi == "alın+yanaklar") & (pos.füzyon == "mean") & (pos.takip == "viterbi")),
        ("3 ROI SNR füzyon + Viterbi", (pos.roi == "alın+yanaklar") & (pos.füzyon == "snr") & (pos.takip == "viterbi")),
        ("Tüm yüz + Viterbi", (pos.roi == "tüm_yüz") & (pos.takip == "viterbi")),
        ("4 bölge SNR füzyon + argmax", (pos.roi == "4_bölge") & (pos.füzyon == "snr") & (pos.takip == "argmax")),
        ("4 bölge SNR füzyon + Viterbi (önerilen)", (pos.roi == "4_bölge") & (pos.füzyon == "snr") & (pos.takip == "viterbi")),
    ]
    abl = pd.DataFrame({name: pos[m].groupby("senaryo")["MAE"].mean() for name, m in variants}).T[scen_list]
    abl.columns = [SCENARIO_NAMES_TR[c] for c in abl.columns]
    abl["ORTALAMA"] = abl.mean(axis=1)
    plot_heatmap(abl, os.path.join(fig_dir, "B_ablasyon_pos.png"),
                 "Ablasyon (POS): ROI, füzyon ve takip seçimlerinin etkisi", vmax=min(30, np.nanmax(abl.values)))
    plot_bars([n.replace(" (önerilen)", "*") for n in abl.index], abl["ORTALAMA"].values,
              os.path.join(fig_dir, "B2_ablasyon_ortalama.png"),
              "Ablasyon: tüm senaryolar ortalaması MAE (POS)", highlight=len(abl) - 1)
    lines += ["## B. Ablasyon — POS yöntemiyle ROI / füzyon / takip (MAE, BPM)", "",
              abl.round(2).to_markdown(), ""]

    # (C) En iyi konfigürasyonlar (genel)
    summ = summary(df)
    summ.to_csv(os.path.join(a.out, "konfigurasyon_ozeti.csv"), index=False)
    lines += ["## C. Tüm konfigürasyonlar içinde en iyi 15 (ortalama MAE)", "",
              summ.head(15).round(2).to_markdown(index=False), ""]

    # (D) Her yöntem için önerilen vs klasik
    comp = []
    for m in methods:
        dm = df[df.yöntem == m]
        klasik = dm[(dm.roi == "tüm_yüz") & (dm.takip == "argmax")]["MAE"].mean()
        oner = dm[(dm.roi == "4_bölge") & (dm.füzyon == "snr") & (dm.takip == "viterbi")]["MAE"].mean()
        comp.append({"yöntem": m.upper(), "klasik MAE": klasik, "önerilen MAE": oner,
                     "iyileşme %": 100 * (klasik - oner) / klasik if klasik > 0 else 0})
    comp = pd.DataFrame(comp)
    lines += ["## D. Her yöntem için: klasik (tüm yüz+argmax) vs önerilen (4 bölge SNR füzyon + Viterbi)", "",
              comp.round(2).to_markdown(index=False), ""]

    print("[4/4] Örnek şekiller ve solunum...")
    best_cfg = Config("pos", ("forehead", "left_cheek", "right_cheek", "full"), "snr", "viterbi", True)
    base_cfg = Config("pos", ("full",), "mean", "argmax", False)
    ests, refs = [], []
    for v in videos:
        r = estimate(v["traces"], best_cfg)
        ref = gt_window_hr(v["gt"], r.centers, best_cfg.win_sec)
        ests.append(r.hr)
        refs.append(ref)
        if v["name"] in ("hard_s0", "local_flicker_s0", "occlusion_s0"):
            plot_result(r, v["traces"], ref, os.path.join(fig_dir, f"E_ornek_{v['name']}.png"),
                        f"Önerilen yöntem — senaryo: {SCENARIO_NAMES_TR[v['senaryo']]}")
            plot_roi_weights(r, os.path.join(fig_dir, f"F_roi_agirlik_{v['name']}.png"),
                             f"ROI ağırlıkları — {SCENARIO_NAMES_TR[v['senaryo']]}")
            rb = estimate(v["traces"], base_cfg)
            plot_result(rb, v["traces"], ref, os.path.join(fig_dir, f"E_klasik_{v['name']}.png"),
                        f"Klasik (POS, tüm yüz, argmax) — senaryo: {SCENARIO_NAMES_TR[v['senaryo']]}")
    plot_bland_altman(np.concatenate(ests), np.concatenate(refs), os.path.join(fig_dir, "G_bland_altman_onerilen.png"),
                      "Bland-Altman — önerilen yöntem, tüm sentetik videolar")

    rr_rows = []
    for v in videos:
        _, _, rr, _ = respiration_rate(v["traces"].chest_dy, v["traces"].fps, v["traces"].face_cy)
        rr_rows.append({"senaryo": v["senaryo"], "gerçek": v["gt"]["rr_bpm"], "tahmin": rr,
                        "hata": abs(rr - v["gt"]["rr_bpm"])})
    rr_df = pd.DataFrame(rr_rows)
    rr_s = rr_df.groupby("senaryo")["hata"].mean().reindex(scen_list)
    rr_s.index = [SCENARIO_NAMES_TR[i] for i in rr_s.index]
    lines += ["## H. Solunum hızı mutlak hatası (nefes/dk)", "",
              rr_s.round(2).to_frame("MAE").to_markdown(), "",
              f"Genel solunum MAE: **{rr_df['hata'].mean():.2f} nefes/dk**", ""]

    with open(os.path.join(a.out, "SONUCLAR.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    json.dump({"seeds": a.seeds, "duration": a.duration, "n_videos": len(videos),
               "elapsed_s": time.time() - t0}, open(os.path.join(a.out, "calisma_bilgisi.json"), "w"))

    if a.save_example_video:
        v = make_scenario("hard", seed=0, duration=20)
        write_video(v, os.path.join(a.out, "ornek_sentetik_hard.avi"))
    print("\n".join(lines))
    print(f"\nToplam süre: {time.time() - t0:.1f} s  ->  {a.out}")


if __name__ == "__main__":
    main()
