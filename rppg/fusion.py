"""
ÖZGÜN KATKI 1 — SNR ağırlıklı çoklu-ROI spektral füzyon
ÖZGÜN KATKI 2 — Hareket farkında güven ağırlığı

Motivasyon
----------
Klasik rPPG çalışmalarının çoğu tek bir ROI (tüm yüz veya alın) kullanır ya
da ROI'lerin RGB ortalamasını birleştirir. Oysa gerçek hayatta:
  * alın saçla örtülebilir,
  * bir yanağa ekran/pencere ışığı vurabilir,
  * konuşurken yanaklar hareket eder, alın sabit kalır.
Sabit ağırlıklı ortalama bu durumlarda bozuk bölgenin gürültüsünü sinyale
karıştırır.

Yöntem
------
Her ROI r ve her zaman penceresi t için:
    S_r(t, f)     : normalize güç spektrumu
    SNR_r(t)      : o penceredeki tepe çevresi güç / geri kalan güç
    w_r(t)        = SNR_lin_r(t) ** γ        (γ = 2)
    S_fused(t, f) = Σ_r w_r(t) S_r(t, f) / Σ_r w_r(t)
Böylece her pencerede o an en temiz sinyali veren bölge baskın olur ve
ağırlıklar zamanla değişebilir (ör. kişi başını çevirince).

Hareket farkında güven:
    c(t) = 1 / (1 + (m̄(t) / m_ref)²),   m_ref = 2·medyan(m̄)
Viterbi'de gözlem log-olasılığı c(t) ile ölçeklenir: yüksek hareketli
pencerede spektrum "daha az inanılır" ve takip önceki HR eğilimini sürdürür.
"""
from __future__ import annotations

from typing import Dict, Tuple

import numpy as np

from .hr import BPM_GRID, peak_bpm, spectrum_bpm, window_snr_from_spectrum, window_starts


def motion_confidence(motion: np.ndarray, fs: float, win_sec: float, step_sec: float,
                      floor: float = 0.1) -> np.ndarray:
    starts, L, _ = window_starts(len(motion), fs, win_sec, step_sec)
    m = np.array([np.mean(motion[s:s + L]) for s in starts])
    ref = 2.0 * np.median(m) + 1e-9
    c = 1.0 / (1.0 + (m / ref) ** 2)
    return np.clip(c / c.max(), floor, 1.0)


def snr_fused_spectrogram(bvps: Dict[str, np.ndarray], fs: float, win_sec: float = 10.0,
                          step_sec: float = 1.0, gamma: float = 2.0, grid: np.ndarray = BPM_GRID
                          ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, list, np.ndarray]:
    names = list(bvps.keys())
    n = len(next(iter(bvps.values())))
    starts, L, centers = window_starts(n, fs, win_sec, step_sec)
    T, F, R = len(starts), len(grid), len(names)
    specs = np.zeros((R, T, F))
    snrs = np.zeros((T, R))
    for r, name in enumerate(names):
        x = bvps[name]
        for t, s in enumerate(starts):
            p = spectrum_bpm(x[s:s + L], fs, grid)
            specs[r, t] = p
            snrs[t, r] = window_snr_from_spectrum(grid, p, peak_bpm(grid, p))
    w = np.power(10.0, snrs / 10.0) ** gamma
    w = w / w.sum(axis=1, keepdims=True)
    fused = np.einsum("tr,rtf->tf", w, specs)
    fused /= fused.sum(axis=1, keepdims=True)
    return centers, fused, w, names, snrs
