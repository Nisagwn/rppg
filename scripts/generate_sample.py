#!/usr/bin/env python
"""
Kamera/veri seti olmadan denemek için örnek sentetik videolar üretir.

    python scripts/generate_sample.py                  # data/ornek_*.avi
    python scripts/generate_sample.py --scenario hard --duration 30
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from rppg.synthetic import SCENARIOS, make_scenario, write_video  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", default="all", help=f"all | {', '.join(SCENARIOS)}")
    ap.add_argument("--duration", type=float, default=30)
    ap.add_argument("--out", default="data")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    names = ["ideal", "hard"] if a.scenario == "all" else [a.scenario]
    for n in names:
        v = make_scenario(n, seed=0, duration=a.duration)
        path = os.path.join(a.out, f"ornek_{n}.avi")
        write_video(v, path)
        info = {"senaryo": n, "bbox": [round(x, 1) for x in v.face_bbox()],
                "gercek_hr_ortalama": float(v.hr.mean()), "gercek_solunum": v.cfg.rr_bpm}
        json.dump(info, open(path.replace(".avi", ".json"), "w"), indent=2)
        print(f"{path}  (gerçek HR ort. {info['gercek_hr_ortalama']:.1f} BPM, "
              f"solunum {info['gercek_solunum']:.1f}/dk, bbox {info['bbox']})")
    print(f"\nDeneme: python scripts/run_video.py --video {path} --bbox "
          + " ".join(str(x) for x in info["bbox"]))


if __name__ == "__main__":
    main()
