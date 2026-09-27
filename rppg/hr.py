"""
Frekans domeninde nabız (HR) tahmini.

* Hann pencereli, sıfır dolgulu periyodogram -> 0.25 BPM çözünürlük
* SNR (de Haan & Jeanne 2013): temel frekans ±6 BPM ve 1. harmonik ±12 BPM
  içindeki güç / bandın geri kalanındaki güç (dB)
* Kayan pencere spektrogramı (varsayılan 10 s pencere, 1 s adım)
* Viterbi takibi: Spektrogram üzerinde, ardışık pencereler arasında
  fizyolojik olarak makul HR değişimini (Gauss geçiş olasılığı) zorlayan
  en olası yol. Tek pencerelik hareket kaynaklı sahte tepeleri yok sayar.
"""
from __future__ import annotations

from typing import Optional, Tuple

import numpy as np
from scipy import signal as sps

BPM_GRID = np.arange(42.0, 210.0 + 1e-9, 0.5)   # 0.7–3.5 Hz


def spectrum_bpm(x: np.ndarray, fs: float, grid: np.ndarray = BPM_GRID) -> np.ndarray:
    """Sinyalin güç spektrumunu BPM ızgarasına örnekler (toplamı 1)."""
    x = np.asarray(x, dtype=float)
    x = x - x.mean()
    nfft = int(max(len(x), fs * 60 * 4))  # 0.25 BPM ham çözünürlük
    f, p = sps.periodogram(x, fs=fs, window="hann", nfft=nfft, detrend=False)
    pg = np.interp(grid / 60.0, f, p)
    s = pg.sum()
    return pg / s if s > 0 else np.full_like(grid, 1.0 / len(grid))


def peak_bpm(grid: np.ndarray, p: np.ndarray) -> float:
    """Parabolik enterpolasyonla alt-bin tepe konumu."""
    i = int(np.argmax(p))
    if 0 < i < len(p) - 1:
        a, b, c = p[i - 1], p[i], p[i + 1]
        d = a - 2 * b + c
        if abs(d) > 1e-15:
            off = 0.5 * (a - c) / d
            return float(grid[i] + off * (grid[1] - grid[0]))
    return float(grid[i])


def hr_fft(x: np.ndarray, fs: float) -> float:
    return peak_bpm(BPM_GRID, spectrum_bpm(x, fs))


SNR_GRID = np.arange(30.0, 240.0 + 1e-9, 0.5)


def snr_db(x: np.ndarray, fs: float, hr: Optional[float] = None) -> float:
    p = spectrum_bpm(x, fs, SNR_GRID)
    if hr is None:
        m = (SNR_GRID >= BPM_GRID[0]) & (SNR_GRID <= BPM_GRID[-1])
        hr = SNR_GRID[m][np.argmax(p[m])]
    sig = (np.abs(SNR_GRID - hr) <= 6) | (np.abs(SNR_GRID - 2 * hr) <= 12)
    s, n = p[sig].sum(), p[~sig].sum()
    return float(10 * np.log10((s + 1e-12) / (n + 1e-12)))


def window_snr_from_spectrum(grid: np.ndarray, p: np.ndarray, hr: float) -> float:
    """Izgara spektrumundan hızlı SNR (yalnızca temel frekans; harmonik ızgaradaysa o da)."""
    sig = (np.abs(grid - hr) <= 6) | (np.abs(grid - 2 * hr) <= 12)
    s, n = p[sig].sum(), p[~sig].sum()
    return float(10 * np.log10((s + 1e-12) / (n + 1e-12)))


def window_starts(n: int, fs: float, win_sec: float, step_sec: float):
    L = int(round(win_sec * fs))
    S = max(1, int(round(step_sec * fs)))
    if n < L:
        return [0], L, np.array([n / 2.0 / fs])
    starts = list(range(0, n - L + 1, S))
    centers = np.array([(s + L / 2.0) / fs for s in starts])
    return starts, L, centers


def spectrogram(x: np.ndarray, fs: float, win_sec: float = 10.0, step_sec: float = 1.0,
                grid: np.ndarray = BPM_GRID) -> Tuple[np.ndarray, np.ndarray]:
    starts, L, centers = window_starts(len(x), fs, win_sec, step_sec)
    S = np.stack([spectrum_bpm(x[s:s + L], fs, grid) for s in starts])
    return centers, S


def argmax_track(S: np.ndarray, grid: np.ndarray = BPM_GRID) -> np.ndarray:
    return np.array([peak_bpm(grid, row) for row in S])


def viterbi_track(S: np.ndarray, grid: np.ndarray = BPM_GRID, step_sec: float = 1.0,
                  max_rate_bpm_s: float = 4.0, conf: Optional[np.ndarray] = None) -> np.ndarray:
    """
    S     : (T, F) satır-normalize spektrogram (olasılık gibi yorumlanır)
    conf  : (T,) pencere güveni [0,1]. Düşük güvenli pencerede gözlem
            olasılığı düzleşir (log p * conf) ve takip önceki eğilimi sürdürür.
    Geçiş: log N(Δbpm; 0, σ²),  σ = max(1.5, max_rate * step)
    """
    T, F = S.shape
    if conf is None:
        conf = np.ones(T)
    logE = np.log(S / (S.max(axis=1, keepdims=True) + 1e-15) + 1e-6) * conf[:, None]
    sigma = max(1.5, max_rate_bpm_s * step_sec)
    d = grid[:, None] - grid[None, :]
    logA = -0.5 * (d / sigma) ** 2           # (F_prev, F_next)
    dp = logE[0].copy()
    back = np.zeros((T, F), dtype=np.int32)
    for t in range(1, T):
        cand = dp[:, None] + logA            # (F_prev, F_next)
        back[t] = np.argmax(cand, axis=0)
        dp = cand[back[t], np.arange(F)] + logE[t]
    path = np.zeros(T, dtype=np.int32)
    path[-1] = int(np.argmax(dp))
    for t in range(T - 1, 0, -1):
        path[t - 1] = back[t, path[t]]
    # yol üzerinde yerel parabolik iyileştirme
    out = np.empty(T)
    for t in range(T):
        i = path[t]
        lo, hi = max(0, i - 3), min(F, i + 4)
        j = lo + int(np.argmax(S[t, lo:hi]))
        out[t] = peak_bpm(grid[lo:hi], S[t, lo:hi]) if hi - lo >= 3 else grid[j]
    return out


class OnlineHRTracker:
    """
    Canlı demo için ileri (forward) Bayes filtresi — Viterbi'nin çevrimiçi eşi.
      tahmin:     inanç ⊛ Gauss(σ = rate·dt)
      güncelleme: inanç · p^conf
    """

    def __init__(self, grid: np.ndarray = BPM_GRID, max_rate_bpm_s: float = 4.0):
        self.grid = grid
        self.rate = max_rate_bpm_s
        self.belief = np.full(len(grid), 1.0 / len(grid))

    def reset(self):
        self.belief[:] = 1.0 / len(self.grid)

    def update(self, p: np.ndarray, dt: float, conf: float = 1.0) -> float:
        sigma = max(1.5, self.rate * dt)
        step = self.grid[1] - self.grid[0]
        k = int(np.ceil(4 * sigma / step))
        kern = np.exp(-0.5 * ((np.arange(-k, k + 1) * step) / sigma) ** 2)
        kern /= kern.sum()
        pred = np.convolve(self.belief, kern, mode="same") + 1e-9
        like = (p / (p.max() + 1e-15) + 1e-6) ** conf
        post = pred * like
        self.belief = post / post.sum()
        return peak_bpm(self.grid, self.belief)
