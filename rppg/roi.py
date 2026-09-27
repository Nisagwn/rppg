"""
Yüz tespiti, takibi, ROI (ilgi bölgesi) tanımları ve cilt segmentasyonu.

Klasik görüntü işleme adımları:
  * Viola-Jones Haar kaskad sınıflandırıcı ile yüz tespiti
  * Normalize çapraz korelasyon (NCC) ile şablon eşleme tabanlı takip
  * Üstel hareketli ortalama (EMA) ile kutu titreşiminin bastırılması
  * YCrCb renk uzayında eşikleme ile cilt maskesi
  * Morfolojik açma/kapama ile maske temizliği
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import cv2
import numpy as np

CASCADE_PATH = (cv2.data.haarcascades if hasattr(cv2, "data") else "") + "haarcascade_frontalface_default.xml"

# ROI'ler yüz kutusuna göre oransal tanımlanır: (x, y, w, h) kesirleri.
ROI_DEFS: Dict[str, Tuple[float, float, float, float]] = {
    "forehead": (0.30, 0.08, 0.40, 0.17),
    "left_cheek": (0.15, 0.50, 0.22, 0.22),
    "right_cheek": (0.63, 0.50, 0.22, 0.22),
    "full": (0.20, 0.10, 0.60, 0.80),
}

ROI_NAMES_TR = {
    "forehead": "Alın",
    "left_cheek": "Sol yanak",
    "right_cheek": "Sağ yanak",
    "full": "Tüm yüz",
}

# YCrCb cilt eşikleri (Chai & Ngan 1999'a dayalı yaygın aralıklar)
SKIN_CR = (133, 173)
SKIN_CB = (77, 127)
SKIN_Y = (40, 240)  # çok karanlık ve parlama (specular) pikselleri dışla


@dataclass
class BBox:
    x: float
    y: float
    w: float
    h: float

    def as_int(self) -> Tuple[int, int, int, int]:
        return int(round(self.x)), int(round(self.y)), int(round(self.w)), int(round(self.h))

    @property
    def center(self) -> Tuple[float, float]:
        return self.x + self.w / 2.0, self.y + self.h / 2.0

    def to_array(self) -> np.ndarray:
        return np.array([self.x, self.y, self.w, self.h], dtype=float)


def clip_rect(x: int, y: int, w: int, h: int, shape) -> Tuple[int, int, int, int]:
    H, W = shape[:2]
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W, x + w), min(H, y + h)
    return x0, y0, max(0, x1 - x0), max(0, y1 - y0)


def roi_rects(bbox: BBox, frame_shape, names=None) -> Dict[str, Tuple[int, int, int, int]]:
    """Yüz kutusundan ROI dikdörtgenlerini (piksel) hesaplar."""
    names = names or list(ROI_DEFS.keys())
    out = {}
    for n in names:
        fx, fy, fw, fh = ROI_DEFS[n]
        r = (int(bbox.x + fx * bbox.w), int(bbox.y + fy * bbox.h),
             max(2, int(fw * bbox.w)), max(2, int(fh * bbox.h)))
        out[n] = clip_rect(*r, frame_shape)
    return out


_MORPH_KERNEL = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))


def skin_mask(patch_bgr: np.ndarray) -> np.ndarray:
    """YCrCb eşikleme + morfolojik açma/kapama ile cilt maskesi (uint8 0/255)."""
    ycrcb = cv2.cvtColor(patch_bgr, cv2.COLOR_BGR2YCrCb)
    lo = np.array([SKIN_Y[0], SKIN_CR[0], SKIN_CB[0]], dtype=np.uint8)
    hi = np.array([SKIN_Y[1], SKIN_CR[1], SKIN_CB[1]], dtype=np.uint8)
    m = cv2.inRange(ycrcb, lo, hi)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, _MORPH_KERNEL)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, _MORPH_KERNEL)
    return m


class FaceTracker:
    """
    Haar kaskad tespiti + NCC şablon eşleme ile yüz takibi.

    - Her `detect_every` karede bir Haar tespiti yapılır (pahalı, titrek).
    - Aradaki karelerde yüz şablonu arama penceresinde NCC ile eşlenir
      (ucuz, alt-piksele yakın kararlı).
    - Tespit sonuçları EMA ile yumuşatılır; böylece ROI kenarındaki
      titreşimin sinyale sızması azaltılır.
    - `initial_bbox` verilir ve `use_haar=False` ise yalnızca şablon
      takibi yapılır (sentetik veriler ve Haar'ın bulamadığı durumlar için).
    """

    def __init__(self, detect_every: int = 15, smooth: float = 0.7,
                 use_haar: bool = True, initial_bbox: Optional[Tuple[float, float, float, float]] = None,
                 min_face: int = 60, search_margin: float = 0.25, ncc_threshold: float = 0.45):
        self.detect_every = detect_every
        self.smooth = smooth
        self.use_haar = use_haar
        self.min_face = min_face
        self.search_margin = search_margin
        self.ncc_threshold = ncc_threshold
        if use_haar and not hasattr(cv2, "CascadeClassifier"):
            raise RuntimeError(
                f"Bu OpenCV sürümünde ({cv2.__version__}) Haar kaskad sınıflandırıcı yok (OpenCV 5 kaldırdı). "
                "Çözüm: pip install \"opencv-python>=4.8,<5\"")
        self.cascade = cv2.CascadeClassifier(CASCADE_PATH) if use_haar else None
        if use_haar and self.cascade.empty():
            raise RuntimeError(f"Haar kaskad dosyası yüklenemedi: {CASCADE_PATH}")
        self.bbox: Optional[BBox] = BBox(*initial_bbox) if initial_bbox is not None else None
        self.template: Optional[np.ndarray] = None
        self.frame_idx = 0
        self.prev_gray_face: Optional[np.ndarray] = None
        self.prev_center: Optional[Tuple[float, float]] = None
        self.lost_frames = 0

    # -- yardımcılar -------------------------------------------------------
    def _detect(self, gray: np.ndarray) -> Optional[BBox]:
        faces = self.cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5,
                                              minSize=(self.min_face, self.min_face))
        if len(faces) == 0:
            return None
        if self.bbox is not None:
            cx, cy = self.bbox.center
            faces = sorted(faces, key=lambda f: (f[0] + f[2] / 2 - cx) ** 2 + (f[1] + f[3] / 2 - cy) ** 2)
            return BBox(*map(float, faces[0]))
        f = max(faces, key=lambda f: f[2] * f[3])
        return BBox(*map(float, f))

    def _set_template(self, gray: np.ndarray):
        x, y, w, h = self.bbox.as_int()
        # şablon: yüzün iç kısmı (arka plan kenarları hariç)
        tx, ty, tw, th = clip_rect(x + int(0.15 * w), y + int(0.15 * h), int(0.7 * w), int(0.7 * h), gray.shape)
        if tw > 8 and th > 8:
            self.template = gray[ty:ty + th, tx:tx + tw].copy()
            self._tmpl_offset = (tx - x, ty - y)

    def _track_template(self, gray: np.ndarray) -> Optional[BBox]:
        if self.template is None or self.bbox is None:
            return None
        x, y, w, h = self.bbox.as_int()
        mx, my = int(self.search_margin * w), int(self.search_margin * h)
        sx, sy, sw, sh = clip_rect(x - mx, y - my, w + 2 * mx, h + 2 * my, gray.shape)
        th, tw = self.template.shape
        if sw <= tw or sh <= th:
            return None
        res = cv2.matchTemplate(gray[sy:sy + sh, sx:sx + sw], self.template, cv2.TM_CCOEFF_NORMED)
        _, maxv, _, maxloc = cv2.minMaxLoc(res)
        if maxv < self.ncc_threshold:
            return None
        # alt-piksel tepe konumu (parabolik yaklaşım)
        px, py = float(maxloc[0]), float(maxloc[1])
        ix, iy = maxloc
        if 0 < ix < res.shape[1] - 1:
            l, c, r = res[iy, ix - 1], res[iy, ix], res[iy, ix + 1]
            d = l - 2 * c + r
            if abs(d) > 1e-9:
                px += 0.5 * (l - r) / d
        if 0 < iy < res.shape[0] - 1:
            u, c, dn = res[iy - 1, ix], res[iy, ix], res[iy + 1, ix]
            d = u - 2 * c + dn
            if abs(d) > 1e-9:
                py += 0.5 * (u - dn) / d
        ox, oy = self._tmpl_offset
        return BBox(sx + px - ox, sy + py - oy, self.bbox.w, self.bbox.h)

    # -- ana arayüz ------------------------------------------------------------
    def update(self, frame_bgr: np.ndarray) -> Tuple[Optional[BBox], float]:
        """Yeni kareyi işler. (bbox, hareket_indeksi) döndürür."""
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        new = None
        do_detect = self.use_haar and (self.bbox is None or self.frame_idx % self.detect_every == 0
                                       or self.lost_frames > 0)
        if do_detect:
            det = self._detect(gray)
            if det is not None:
                if self.bbox is None:
                    new = det
                else:
                    a = self.smooth
                    new = BBox(a * self.bbox.x + (1 - a) * det.x, a * self.bbox.y + (1 - a) * det.y,
                               a * self.bbox.w + (1 - a) * det.w, a * self.bbox.h + (1 - a) * det.h)
                self.bbox = new
                self._set_template(gray)
        if new is None and self.bbox is not None:
            if self.template is None:
                self._set_template(gray)
                new = self.bbox
            else:
                new = self._track_template(gray)
                if new is not None:
                    self.bbox = new
        if new is None:
            self.lost_frames += 1
        else:
            self.lost_frames = 0
        self.frame_idx += 1

        # hareket indeksi = kutu merkez yer değiştirmesi (yüz genişliğine oranla)
        #                 + yüz içindeki ortalama mutlak kare farkı (ifade/konuşma)
        motion = 0.0
        if self.bbox is not None:
            x, y, w, h = self.bbox.as_int()
            fx, fy, fw, fh = clip_rect(x, y, w, h, gray.shape)
            face = cv2.resize(gray[fy:fy + fh, fx:fx + fw], (64, 64)).astype(np.float32) if fw > 4 and fh > 4 else None
            c = self.bbox.center
            if self.prev_center is not None:
                motion += float(np.hypot(c[0] - self.prev_center[0], c[1] - self.prev_center[1]) / max(self.bbox.w, 1))
            if face is not None and self.prev_gray_face is not None:
                motion += float(np.mean(np.abs(face - self.prev_gray_face)) / 255.0)
            self.prev_center = c
            self.prev_gray_face = face
        return (self.bbox if new is not None else None), motion
