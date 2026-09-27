"""
Videodan ham sinyallerin çıkarılması (uzamsal ortalama).

Her karede:
  1. Yüz takip edilir (roi.FaceTracker)
  2. Her ROI için cilt maskesi (YCrCb + morfoloji) uygulanır
  3. Maske içindeki piksellerin ortalama R, G, B değeri alınır
     -> uzamsal ortalama, kamera gürültüsünü ~1/sqrt(N) oranında bastırır
  4. Göğüs bölgesinde Farnebäck yoğun optik akışının dikey bileşeni ortalanır
     (solunum için)
Sonuç: zaman x kanal izleri (Traces).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, Optional, Sequence

import cv2
import numpy as np

from .filtering import interpolate_nans, resample_uniform
from .roi import ROI_DEFS, FaceTracker, clip_rect, roi_rects, skin_mask


@dataclass
class Traces:
    fps: float
    rgb: Dict[str, np.ndarray]            # ROI adı -> (N, 3) RGB ortalamaları
    skin_ratio: Dict[str, np.ndarray]     # ROI adı -> (N,) cilt piksel oranı
    motion: np.ndarray                    # (N,) hareket indeksi
    bboxes: np.ndarray                    # (N, 4) x, y, w, h
    chest_dy: np.ndarray                  # (N,) göğüs dikey optik akış ortalaması
    face_cy: np.ndarray                   # (N,) yüz merkezi dikey konumu
    meta: dict = field(default_factory=dict)

    @property
    def n(self) -> int:
        return len(self.motion)

    def save(self, path: str):
        d = {"fps": self.fps, "motion": self.motion, "bboxes": self.bboxes,
             "chest_dy": self.chest_dy, "face_cy": self.face_cy}
        for k, v in self.rgb.items():
            d[f"rgb__{k}"] = v
        for k, v in self.skin_ratio.items():
            d[f"skin__{k}"] = v
        np.savez_compressed(path, **d)

    @staticmethod
    def load(path: str) -> "Traces":
        z = np.load(path)
        rgb = {k[5:]: z[k] for k in z.files if k.startswith("rgb__")}
        skin = {k[6:]: z[k] for k in z.files if k.startswith("skin__")}
        return Traces(float(z["fps"]), rgb, skin, z["motion"], z["bboxes"], z["chest_dy"], z["face_cy"])

    def slice(self, start: int, end: int) -> "Traces":
        return Traces(self.fps, {k: v[start:end] for k, v in self.rgb.items()},
                      {k: v[start:end] for k, v in self.skin_ratio.items()},
                      self.motion[start:end], self.bboxes[start:end],
                      self.chest_dy[start:end], self.face_cy[start:end], dict(self.meta))

    def resampled(self, timestamps: np.ndarray, fs: float) -> "Traces":
        """Düzensiz zaman damgalarından sabit fs'e yeniden örnekleme."""
        def rs(a):
            return resample_uniform(a, timestamps, fs)[1]
        return Traces(fs, {k: rs(v) for k, v in self.rgb.items()},
                      {k: rs(v) for k, v in self.skin_ratio.items()},
                      rs(self.motion), rs(self.bboxes), rs(self.chest_dy), rs(self.face_cy), dict(self.meta))


def chest_rect(bbox, frame_shape):
    x, y, w, h = bbox
    return clip_rect(int(x - 0.25 * w), int(y + 1.2 * h), int(1.5 * w), int(0.8 * h), frame_shape)


MASK_GRID = 32  # yumuşak maskenin ROI'ye göre sabit çözünürlüğü


