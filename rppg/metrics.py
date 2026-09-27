"""Değerlendirme metrikleri."""
from __future__ import annotations

import numpy as np


def mae(est, ref) -> float:
    return float(np.mean(np.abs(np.asarray(est) - np.asarray(ref))))


def rmse(est, ref) -> float:
    return float(np.sqrt(np.mean((np.asarray(est) - np.asarray(ref)) ** 2)))


def mape(est, ref) -> float:
    ref = np.asarray(ref, dtype=float)
    return float(np.mean(np.abs(np.asarray(est) - ref) / np.maximum(ref, 1e-9)) * 100)


def pearson(est, ref) -> float:
    e, r = np.asarray(est, float), np.asarray(ref, float)
    if len(e) < 3 or e.std() < 1e-9 or r.std() < 1e-9:
        return float("nan")
    return float(np.corrcoef(e, r)[0, 1])


def within(est, ref, tol: float = 5.0) -> float:
    """|hata| <= tol BPM olan pencerelerin yüzdesi."""
    return float(np.mean(np.abs(np.asarray(est) - np.asarray(ref)) <= tol) * 100)


def bland_altman(est, ref):
    e, r = np.asarray(est, float), np.asarray(ref, float)
    d = e - r
    bias = float(d.mean())
    sd = float(d.std(ddof=1)) if len(d) > 1 else 0.0
    return {"bias": bias, "loa_low": bias - 1.96 * sd, "loa_high": bias + 1.96 * sd,
            "mean": (e + r) / 2, "diff": d}


def summarize(est, ref) -> dict:
    return {"MAE": mae(est, ref), "RMSE": rmse(est, ref), "MAPE": mape(est, ref),
            "r": pearson(est, ref), "<=5BPM%": within(est, ref, 5.0)}
