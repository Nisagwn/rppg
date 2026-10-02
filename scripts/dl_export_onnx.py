#!/usr/bin/env python
"""
Eğitilmiş FactorizePhys modelini mobil uygulama için ONNX'e çevirir ve PyTorch çıktısıyla karşılaştırır.

    python scripts/dl_export_onnx.py                                   # Kaggle modeli -> mobile/model/factorizephys.onnx
    python scripts/dl_export_onnx.py --model results/derin_ogrenme/egitim/best.pth

Girdi [1, 3, 161, 72, 72] float32 (0–255 ham RGB, 30 fps, son kare tekrarlı), çıktı [1, 160] nabız dalgası.
ONNX'in TorchScript dışa aktarıcısı aten::diff'i desteklemediği için dışa aktarma sırasında torch.diff
matematiksel eşdeğeri olan dilimleme farkıyla (x[1:] - x[:-1]) değiştirilir.
"""
import argparse
import os

import numpy as np
import torch

from dl_common import ROOT, build_model


def _diff_slices(x, n=1, dim=-1, prepend=None, append=None):
    assert n == 1 and prepend is None and append is None
    L = x.shape[dim]
    return x.narrow(dim, 1, L - 1) - x.narrow(dim, 0, L - 1)


class BvpOnly(torch.nn.Module):
    def __init__(self, m):
        super().__init__()
        self.m = m

    def forward(self, x):
        return self.m(x)[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=os.path.join(ROOT, "results/derin_ogrenme/kaggle/cikti/best.pth"))
    ap.add_argument("--out", default=os.path.join(ROOT, "mobile/model/factorizephys.onnx"))
    a = ap.parse_args()

    w = BvpOnly(build_model(torch.device("cpu"), a.model)).eval()
    x = torch.rand(1, 3, 161, 72, 72) * 255
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    orig = torch.diff
    torch.diff = _diff_slices
    try:
        torch.onnx.export(w, (x,), a.out, input_names=["video"], output_names=["bvp"], opset_version=17, dynamo=False)
    finally:
        torch.diff = orig
    print(f"{a.out}: {os.path.getsize(a.out) / 1024:.0f} KB")

    import onnxruntime as ort
    s = ort.InferenceSession(a.out, providers=["CPUExecutionProvider"])
    with torch.no_grad():
        ref = w(x).numpy()
    got = s.run(None, {"video": x.numpy()})[0]
    print(f"PyTorch ile en büyük fark {np.abs(ref - got).max():.2e}, korelasyon {np.corrcoef(ref.ravel(), got.ravel())[0, 1]:.6f}")


if __name__ == "__main__":
    main()
