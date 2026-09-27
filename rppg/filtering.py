"""
Sinyal ön işleme: trend giderme ve bant geçiren filtreleme.

* Tarvainen vd. (2002) düzgünlük önselli (smoothness priors) detrend:
      z_trend = (I + λ² D₂ᵀ D₂)⁻¹ z
  Burada D₂ ikinci fark operatörüdür. Aydınlatma kaynaklı yavaş kaymaları
  kaldırırken nabız bileşenine dokunmaz.
* Sıfır fazlı Butterworth bant geçiren filtre (ileri-geri, sosfiltfilt):
  Faz kayması yaratmadığı için dalga biçimi ve tepe zamanları korunur.
"""
from __future__ import annotations

import numpy as np
from scipy import signal, sparse
from scipy.sparse.linalg import spsolve

HR_BAND = (0.7, 3.5)     # Hz  -> 42–210 BPM
RESP_BAND = (0.1, 0.5)   # Hz  -> 6–30 nefes/dk


def detrend_tarvainen(x: np.ndarray, lam: float = 100.0) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    n = len(x)
    if n < 4:
        return x - x.mean()
    I = sparse.eye(n, format="csc")
    D2 = sparse.diags([1.0, -2.0, 1.0], [0, 1, 2], shape=(n - 2, n), format="csc")
    A = I + (lam ** 2) * (D2.T @ D2)
    trend = spsolve(A.tocsc(), x)
    return x - trend


def bandpass(x: np.ndarray, fs: float, lo: float, hi: float, order: int = 3) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    hi = min(hi, 0.45 * fs)
    sos = signal.butter(order, [lo, hi], btype="bandpass", fs=fs, output="sos")
    padlen = min(len(x) - 1, 3 * (2 * len(sos) + 1) * 3)
    if len(x) < 10:
        return x - x.mean()
    return signal.sosfiltfilt(sos, x, padlen=padlen)


def zscore(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    s = x.std()
    return (x - x.mean()) / (s if s > 1e-12 else 1.0)


def preprocess_bvp(x: np.ndarray, fs: float, band=HR_BAND, lam: float = 100.0) -> np.ndarray:
    """Detrend -> bant geçiren -> z-skor."""
    return zscore(bandpass(detrend_tarvainen(x, lam), fs, *band))


def interpolate_nans(x: np.ndarray) -> np.ndarray:
    """1B veya 2B (zaman ekseni 0) dizide NaN'ları doğrusal enterpolasyonla doldurur."""
    x = np.array(x, dtype=float, copy=True)
    if x.ndim == 1:
        x = x[:, None]
        squeeze = True
    else:
        squeeze = False
    t = np.arange(len(x))
    for c in range(x.shape[1]):
        col = x[:, c]
        bad = ~np.isfinite(col)
        if bad.all():
            col[:] = 0.0
        elif bad.any():
            col[bad] = np.interp(t[bad], t[~bad], col[~bad])
    return x[:, 0] if squeeze else x


def resample_uniform(values: np.ndarray, timestamps: np.ndarray, fs: float):
    """Düzensiz zaman damgalı örnekleri sabit fs ızgarasına enterpole eder.
    Webcam'lerde FPS dalgalanması spektrumu bozar; bu adım onu düzeltir."""
    timestamps = np.asarray(timestamps, dtype=float)
    t0 = timestamps[0]
    tt = timestamps - t0
    grid = np.arange(0.0, tt[-1], 1.0 / fs)
    values = np.asarray(values, dtype=float)
    if values.ndim == 1:
        return grid, np.interp(grid, tt, values)
    return grid, np.stack([np.interp(grid, tt, values[:, c]) for c in range(values.shape[1])], axis=1)
