"""
Eulerian Video Magnification — renk büyütme (Wu vd., SIGGRAPH 2012).

Fikir: Her pikseli zamanda bir sinyal olarak ele al; nabız bandındaki
(ör. 0.8–2 Hz) küçük renk değişimlerini bant geçiren filtre ile ayır,
α kat büyüt ve orijinale geri ekle. Uzamsal gürültüyü azaltmak için
işlem Gauss piramidinin kaba bir seviyesinde yapılır (uzamsal alçak geçiren).

  Î(x,t) = I(x,t) + α · Up( BP_t( Down_L( I(x,t) ) ) )

Renk büyütmede kromatik bileşenler YIQ uzayında ayrı zayıflatılabilir.

İki sürüm:
  magnify_color     : çevrimdışı, ideal (FFT maskeli) zamansal filtre
  StreamingEVM      : çevrimiçi, 2. dereceden IIR Butterworth (canlı demo)
"""
from __future__ import annotations

from typing import List

import cv2
import numpy as np
from scipy import signal as sps

RGB2YIQ = np.array([[0.299, 0.587, 0.114],
                    [0.596, -0.274, -0.322],
                    [0.211, -0.523, 0.312]], dtype=np.float32)
YIQ2RGB = np.linalg.inv(RGB2YIQ).astype(np.float32)


def _down(img: np.ndarray, level: int) -> np.ndarray:
    for _ in range(level):
        img = cv2.pyrDown(img)
    return img


def magnify_color(frames: List[np.ndarray], fs: float, lo: float = 0.8, hi: float = 2.0,
                  alpha: float = 50.0, level: int = 4, chroma_atten: float = 1.0) -> List[np.ndarray]:
    """frames: BGR uint8 kare listesi. Aynı boyutta büyütülmüş kareler döndürür."""
    H, W = frames[0].shape[:2]
    small = []
    for f in frames:
        rgb = cv2.cvtColor(f, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
        yiq = rgb @ RGB2YIQ.T
        small.append(_down(yiq, level))
    V = np.stack(small)                                   # (T, h, w, 3)
    T = V.shape[0]
    F = np.fft.rfft(V, axis=0)
    freqs = np.fft.rfftfreq(T, d=1.0 / fs)
    mask = ((freqs >= lo) & (freqs <= hi)).astype(np.float32)
    filt = np.fft.irfft(F * mask[:, None, None, None], n=T, axis=0).astype(np.float32)
    filt *= alpha
    filt[..., 1:] *= chroma_atten
    out = []
    for f, d in zip(frames, filt):
        rgb = cv2.cvtColor(f, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
        yiq = rgb @ RGB2YIQ.T + cv2.resize(d, (W, H), interpolation=cv2.INTER_LINEAR)
        res = np.clip(yiq @ YIQ2RGB.T, 0, 1)
        out.append(cv2.cvtColor((res * 255).astype(np.uint8), cv2.COLOR_RGB2BGR))
    return out


class StreamingEVM:
    """Kare kare çalışan renk büyütme (IIR bant geçiren, piksel başına durum)."""

    def __init__(self, fs: float, lo: float = 0.8, hi: float = 2.0, alpha: float = 60.0, level: int = 4):
        self.alpha, self.level = alpha, level
        self.sos = sps.butter(1, [lo, hi], btype="bandpass", fs=fs, output="sos")
        self.z = None

    def process(self, frame_bgr: np.ndarray) -> np.ndarray:
        H, W = frame_bgr.shape[:2]
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
        yiq = rgb @ RGB2YIQ.T
        x = _down(yiq, self.level)
        if self.z is None or self.z.shape[1:] != x.shape:
            self.z = np.zeros((len(self.sos), 2) + x.shape, dtype=np.float32)
            self._warm = 0
        y = x
        for k, (b0, b1, b2, a0, a1, a2) in enumerate(self.sos):
            z0, z1 = self.z[k, 0], self.z[k, 1]
            out = b0 * y + z0
            self.z[k, 0] = b1 * y - a1 * out + z1
            self.z[k, 1] = b2 * y - a2 * out
            y = out
        self._warm += 1
        if self._warm < 15:  # filtre oturana kadar büyütme yapma
            return frame_bgr
        yiq = yiq + self.alpha * cv2.resize(y, (W, H), interpolation=cv2.INTER_LINEAR)
        res = np.clip(yiq @ YIQ2RGB.T, 0, 1)
        return cv2.cvtColor((res * 255).astype(np.uint8), cv2.COLOR_RGB2BGR)
