"""Uçtan uca nabız tahmini: Traces + Config -> Result."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional, Sequence

import numpy as np

from .filtering import preprocess_bvp
from .fusion import motion_confidence, snr_fused_spectrogram
from .hr import BPM_GRID, argmax_track, spectrogram, viterbi_track, window_snr_from_spectrum
from .methods import apply_method
from .signals import Traces


@dataclass
class Config:
    method: str = "pos"
    rois: Sequence[str] = ("forehead", "left_cheek", "right_cheek", "full")
    fusion: str = "snr"          # "snr" (özgün) | "mean" (klasik RGB ortalaması)
    tracker: str = "viterbi"     # "viterbi" (özgün) | "argmax" (klasik)
    motion_aware: bool = True    # (özgün) hareket farkında güven
    win_sec: float = 10.0
    step_sec: float = 1.0
    max_rate_bpm_s: float = 4.0
    gamma: float = 2.0

    @property
    def name(self) -> str:
        r = "+".join(self.rois)
        ma = "+ma" if (self.motion_aware and self.tracker == "viterbi") else ""
        return f"{self.method}|{r}|{self.fusion}|{self.tracker}{ma}"


@dataclass
class Result:
    config: Config
    centers: np.ndarray
    hr: np.ndarray
    spec: np.ndarray
    grid: np.ndarray
    bvp: np.ndarray
    bvps: Dict[str, np.ndarray]
    conf: np.ndarray
    snr_db: np.ndarray
    roi_weights: Optional[np.ndarray] = None
    roi_names: list = field(default_factory=list)

    @property
    def hr_mean(self) -> float:
        return float(np.mean(self.hr))


def estimate(traces: Traces, cfg: Config = Config()) -> Result:
    fs = traces.fps
    rois = [r for r in cfg.rois if r in traces.rgb]
    if not rois:
        raise ValueError(f"İstenen ROI'ler izlerde yok: {cfg.rois}")

    bvps = {r: preprocess_bvp(apply_method(cfg.method, traces.rgb[r], fs), fs) for r in rois}
    weights, names = None, rois
    if cfg.fusion == "mean" or len(rois) == 1:
        rgb = np.mean([traces.rgb[r] for r in rois], axis=0)
        bvp = preprocess_bvp(apply_method(cfg.method, rgb, fs), fs)
        centers, S = spectrogram(bvp, fs, cfg.win_sec, cfg.step_sec)
    elif cfg.fusion == "snr":
        centers, S, weights, names, _ = snr_fused_spectrogram(bvps, fs, cfg.win_sec, cfg.step_sec, cfg.gamma)
        best = names[int(np.argmax(weights.mean(axis=0)))]
        bvp = bvps[best]
    else:
        raise ValueError(f"Bilinmeyen füzyon: {cfg.fusion}")

    if cfg.motion_aware and cfg.tracker == "viterbi":
        conf = motion_confidence(traces.motion, fs, cfg.win_sec, cfg.step_sec)
        conf = conf[:len(S)]
    else:
        conf = np.ones(len(S))

    if cfg.tracker == "viterbi":
        hr = viterbi_track(S, BPM_GRID, cfg.step_sec, cfg.max_rate_bpm_s, conf)
    elif cfg.tracker == "argmax":
        hr = argmax_track(S, BPM_GRID)
    else:
        raise ValueError(f"Bilinmeyen takipçi: {cfg.tracker}")

    snr = np.array([window_snr_from_spectrum(BPM_GRID, S[t], hr[t]) for t in range(len(hr))])
    return Result(cfg, centers, hr, S, BPM_GRID, bvp, bvps, conf, snr, weights, list(names))
