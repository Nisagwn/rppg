"""Derin öğrenme yardımcılarının (scripts/dl_common.py, scripts/dl_train.py) birim testleri.
PyTorch kurulu değilse atlanır; gerçek FactorizePhys modeli gerekmez (küçük sahte model kullanılır)."""
import os
import sys

import numpy as np
import pytest

torch = pytest.importorskip("torch")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from dl_common import CHUNK, chunk_starts, hr_from_bvp, predict_video  # noqa: E402
from dl_train import neg_pearson, spectral_kl  # noqa: E402

FS = 30.0


class EdgeModel(torch.nn.Module):
    """Yeşil kanal ortalaması; edge > 0 ise parça kenarlarına güçlü bozulma ekler."""

    def __init__(self, edge=0.0):
        super().__init__()
        self.edge = edge

    def forward(self, x):
        g = x[:, 1].mean((-1, -2))[:, :-1]
        t = torch.arange(CHUNK, dtype=torch.float32)
        ramp = torch.exp(-t / 8) + torch.exp(-(CHUNK - 1 - t) / 8)
        g = (g - g.mean(1, keepdim=True)) / (g.std(1, keepdim=True) + 1e-8)
        return (g + self.edge * 3 * ramp,)


def pulse_frames(hr=84.0, sec=40, seed=0):
    rng = np.random.default_rng(seed)
    t = np.arange(int(sec * FS)) / FS
    pulse = np.sin(2 * np.pi * hr / 60 * t)
    f = 120 + 3 * pulse[:, None, None, None] * np.array([0.3, 1, 0.5]) + rng.normal(0, 6, (len(t), 72, 72, 3))
    return np.clip(f, 0, 255).astype(np.uint8)


def test_chunk_starts_cover_video_and_end_aligned():
    for n, hop in [(160, 160), (500, 160), (500, 80), (1000, 37)]:
        s = chunk_starts(n, hop)
        assert s[0] == 0 and s[-1] + CHUNK == n
        assert all(b - a <= hop for a, b in zip(s, s[1:]))


def test_predict_video_short_returns_none():
    assert predict_video(EdgeModel(), pulse_frames(sec=3), torch.device("cpu")) is None


@pytest.mark.parametrize("kw", [{}, {"hop": 80}, {"hop": 80, "flip": True}])
def test_predict_video_recovers_hr(kw):
    y = predict_video(EdgeModel(), pulse_frames(84.0), torch.device("cpu"), **kw)
    assert y.shape == (40 * 30,) and np.isfinite(y).all()
    _, hr_a, _ = hr_from_bvp(y)
    assert np.abs(hr_a - 84.0).mean() < 1.0


def test_overlap_suppresses_chunk_edge_artifacts():
    frames = pulse_frames(84.0)
    t = np.arange(len(frames)) / FS
    pulse = np.sin(2 * np.pi * 84.0 / 60 * t)
    plain = predict_video(EdgeModel(1.0), frames, torch.device("cpu"))
    blended = predict_video(EdgeModel(1.0), frames, torch.device("cpu"), hop=80)
    assert np.corrcoef(blended, pulse)[0, 1] > np.corrcoef(plain, pulse)[0, 1] + 0.05


def test_spectral_kl_penalizes_wrong_frequency_not_sign():
    t = torch.arange(CHUNK) / FS
    lab = torch.sin(2 * np.pi * 1.4 * t)[None]
    harmonic = torch.sin(2 * np.pi * 2.8 * t)[None]
    assert spectral_kl(lab, lab).item() < 1e-4
    assert spectral_kl(-lab, lab).item() < 1e-4          # işaret Pearson'ın işi
    assert spectral_kl(harmonic, lab).item() > 5.0
    assert neg_pearson(harmonic, lab).item() < 1.1        # Pearson harmoniği ayırt etmiyor


def test_spectral_kl_gradient_finite():
    p = torch.randn(3, CHUNK, requires_grad=True)
    lab = torch.sin(2 * np.pi * 1.2 * torch.arange(CHUNK) / FS).repeat(3, 1)
    spectral_kl(p, lab).backward()
    assert torch.isfinite(p.grad).all()
