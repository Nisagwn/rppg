"""
Solunum hızı tahmini.

Kaynak sinyal: göğüs bölgesinde Farnebäck yoğun optik akışının dikey
bileşeninin medyanı (her kare). Kümülatif toplam -> göğüs yer değiştirmesi.
Göğüs görünmüyorsa yedek sinyal: yüz merkezinin dikey konumu (nefesle baş
hafifçe inip kalkar).

Adımlar: kümülatif toplam -> Tarvainen detrend -> 0.1–0.5 Hz bant geçiren
-> kayan pencere (30 s) spektrumu -> tepe (nefes/dk).
"""
from __future__ import annotations

import numpy as np

from .filtering import RESP_BAND, bandpass, detrend_tarvainen, zscore
from .hr import peak_bpm, spectrum_bpm, window_starts

RR_GRID = np.arange(6.0, 30.0 + 1e-9, 0.25)  # nefes/dk


def respiration_signal(chest_dy: np.ndarray, fs: float, face_cy: np.ndarray = None) -> np.ndarray:
    dy = np.nan_to_num(np.asarray(chest_dy, dtype=float))
    use_face = np.count_nonzero(dy) < 0.5 * len(dy)
    x = np.asarray(face_cy, dtype=float) if (use_face and face_cy is not None) else np.cumsum(dy)
    x = detrend_tarvainen(x, lam=max(300.0, 10 * fs))
    return zscore(bandpass(x, fs, *RESP_BAND, order=2))


def respiration_rate(chest_dy: np.ndarray, fs: float, face_cy: np.ndarray = None,
                     win_sec: float = 30.0, step_sec: float = 2.0):
    """(merkez_zamanları, nefes/dk dizisi, tüm sinyal için tek tahmin, sinyal)"""
    x = respiration_signal(chest_dy, fs, face_cy)
    starts, L, centers = window_starts(len(x), fs, min(win_sec, len(x) / fs), step_sec)
    rr = np.array([peak_bpm(RR_GRID, spectrum_bpm(x[s:s + L], fs, RR_GRID)) for s in starts])
    overall = peak_bpm(RR_GRID, spectrum_bpm(x, fs, RR_GRID))
    return centers, rr, overall, x