class TraceExtractor:
    """
    Kare kare çalışan çıkarıcı (canlı demo da bunu kullanır).

    ÖZGÜN KATKI 4 — Zamanda yumuşatılmış (soft) cilt maskesi
    ------------------------------------------------------
    Her karede yeniden hesaplanan İKİLİ cilt maskesinde, eşik sınırındaki
    pikseller aydınlatma değiştikçe maskeye girip çıkar. Böylece ROI
    ortalaması ışığa göre doğrusal olmaktan çıkar ve POS/CHROM'un
    "yoğunluk değişimi tüm kanallarda orantılıdır" varsayımı bozulur:
    ışık titremesi nabız sanılır (deneyle gösterildi, bkz. rapor).

    Çözüm: ROI'ye göre normalize edilmiş sabit bir ızgarada (32x32) maske
    olasılık haritası üstel ortalama ile güncellenir
        p_t = β p_{t-1} + (1-β) m_t,   β = 0.98  (~1.7 s zaman sabiti)
    ve ortalama bu p ile AĞIRLIKLI alınır (eşik yok -> doğrusal).
    1.7 Hz'lik titremenin maskeye sızması ~17 kat azalır.
    mask_mode: "soft" (varsayılan) | "binary" (klasik) | "none"
    """

    def __init__(self, tracker: FaceTracker, rois: Sequence[str] = tuple(ROI_DEFS.keys()),
                 use_skin_mask: bool = True, respiration: bool = True, min_skin_ratio: float = 0.15,
                 mask_mode: str = "soft", mask_beta: float = 0.98):
        self.tracker = tracker
        self.rois = list(rois)
        self.use_skin_mask = use_skin_mask
        self.mask_mode = mask_mode if use_skin_mask else "none"
        self.mask_beta = mask_beta
        self.mask_prob = {}
        self.respiration = respiration
        self.min_skin_ratio = min_skin_ratio
        self.prev_chest = None
        self.prev_chest_rect = None

    def process(self, frame_bgr: np.ndarray):
        bbox, motion = self.tracker.update(frame_bgr)
        rgb, skin = {}, {}
        chest_dy = np.nan
        if bbox is None:
            for n in self.rois:
                rgb[n] = np.full(3, np.nan)
                skin[n] = 0.0
            self.prev_chest = None
            return None, motion, rgb, skin, chest_dy, None

        rects = roi_rects(bbox, frame_bgr.shape, self.rois)
        for n, (x, y, w, h) in rects.items():
            patch = frame_bgr[y:y + h, x:x + w]
            if patch.size == 0:
                rgb[n] = np.full(3, np.nan)
                skin[n] = 0.0
                continue
            if self.mask_mode == "binary":
                m = skin_mask(patch)
                ratio = float(np.count_nonzero(m)) / m.size
                if ratio >= self.min_skin_ratio:
                    b, g, r, _ = cv2.mean(patch, mask=m)
                else:  # maske güvenilmez -> tüm ROI
                    b, g, r, _ = cv2.mean(patch)
            elif self.mask_mode == "soft":
                m = cv2.resize(skin_mask(patch), (MASK_GRID, MASK_GRID), interpolation=cv2.INTER_AREA)
                m = m.astype(np.float32) / 255.0
                p = self.mask_prob.get(n)
                p = m if p is None else self.mask_beta * p + (1 - self.mask_beta) * m
                self.mask_prob[n] = p
                ratio = float(p.mean())
                if ratio >= self.min_skin_ratio:
                    wgt = cv2.resize(p, (w, h), interpolation=cv2.INTER_LINEAR)
                    s_ = float(wgt.sum()) + 1e-9
                    b, g, r = np.tensordot(wgt, patch.astype(np.float32), axes=([0, 1], [0, 1])) / s_
                else:
                    b, g, r, _ = cv2.mean(patch)
            else:
                ratio = 1.0
                b, g, r, _ = cv2.mean(patch)
            rgb[n] = np.array([r, g, b])
            skin[n] = ratio

        if self.respiration:
            cx, cy, cw, ch = chest_rect(bbox.to_array(), frame_bgr.shape)
            if cw > 16 and ch > 16:
                gray = cv2.cvtColor(frame_bgr[cy:cy + ch, cx:cx + cw], cv2.COLOR_BGR2GRAY)
                scale = 96.0 / max(cw, ch)
                small = cv2.resize(gray, (max(8, int(cw * scale)), max(8, int(ch * scale))))
                if self.prev_chest is not None and self.prev_chest.shape == small.shape:
                    flow = cv2.calcOpticalFlowFarneback(self.prev_chest, small, None,
                                                        0.5, 2, 9, 3, 5, 1.1, 0)
                    chest_dy = float(np.median(flow[..., 1])) / scale
                self.prev_chest = small
            else:
                self.prev_chest = None
        return bbox, motion, rgb, skin, chest_dy, rects


def extract_traces(frames: Iterable[np.ndarray], fps: float, tracker: Optional[FaceTracker] = None,
                   rois: Sequence[str] = tuple(ROI_DEFS.keys()), use_skin_mask: bool = True,
                   respiration: bool = True, max_frames: Optional[int] = None,
                   progress: bool = False, mask_mode: str = "soft") -> Traces:
    tracker = tracker or FaceTracker()
    ex = TraceExtractor(tracker, rois, use_skin_mask, respiration, mask_mode=mask_mode)
    rgb = {n: [] for n in rois}
    skin = {n: [] for n in rois}
    motion, bboxes, chest, face_cy = [], [], [], []
    for i, frame in enumerate(frames):
        if max_frames is not None and i >= max_frames:
            break
        bbox, m, r, s, dy, _ = ex.process(frame)
        for n in rois:
            rgb[n].append(r[n])
            skin[n].append(s[n])
        motion.append(m)
        bboxes.append(bbox.to_array() if bbox is not None else np.full(4, np.nan))
        chest.append(dy)
        face_cy.append(bbox.center[1] if bbox is not None else np.nan)
        if progress and i % 300 == 0:
            print(f"  kare {i}", flush=True)
    if len(motion) == 0:
        raise ValueError("Videodan hiç kare okunamadı.")
    bb = np.array(bboxes)
    if np.all(np.isnan(bb[:, 0])):
        raise RuntimeError("Hiçbir karede yüz bulunamadı. Işığı/kamera açısını kontrol edin "
                           "veya --bbox ile başlangıç kutusu verin.")
    out = Traces(
        fps=float(fps),
        rgb={n: interpolate_nans(np.array(v)) for n, v in rgb.items()},
        skin_ratio={n: np.array(v, dtype=float) for n, v in skin.items()},
        motion=np.array(motion, dtype=float),
        bboxes=interpolate_nans(bb),
        chest_dy=np.nan_to_num(np.array(chest, dtype=float)),
        face_cy=interpolate_nans(np.array(face_cy, dtype=float)),
    )
    return out
