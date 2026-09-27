#!/usr/bin/env python
"""
Eulerian Video Magnification ile nabzı görünür kılan video üretir
(orijinal | büyütülmüş yan yana).

    python scripts/make_evm_video.py --video data/ornek.avi --out results/evm.mp4
    python scripts/make_evm_video.py --video yuz.avi --alpha 100 --lo 0.8 --hi 2.0 --seconds 15
"""
import argparse
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from rppg.evm import magnify_color  # noqa: E402
from rppg.io_utils import iter_frames, video_info  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--out", default="results/evm.mp4")
    ap.add_argument("--alpha", type=float, default=80)
    ap.add_argument("--lo", type=float, default=0.8)
    ap.add_argument("--hi", type=float, default=2.0)
    ap.add_argument("--level", type=int, default=4)
    ap.add_argument("--seconds", type=float, default=15, help="bellek için süre sınırı")
    ap.add_argument("--resize", type=int, default=480)
    a = ap.parse_args()
    fps, *_ = video_info(a.video)
    frames = list(iter_frames(a.video, int(a.seconds * fps), a.resize))
    print(f"{len(frames)} kare, fps={fps:.1f}; büyütülüyor (α={a.alpha}, {a.lo}-{a.hi} Hz)...")
    mag = magnify_color(frames, fps, a.lo, a.hi, a.alpha, a.level)
    H, W = frames[0].shape[:2]
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    w = cv2.VideoWriter(a.out, cv2.VideoWriter_fourcc(*"mp4v"), fps, (2 * W, H))
    for f, m in zip(frames, mag):
        cv2.putText(f, "orijinal", (8, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
        cv2.putText(m, f"EVM x{a.alpha:.0f}", (8, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
        w.write(np.hstack([f, m]))
    w.release()
    print("Kaydedildi:", a.out)


if __name__ == "__main__":
    main()
