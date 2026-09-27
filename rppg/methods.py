"""
rPPG yöntemleri: RGB izlerinden kan hacmi nabız (BVP) sinyali elde etme.

Hepsi (N, 3) RGB dizisi ve örnekleme frekansı alır, (N,) BVP döndürür.

GREEN  – Verkruysse vd. 2008: Hemoglobin yeşil ışığı en güçlü soğurduğu için
         yeşil kanal tek başına en yüksek nabız genliğini taşır.
ICA    – Poh vd. 2010: Normalize RGB'ye FastICA; nabız bandında en baskın
         spektral tepeye sahip bileşen seçilir.
CHROM  – de Haan & Jeanne 2013: Renklilik (chrominance) projeksiyonu
         X = 3R - 2G, Y = 1.5R + G - 1.5B;  S = Xf - α Yf,  α = σ(Xf)/σ(Yf).
         Beyaz ışık varsayımıyla speküler yansımayı bastırır.
POS    – Wang vd. 2017: Cilt tonuna dik düzlem (Plane-Orthogonal-to-Skin)
         P = [[0, 1, -1], [-2, 1, 1]];  h = S1 + (σ1/σ2) S2
         Kısa pencerelerde hesaplanıp örtüşmeli toplama ile birleştirilir.
LGI    – Pilz vd. 2018: Yerel grup değişmezliği; pencere kovaryansının
         baskın bileşeni (yoğunluk değişimi) izdüşümle atılır.
"""
from __future__ import annotations

import numpy as np
from scipy import signal as sps

from .filtering import HR_BAND, bandpass


def _temporal_normalize(rgb: np.ndarray) -> np.ndarray:
    m = rgb.mean(axis=0, keepdims=True)
    m[m == 0] = 1.0
    return rgb / m


def green(rgb: np.ndarray, fs: float) -> np.ndarray:
    return rgb[:, 1].astype(float)


def ica(rgb: np.ndarray, fs: float, seed: int = 0) -> np.ndarray:
    from sklearn.decomposition import FastICA

    x = rgb.astype(float)
    x = (x - x.mean(0)) / (x.std(0) + 1e-12)
    x = np.stack([bandpass(x[:, c], fs, *HR_BAND) for c in range(3)], axis=1)
    import warnings

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            S = FastICA(n_components=3, random_state=seed, whiten="unit-variance",
                        max_iter=1000).fit_transform(x)
    except Exception:
        return x[:, 1]
    best, best_score = S[:, 1], -1.0
    for k in range(S.shape[1]):
        f, p = sps.periodogram(S[:, k], fs=fs, nfft=max(len(S), int(fs * 60)))
        band = (f >= HR_BAND[0]) & (f <= HR_BAND[1])
        score = p[band].max() / (p.sum() + 1e-12)
        if score > best_score:
            best, best_score = S[:, k], score
    return best


def _overlap_add(rgb: np.ndarray, fs: float, win_sec: float, fn) -> np.ndarray:
    n = len(rgb)
    L = max(8, int(np.ceil(win_sec * fs)))
    if n <= L:
        return fn(_temporal_normalize(rgb))
    out = np.zeros(n)
    wsum = np.zeros(n)
    hann = np.hanning(L)
    step = max(1, L // 2)
    starts = list(range(0, n - L + 1, step))
    if starts[-1] != n - L:
        starts.append(n - L)
    for s in starts:
        seg = rgb[s:s + L]
        cn = _temporal_normalize(seg)
        h = fn(cn)
        h = h - h.mean()
        sd = h.std()
        if sd > 1e-12:
            h = h / sd
        out[s:s + L] += h * hann
        wsum[s:s + L] += hann
    wsum[wsum == 0] = 1.0
    return out / wsum


def pos(rgb: np.ndarray, fs: float, win_sec: float = 1.6) -> np.ndarray:
    P = np.array([[0.0, 1.0, -1.0], [-2.0, 1.0, 1.0]])

    def f(cn):
        S = cn @ P.T                       # (L, 2)
        s1, s2 = S[:, 0], S[:, 1]
        return s1 + (s1.std() / (s2.std() + 1e-12)) * s2

    return _overlap_add(rgb.astype(float), fs, win_sec, f)


def chrom(rgb: np.ndarray, fs: float, win_sec: float = 1.6) -> np.ndarray:
    rgb = rgb.astype(float)
    # yerel ortalama ile normalize (kayan ortalama ~ win_sec)
    L = max(3, int(win_sec * fs))
    kernel = np.ones(L) / L
    mean = np.stack([np.convolve(np.pad(rgb[:, c], (L // 2, L - 1 - L // 2), mode="edge"), kernel, "valid")
                     for c in range(3)], axis=1)
    cn = rgb / np.maximum(mean, 1e-6)
    X = 3 * cn[:, 0] - 2 * cn[:, 1]
    Y = 1.5 * cn[:, 0] + cn[:, 1] - 1.5 * cn[:, 2]
    Xf = bandpass(X, fs, *HR_BAND)
    Yf = bandpass(Y, fs, *HR_BAND)
    # α pencere bazında hesaplanır, örtüşmeli toplama
    n = len(rgb)
    if n <= L:
        return Xf - (Xf.std() / (Yf.std() + 1e-12)) * Yf
    out, wsum = np.zeros(n), np.zeros(n)
    hann = np.hanning(L)
    step = max(1, L // 2)
    starts = list(range(0, n - L + 1, step))
    if starts[-1] != n - L:
        starts.append(n - L)
    for s in starts:
        x, y = Xf[s:s + L], Yf[s:s + L]
        h = x - (x.std() / (y.std() + 1e-12)) * y
        h = h - h.mean()
        out[s:s + L] += h * hann
        wsum[s:s + L] += hann
    wsum[wsum == 0] = 1.0
    return out / wsum


def lgi(rgb: np.ndarray, fs: float, win_sec: float = 1.6) -> np.ndarray:
    def f(cn):
        # Merkezlenmemiş normalize veri: baskın tekil vektör ≈ yoğunluk/cilt
        # tonu yönüdür (Pilz vd. 2018; rPPG-Toolbox uygulamasıyla aynı).
        c = cn
        U, _, _ = np.linalg.svd(c.T @ c)
        u = U[:, :1]
        Pm = np.eye(3) - u @ u.T
        S = c @ Pm.T
        return S[:, 1]

    return _overlap_add(rgb.astype(float), fs, win_sec, f)


METHODS = {"green": green, "ica": ica, "chrom": chrom, "pos": pos, "lgi": lgi}
METHOD_NAMES_TR = {"green": "GREEN", "ica": "ICA", "chrom": "CHROM", "pos": "POS", "lgi": "LGI"}


def apply_method(name: str, rgb: np.ndarray, fs: float) -> np.ndarray:
    if name not in METHODS:
        raise ValueError(f"Bilinmeyen yöntem: {name}. Seçenekler: {list(METHODS)}")
    return METHODS[name](rgb, fs)
