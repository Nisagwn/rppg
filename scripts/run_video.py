#!/usr/bin/env python
"""
Tek bir video dosyasından nabız ve solunum tahmini.

Örnekler:
    python scripts/run_video.py --video data/ornek.avi
    python scripts/run_video.py --video vid.avi --gt ground_truth.txt --method chrom
    python scripts/run_video.py --video kayit.mkv --bbox 100 40 120 130   # Haar bulamazsa
    python scripts/run_video.py --recording data/kayitlar/nisa_isik_01    # record_session çıktısı
"""
import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from rppg.io_utils import gt_window_hr, iter_frames, load_recording, load_ubfc_gt, video_info  # noqa: E402
from rppg.metrics import summarize  # noqa: E402
from rppg.pipeline import Config, estimate  # noqa: E402
from rppg.plotting import plot_result, plot_roi_weights  # noqa: E402
from rppg.respiration import respiration_rate  # noqa: E402
from rppg.roi import FaceTracker  # noqa: E402
from rppg.signals import extract_traces  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description="Videodan temassız nabız/solunum ölçümü")
    ap.add_argument("--video")
    ap.add_argument("--recording", help="record_session.py ile kaydedilmiş klasör")
    ap.add_argument("--gt", help="UBFC ground_truth.txt / gtdump.xmp (veya bulunduğu klasör)")
    ap.add_argument("--method", default="pos", choices=["green", "ica", "chrom", "pos", "lgi"])
    ap.add_argument("--rois", default="forehead,left_cheek,right_cheek,full")
    ap.add_argument("--fusion", default="snr", choices=["snr", "mean"])
    ap.add_argument("--tracker", default="viterbi", choices=["viterbi", "argmax"])
    ap.add_argument("--win", type=float, default=10.0)
    ap.add_argument("--bbox", type=float, nargs=4, metavar=("X", "Y", "W", "H"))
    ap.add_argument("--max-seconds", type=float)
    ap.add_argument("--resize", type=int, default=640, help="genişlik üst sınırı (hız için)")
    ap.add_argument("--out", default="results/run")
    a = ap.parse_args()

    timestamps, gt = None, None
    if a.recording:
        rec = load_recording(a.recording)
        a.video, timestamps, gt = rec["video"], rec["timestamps"], rec["gt"]
    if not a.video:
        ap.error("--video veya --recording gerekli")
    fps, n, w, h = video_info(a.video)
    print(f"Video: {a.video}  {w}x{h}  {fps:.2f} fps  {n} kare")
    max_frames = int(a.max_seconds * fps) if a.max_seconds else None
    scale = a.resize / w if (a.resize and w > a.resize) else 1.0
    init = tuple(v * scale for v in a.bbox) if a.bbox else None
    tracker = FaceTracker(use_haar=a.bbox is None, initial_bbox=init)
    print("İzler çıkarılıyor...")
    tr = extract_traces(iter_frames(a.video, max_frames, a.resize), fps, tracker, progress=True)
    if timestamps is not None:
        tr = tr.resampled(timestamps[:tr.n], 30.0)
        print(f"Zaman damgalarına göre 30 Hz'e yeniden örneklendi (gerçek ortalama fps: "
              f"{(len(timestamps) - 1) / (timestamps[-1] - timestamps[0]):.2f})")

    cfg = Config(a.method, tuple(a.rois.split(",")), a.fusion, a.tracker, a.tracker == "viterbi", a.win)
    r = estimate(tr, cfg)
    _, rr_series, rr, _ = respiration_rate(tr.chest_dy, tr.fps, tr.face_cy)

    if a.gt:
        gdir = a.gt if os.path.isdir(a.gt) else os.path.dirname(a.gt)
        gt = load_ubfc_gt(gdir)
    ref = gt_window_hr(gt, r.centers, cfg.win_sec) if gt is not None else None

    os.makedirs(a.out, exist_ok=True)
    base = os.path.splitext(os.path.basename(a.video))[0]
    plot_result(r, tr, ref, os.path.join(a.out, f"{base}_sonuc.png"), f"{base} — {cfg.name}")
    plot_roi_weights(r, os.path.join(a.out, f"{base}_roi_agirlik.png"))
    out = {"video": a.video, "config": cfg.name, "hr_ortalama_bpm": r.hr_mean,
           "hr_seri": {"t": r.centers.round(2).tolist(), "bpm": r.hr.round(2).tolist()},
           "solunum_nefes_dk": rr, "ortalama_snr_db": float(np.mean(r.snr_db))}
    if ref is not None:
        out["metrikler"] = summarize(r.hr, ref)
    json.dump(out, open(os.path.join(a.out, f"{base}_sonuc.json"), "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"\nOrtalama nabız : {r.hr_mean:.1f} BPM")
    print(f"Solunum hızı   : {rr:.1f} nefes/dk")
    print(f"Ortalama SNR   : {np.mean(r.snr_db):.1f} dB")
    if ref is not None:
        print("Metrikler      :", {k: round(v, 2) for k, v in out["metrikler"].items()})
    print(f"Çıktılar       : {a.out}")


if __name__ == "__main__":
    main()
