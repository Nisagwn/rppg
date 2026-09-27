"""
ÖZGÜN KATKI 3 — Kontrollü zorluk senaryolu sentetik yüz videosu üreteci.

Gerçek veri setleri (UBFC vb.) zorlukları birbirine karışmış hâlde içerir;
hangi yöntemin hangi zorluğa dayanıklı olduğunu ayırmak zordur. Bu üreteç,
bilinen (ground truth) HR ve solunum hızıyla, zorlukları TEK TEK açıp
kapatabildiğimiz yüz videoları üretir:

  noise         : kamera sensör gürültüsü (Gauss)
  illum         : nabız bandına düşen global beyaz ışık dalgalanması
  compression   : JPEG sıkıştırma (MJPG webcam akışı gibi) — ince renk farklarını siler
  motion        : baş ötelemesi + hıza bağlı speküler parlama
  occlusion     : alnı örten saç (nabız taşımayan bölge)
  screen_light  : tüm sahneye vuran renkli (mavimsi) monitör ışığı titremesi
  local_flicker : tek yanağa vuran renkli (mavimsi) ekran ışığı titremesi

Fizyolojik model (basitleştirilmiş, Wang vd. 2017):
  C(x,t) = u_c · I0(x) · (1 + a · g(x) · p_c · pulse(t)) · L(t) + spec(t) + n
  p_c    = [0.33, 0.77, 0.53]  (R, G, B göreli nabız genliği — yeşil baskın)
  g(x)   : bölgesel perfüzyon haritası (yanaklar güçlü, burun zayıf)
Kareler uint8'e nicemlenir; nabız genliği ~0.5 gri seviyesinin altındadır,
yani tek pikselde görünmez, ancak uzamsal ortalama ile ortaya çıkar.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterator, Tuple

import cv2
import numpy as np

PULSE_VEC = np.array([0.33, 0.77, 0.53])  # R, G, B


@dataclass
class SynthConfig:
    duration: float = 60.0
    fps: float = 30.0
    width: int = 320
    height: int = 240
    hr_start: float = 72.0
    hr_end: float = 96.0
    hr_wiggle: float = 4.0
    rr_bpm: float = 15.0
    pulse_amp: float = 0.0018
    noise_std: float = 1.0
    illum_amp: float = 0.0
    motion_amp: float = 0.0
    specular: float = 0.0
    occlusion: bool = False
    local_flicker: float = 0.0
    screen_light: float = 0.0
    jpeg_quality: int = 0          # >0 ise her kare JPEG ile sıkıştırılır (MJPG webcam gibi)
    breath_head: float = 0.6       # nefesle baş dikey hareketi (piksel)
    seed: int = 0
    skin_bgr: Tuple[int, int, int] = (120, 150, 200)
    extra: dict = field(default_factory=dict)


SCENARIOS = {
    "ideal": dict(),
    "noise": dict(noise_std=6.0),
    "illum": dict(illum_amp=0.012, noise_std=2.0),
    "screen_light": dict(screen_light=0.012, noise_std=2.0),
    "compression": dict(jpeg_quality=70, noise_std=2.0),
    "motion": dict(motion_amp=8.0, specular=10.0, noise_std=2.0),
    "occlusion": dict(occlusion=True, noise_std=3.0),
    "local_flicker": dict(local_flicker=0.08, noise_std=3.0),
    "hard": dict(noise_std=5.0, illum_amp=0.008, screen_light=0.005, motion_amp=6.0, specular=8.0,
                 occlusion=True, local_flicker=0.08, jpeg_quality=75),
}

SCENARIO_NAMES_TR = {
    "ideal": "İdeal", "noise": "Sensör gürültüsü", "illum": "Beyaz ışık dalgalanması", "screen_light": "Renkli ekran ışığı (global)",
    "compression": "JPEG sıkıştırma (q=70)", "motion": "Baş hareketi", "occlusion": "Saç örtmesi (alın)",
    "local_flicker": "Yanakta renkli titreme", "hard": "Hepsi birden",
}


def _bandlimited_noise(n, fs, lo, hi, rng):
    from scipy import signal as sps
    x = rng.standard_normal(n + 200)
    sos = sps.butter(2, [lo, min(hi, 0.45 * fs)], btype="bandpass", fs=fs, output="sos")
    y = sps.sosfiltfilt(sos, x)[100:100 + n]
    return y / (y.std() + 1e-12)


def _ppg_wave(phase):
    """Sistolik tepe + dikrotik çentik benzeri dalga biçimi (birim std)."""
    w = np.sin(phase) + 0.45 * np.sin(2 * phase - 0.9) + 0.15 * np.sin(3 * phase - 1.8)
    return (w - w.mean()) / (w.std() + 1e-12)


class SyntheticVideo:
    def __init__(self, cfg: SynthConfig):
        self.cfg = cfg
        c = cfg
        rng = np.random.default_rng(c.seed)
        self.n = int(c.duration * c.fps)
        t = np.arange(self.n) / c.fps
        self.t = t
        # --- ground truth HR (yavaş değişen) ve BVP
        trend = np.linspace(c.hr_start, c.hr_end, self.n)
        wig = c.hr_wiggle * _bandlimited_noise(self.n, c.fps, 0.01, 0.08, rng) if c.hr_wiggle > 0 else 0
        self.hr = trend + wig
        phase = 2 * np.pi * np.cumsum(self.hr / 60.0) / c.fps
        self.pulse = _ppg_wave(phase)
        # --- solunum
        rr_phase = 2 * np.pi * np.cumsum(np.full(self.n, c.rr_bpm / 60.0)) / c.fps
        self.resp = np.sin(rr_phase)
        # --- global aydınlatma ve yerel titreme
        self.illum = 1.0 + c.illum_amp * _bandlimited_noise(self.n, c.fps, 0.7, 3.0, rng) if c.illum_amp else np.ones(self.n)
        self.flicker = _bandlimited_noise(self.n, c.fps, 0.9, 2.5, rng) if c.local_flicker else np.zeros(self.n)
        self.screen = _bandlimited_noise(self.n, c.fps, 0.8, 2.5, rng) if c.screen_light else np.zeros(self.n)
        # --- hareket (düşük frekanslı + ani sarsıntılar)
        if c.motion_amp > 0:
            mx = c.motion_amp * (0.6 * np.sin(2 * np.pi * 0.23 * t) + 0.4 * _bandlimited_noise(self.n, c.fps, 0.05, 1.5, rng))
            my = 0.6 * c.motion_amp * (0.6 * np.sin(2 * np.pi * 0.17 * t + 1.0) + 0.4 * _bandlimited_noise(self.n, c.fps, 0.05, 1.5, rng))
        else:
            mx = np.zeros(self.n)
            my = np.zeros(self.n)
        self.mx = mx
        self.my = my + c.breath_head * self.resp  # nefesle baş hafif iner-kalkar
        speed = np.hypot(np.gradient(mx), np.gradient(my)) * c.fps
        self.spec = c.specular * speed / (speed.max() + 1e-9) if c.specular else np.zeros(self.n)
        self.rng = rng
        self._build_layers()

    # --------------------------------------------------------------------
    def _build_layers(self):
        c, rng = self.cfg, self.rng
        W, H = c.width, c.height
        pad = 40
        self.pad = pad
        CW, CH = W + 2 * pad, H + 2 * pad
        yy, xx = np.mgrid[0:CH, 0:CW].astype(np.float32)
        # arka plan: yumuşak gradyan + doku
        bg = np.zeros((CH, CW, 3), np.float32)
        bg[..., 0] = 70 + 30 * xx / CW
        bg[..., 1] = 80 + 20 * yy / CH
        bg[..., 2] = 90
        bg += cv2.GaussianBlur(rng.normal(0, 6, (CH, CW, 3)).astype(np.float32), (0, 0), 2)
        self.bg = bg
        # yüz: elips
        fcx, fcy = pad + W * 0.5, pad + H * 0.46
        ax, ay = W * 0.17, H * 0.29
        face = (((xx - fcx) / ax) ** 2 + ((yy - fcy) / ay) ** 2) <= 1.0
        face_m = cv2.GaussianBlur(face.astype(np.float32), (0, 0), 1.2)
        tex = 1.0 + cv2.GaussianBlur(rng.normal(0, 0.06, (CH, CW)).astype(np.float32), (0, 0), 1.5)
        base = np.stack([np.full((CH, CW), v, np.float32) for v in c.skin_bgr], -1) * tex[..., None]
        # gölgelendirme (kenarlara doğru koyulaşma)
        r2 = ((xx - fcx) / ax) ** 2 + ((yy - fcy) / ay) ** 2
        base *= (1.0 - 0.25 * np.clip(r2, 0, 1))[..., None]
        # perfüzyon haritası g(x)
        g = np.full((CH, CW), 1.0, np.float32)
        for (cx, cy, s, amp) in [(fcx - 0.5 * ax, fcy + 0.25 * ay, 0.35 * ax, 0.5),
                                 (fcx + 0.5 * ax, fcy + 0.25 * ay, 0.35 * ax, 0.5),
                                 (fcx, fcy - 0.6 * ay, 0.5 * ax, 0.2),
                                 (fcx, fcy + 0.05 * ay, 0.2 * ax, -0.4)]:
            g += amp * np.exp(-(((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * s * s)))
        # yüz özellikleri: kaşlar, gözler, burun deliği, ağız (nabız taşımaz)
        feat = np.zeros((CH, CW), np.uint8)
        for sx in (-1, 1):
            cv2.ellipse(feat, (int(fcx + sx * 0.42 * ax), int(fcy - 0.18 * ay)), (int(0.22 * ax), int(0.07 * ay)), 0, 0, 360, 255, -1)
            cv2.ellipse(feat, (int(fcx + sx * 0.42 * ax), int(fcy - 0.36 * ay)), (int(0.26 * ax), int(0.03 * ay)), 0, 0, 360, 255, -1)
        cv2.ellipse(feat, (int(fcx), int(fcy + 0.52 * ay)), (int(0.35 * ax), int(0.06 * ay)), 0, 0, 360, 255, -1)
        feat_m = cv2.GaussianBlur(feat.astype(np.float32) / 255, (0, 0), 1.0)
        dark = np.array([18, 20, 28], np.float32)
        # saç (her zaman üstte) + senaryoya göre alnı örten perçem
        hair = ((((xx - fcx) / (ax * 1.12)) ** 2 + ((yy - fcy + 0.08 * ay) / (ay * 1.12)) ** 2) <= 1.0) & (yy < fcy - 0.72 * ay)
        if c.occlusion:
            hair |= face & (yy < fcy - 0.40 * ay)
        hair_m = cv2.GaussianBlur(hair.astype(np.float32), (0, 0), 1.0)
        hair_tex = np.array([30, 35, 45], np.float32) * (1 + cv2.GaussianBlur(rng.normal(0, 0.3, (CH, CW)).astype(np.float32), (0, 0), 0.8))[..., None]
        # gövde / göğüs (solunumla hareket eden ayrı katman)
        body = (yy > fcy + 1.05 * ay) & (np.abs(xx - fcx) < 1.6 * ax + (yy - fcy - ay) * 0.6)
        body_m = cv2.GaussianBlur(body.astype(np.float32), (0, 0), 1.5)
        shirt = np.array([140, 90, 60], np.float32) * (1 + cv2.GaussianBlur(rng.normal(0, 0.15, (CH, CW)).astype(np.float32), (0, 0), 1.2))[..., None]
        # stripes for optical flow texture
        shirt *= (1 + 0.15 * np.sin(yy / 3.0))[..., None]

        self.face_m = face_m * (1 - feat_m) * (1 - hair_m)   # nabız taşıyan cilt
        self.face_base = base
        self.g = g
        self.feat_layer = (feat_m[..., None] * dark + hair_m[..., None] * hair_tex)
        self.feat_alpha = np.clip(face_m * feat_m + hair_m, 0, 1)
        self.body_m, self.shirt = body_m, shirt
        # yerel titreme maskesi: sağ yanak (görüntünün sağ tarafı)
        fl = np.exp(-(((xx - (fcx + 0.5 * ax)) ** 2 + (yy - (fcy + 0.25 * ay)) ** 2) / (2 * (0.45 * ax) ** 2)))
        self.flicker_m = (fl * face_m).astype(np.float32)
        self.fcx, self.fcy, self.ax, self.ay = fcx, fcy, ax, ay

    def face_bbox(self) -> Tuple[float, float, float, float]:
        """Haar benzeri başlangıç kutusu (görüntü koordinatlarında)."""
        w = 2.05 * self.ax
        h = 1.75 * self.ay
        x = self.fcx - self.pad - w / 2
        y = self.fcy - self.pad - 0.85 * self.ay
        return (x, y, w, h)

    def _shift(self, img, dx, dy):
        M = np.float32([[1, 0, dx], [0, 1, dy]])
        return cv2.warpAffine(img, M, (img.shape[1], img.shape[0]), flags=cv2.INTER_LINEAR,
                              borderMode=cv2.BORDER_REFLECT)

    def frames(self) -> Iterator[np.ndarray]:
        c = self.cfg
        pad, W, H = self.pad, c.width, c.height
        pv = PULSE_VEC[::-1].astype(np.float32)  # BGR sırası
        flick_col = np.array([1.6, 0.9, 0.5], np.float32)  # mavimsi ekran ışığı (BGR)
        for i in range(self.n):
            mod = 1.0 + c.pulse_amp * self.g[..., None] * pv * self.pulse[i]
            skin = self.face_base * mod
            if c.local_flicker:
                skin = skin * (1.0 + c.local_flicker * self.flicker[i] * self.flicker_m[..., None] * flick_col)
            # katmanları birleştir: arka plan <- gövde <- yüz <- özellikler
            body_dy = 1.8 * self.resp[i]
            bm = self._shift(self.body_m, self.mx[i] * 0.5, body_dy)
            sh = self._shift(self.shirt, self.mx[i] * 0.5, body_dy)
            img = self.bg * (1 - bm[..., None]) + sh * bm[..., None]
            fm = self._shift(self.face_m, self.mx[i], self.my[i])
            sk = self._shift(skin, self.mx[i], self.my[i])
            fa = self._shift(self.feat_alpha, self.mx[i], self.my[i])
            fl = self._shift(self.feat_layer, self.mx[i], self.my[i])
            face_any = np.clip(fm + fa, 0, 1)
            img = img * (1 - face_any[..., None]) + sk * fm[..., None] + fl
            img = img * self.illum[i]
            if c.screen_light:
                img = img * (1.0 + c.screen_light * self.screen[i] * flick_col)
            if self.spec[i] > 0:
                img = img + self.spec[i] * fm[..., None]
            img = img[pad:pad + H, pad:pad + W]
            if c.noise_std > 0:
                img = img + self.rng.normal(0, c.noise_std, img.shape).astype(np.float32)
            out = np.clip(img + 0.5, 0, 255).astype(np.uint8)
            if c.jpeg_quality:
                ok, buf = cv2.imencode(".jpg", out, [cv2.IMWRITE_JPEG_QUALITY, int(c.jpeg_quality)])
                out = cv2.imdecode(buf, cv2.IMREAD_COLOR)
            yield out

    def ground_truth(self) -> dict:
        return {"t": self.t, "hr_inst": self.hr, "bvp": self.pulse, "rr_bpm": self.cfg.rr_bpm,
                "source": "synthetic"}


def make_scenario(name: str, seed: int = 0, **overrides) -> SyntheticVideo:
    kw = dict(SCENARIOS[name])
    kw.update(overrides)
    rng = np.random.default_rng(1000 + seed)
    kw.setdefault("hr_start", float(rng.uniform(62, 80)))
    kw.setdefault("hr_end", float(kw["hr_start"] + rng.uniform(10, 30)))
    kw.setdefault("rr_bpm", float(rng.uniform(11, 19)))
    return SyntheticVideo(SynthConfig(seed=seed, **kw))


def write_video(vid: SyntheticVideo, path: str, codec: str = "FFV1"):
    c = vid.cfg
    fourcc = cv2.VideoWriter_fourcc(*codec)
    w = cv2.VideoWriter(path, fourcc, c.fps, (c.width, c.height))
    if not w.isOpened():
        w = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*"MJPG"), c.fps, (c.width, c.height))
    for f in vid.frames():
        w.write(f)
    w.release()
