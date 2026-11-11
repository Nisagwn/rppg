#!/usr/bin/env python
"""ONNX/PyTorch eşdeğerliğini sabit tohum ve gerçek video parçalarında doğrula."""
import argparse
import hashlib
import json
from pathlib import Path
import time

import numpy as np
import onnxruntime as ort
import torch

from dl_common import build_model, to_input
from rppg.filtering import preprocess_bvp
from rppg.hr import hr_fft


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--checkpoint", default="results/derin_ogrenme/pure_weiqian_s1_seed42/best.pth")
    ap.add_argument("--onnx", default="mobile/model/mmrphys_pure_s1.onnx")
    ap.add_argument("--samples", nargs="+", default=["data/dl/test/mcd_1020_FullHDwebcam_before.npy",
                                                    "data/dl/test_kamera/mcd_1020_IriunWebcam_before.npy"])
    ap.add_argument("--out", default="results/derin_ogrenme/pure_weiqian_s1_seed42/onnx_dogrulama.json")
    a = ap.parse_args()
    torch.set_num_threads(4)
    torch.manual_seed(42)
    model = build_model(torch.device("cpu"), a.checkpoint).eval()
    options = ort.SessionOptions()
    options.intra_op_num_threads = 4
    session = ort.InferenceSession(a.onnx, options, providers=["CPUExecutionProvider"])
    tests = [("random_seed42", torch.rand(1, 3, 161, 72, 72) * 255)]
    for filename in a.samples:
        frames = np.load(filename, mmap_mode="r")
        for start in (0, (len(frames) - 160) // 2, len(frames) - 160):
            tests.append((f"{Path(filename).name}@{start}", to_input(np.array(frames[None, start:start + 160]), "cpu")))
    rows = []
    with torch.no_grad():
        for name, x in tests:
            ref = model(x)[0].numpy()
            begin = time.perf_counter()
            got = session.run(None, {"video": x.numpy()})[0]
            ms = (time.perf_counter() - begin) * 1000
            assert ref.shape == got.shape == (1, 160)
            assert np.isfinite(got).all()
            delta = ref - got
            relative = float(np.linalg.norm(delta) / max(np.linalg.norm(ref), 1e-12))
            corr = float(np.corrcoef(ref.ravel(), got.ravel())[0, 1])
            hr_delta = abs(hr_fft(preprocess_bvp(ref.ravel(), 30), 30)
                           - hr_fft(preprocess_bvp(got.ravel(), 30), 30))
            row = {"sample": name, "max_abs": float(np.abs(delta).max()), "relative_l2": relative,
                   "correlation": corr, "hr_difference_bpm": hr_delta, "ort_cpu_ms": ms}
            rows.append(row)
            # Float32 normalizasyonları küçük farkları büyütebilir; %0.1 bağıl hata sınırı
            # yanında dalga korelasyonu ve aşağı akıştaki nabız değişimi de kontrol edilir.
            assert relative < 1e-3 and corr > 0.99999 and hr_delta < 0.1, row
    report = {"checkpoint": a.checkpoint, "checkpoint_sha256": hashlib.sha256(Path(a.checkpoint).read_bytes()).hexdigest(),
              "onnx": a.onnx, "onnx_sha256": hashlib.sha256(Path(a.onnx).read_bytes()).hexdigest(),
              "onnx_bytes": Path(a.onnx).stat().st_size, "torch": torch.__version__, "ort": ort.__version__,
              "provider": "CPUExecutionProvider", "threads": 4, "samples": rows, "passed": True,
              "thresholds": {"relative_l2_below": 0.001, "correlation_above": 0.99999, "hr_difference_below_bpm": 0.1},
              "note": "Masaüstü CPU; ölçülen süre ilk çağrı ısınmasını da içerebilir, telefon hızı değildir."}
    Path(a.out).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"ONNX: {len(rows)} girdi geçti; en büyük fark {max(r['max_abs'] for r in rows):.3g}")


if __name__ == "__main__":
    main()
