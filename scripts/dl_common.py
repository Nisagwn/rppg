"""Derin öğrenme betikleri için ortak parçalar: rPPG-Toolbox FactorizePhys modeli, çıkarım, HR tahmini."""
import os
import sys
import types

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TOOLBOX = os.path.join(ROOT, "external", "rPPG-Toolbox")
sys.path.insert(0, ROOT)
sys.path.insert(0, TOOLBOX)
sys.modules.setdefault("neurokit2", types.ModuleType("neurokit2"))  # FSAM.py içe aktarıyor, kullanmıyor

from rppg.filtering import preprocess_bvp  # noqa: E402
from rppg.hr import BPM_GRID, argmax_track, spectrogram, viterbi_track  # noqa: E402
from rppg.io_utils import gt_window_hr  # noqa: E402

CHUNK = 160
PRETRAINED = os.path.join(TOOLBOX, "final_model_release", "PURE_FactorizePhys_FSAM_Res.pth")
MD_CONFIG = {"FRAME_NUM": CHUNK, "MD_TYPE": "NMF", "MD_FSAM": True, "MD_TRANSFORM": "T_KAB",
             "MD_S": 1, "MD_R": 1, "MD_STEPS": 4, "MD_INFERENCE": True, "MD_RESIDUAL": True}


def build_model(device, weights=PRETRAINED, dropout=0.1):
    import torch
    from neural_methods.model.FactorizePhys.FactorizePhys import FactorizePhys
    model = FactorizePhys(frames=CHUNK, md_config=dict(MD_CONFIG), in_channels=3, dropout=dropout, device=device)
    if weights:
        sd = torch.load(weights, map_location=device)
        sd = sd.get("model", sd)
        sd = {k.removeprefix("module."): v for k, v in sd.items()}
        missing, unexpected = model.load_state_dict(sd, strict=False)
        if missing or unexpected:
            print(f"  ağırlık uyarısı: eksik {len(missing)}, fazla {len(unexpected)}")
    return model.to(device)


def to_input(frames_uint8, device):
    """[B,T,72,72,3] uint8 -> [B,3,T+1,72,72] float (toolbox: son kare tekrarlanır, model içinde diff alınır)."""
    import torch
    x = torch.as_tensor(np.ascontiguousarray(frames_uint8), device=device).float()
    x = x.permute(0, 4, 1, 2, 3)
    return torch.cat([x, x[:, :, -1:]], dim=2)


def chunk_starts(n, hop):
    """hop adımlı 160 karelik parça başlangıçları; son parça videonun sonuna hizalanır."""
    starts = list(range(0, n - CHUNK + 1, hop))
    if starts[-1] + CHUNK < n:
        starts.append(n - CHUNK)
    return starts


# Örtüşmeli birleştirme penceresi: parça ortasına ağırlık verir, sınırdaki (modelin bağlamı kısa) kareleri
# komşu parçaya bırakır. Mobil uygulamayla aynı (mobile/app.js dlAddBvp: sin²(π(i+0.5)/T), DL_HOP = 80);
# yarım örnek kayması sayesinde uçlarda sıfır olmaz, videonun ilk/son karelerinde 0/0 oluşmaz.
_BLEND = (np.sin(np.pi * (np.arange(CHUNK) + 0.5) / CHUNK) ** 2).astype(np.float32)


def predict_video(model, frames, device, batch=4, hop=CHUNK, flip=False):
    """Tüm video için BVP.

    hop=CHUNK (varsayılan, eski davranış): ardışık 160 karelik parçalar; son parça sona hizalanıp eksik kısmı alınır.
    hop<CHUNK: örtüşmeli parçalar Hann ağırlıklı ortalamayla birleştirilir; parça sınırlarındaki süreksizlik
    (her parça ayrı normalize edilir, kenarlarda modelin zamansal bağlamı kısadır) yumuşar. ör. hop=80 -> %50 örtüşme.
    flip=True: kareler yatay çevrilerek de tahmin alınır ve iki çıktı ortalanır (test zamanı artırma; eğitimde
    yatay çevirme artırması kullanıldığı için model iki yönde de geçerli).
    """
    import torch
    n = len(frames)
    if n < CHUNK:
        return None
    hop = int(max(1, min(hop, CHUNK)))
    starts = chunk_starts(n, hop)
    out = np.zeros(n, dtype=np.float32)
    wsum = np.zeros(n, dtype=np.float32)
    model.eval()
    with torch.no_grad():
        for i in range(0, len(starts), batch):
            ss = starts[i:i + batch]
            clips = np.stack([frames[s:s + CHUNK] for s in ss])
            y = model(to_input(clips, device))[0].float().cpu().numpy()
            if flip:
                y = _znorm(y) + _znorm(model(to_input(clips[:, :, :, ::-1], device))[0].float().cpu().numpy())
            for s, yy in zip(ss, _znorm(y)):
                if hop < CHUNK:
                    out[s:s + CHUNK] += yy * _BLEND
                    wsum[s:s + CHUNK] += _BLEND
                elif s % CHUNK:  # sona hizalı son parça: yalnızca önceki parçaların kapsamadığı kısım
                    done = (n // CHUNK) * CHUNK
                    out[done:] = yy[done - s:]
                else:
                    out[s:s + CHUNK] = yy
    return out / wsum if hop < CHUNK else out


def _znorm(y):
    """Parça başına (son eksen) sıfır ortalama, birim varyans."""
    return (y - y.mean(-1, keepdims=True)) / (y.std(-1, keepdims=True) + 1e-8)


def hr_from_bvp(bvp, fs=30.0, win=10.0, step=1.0):
    x = preprocess_bvp(bvp, fs)
    centers, S = spectrogram(x, fs, win, step)
    return centers, argmax_track(S, BPM_GRID), viterbi_track(S, BPM_GRID, step)


def reference_hr(label, centers, fs=30.0, win=10.0):
    t = np.arange(len(label)) / fs
    return gt_window_hr({"bvp": label, "t": t}, centers, win, fs)


QWIN, QSTEP = 10.0, 2.0  # kalite pencereleri (s)


def label_quality(frames, bvp, fs=30.0):
    """Etiket (sensör) kalitesi: yalnızca etiketten ve etiket-video uyumundan ölçütler.

    Pencere başına (10 s, 2 s adım):
      * hr_l, snr_l: etiketin nabzı ve SNR'ı (temel ±6 + 1. harmonik ±12 BPM / geri kalan, dB)
      * hr_p: yüz kırpıntısının ortasında POS ile videodan bulunan nabız (referanstan bağımsız)
    Video düzeyi:
      * lag_r: POS ile etiket arasındaki çapraz korelasyon, gecikme -30..30 kare (±1 s); POS modelin kuralına göre
        ters işaretli çıkar, bu yüzden -POS kullanılır: doğru işaretli ve senkron etikette r(0) yüksek ve pozitif.
    Döndürülen frame_ok: karenin ait olduğu pencerelerin çoğunda etiket iyi mi (sampler parçaları buna göre seçer).
    """
    from rppg.hr import SNR_GRID, spectrum_bpm, window_snr_from_spectrum, window_starts
    from rppg.methods import pos
    frames = np.asarray(frames)
    rgb = frames[:, 15:57, 15:57].reshape(len(frames), -1, 3).mean(axis=1).astype(float)
    lab = preprocess_bvp(np.asarray(bvp, dtype=float), fs)
    vid = -preprocess_bvp(pos(rgb, fs), fs)
    starts, L, centers = window_starts(len(lab), fs, QWIN, QSTEP)
    band = (SNR_GRID >= BPM_GRID[0]) & (SNR_GRID <= BPM_GRID[-1])
    hr_l, snr_l, hr_p = [], [], []
    for s in starts:
        p = spectrum_bpm(lab[s:s + L], fs, SNR_GRID)
        h = float(SNR_GRID[band][np.argmax(p[band])])
        hr_l.append(h)
        snr_l.append(window_snr_from_spectrum(SNR_GRID, p, h))
        q = spectrum_bpm(vid[s:s + L], fs, SNR_GRID)
        hr_p.append(float(SNR_GRID[band][np.argmax(q[band])]))
    hr_l, snr_l, hr_p = map(np.array, (hr_l, snr_l, hr_p))
    med = np.array([np.median(hr_l[max(0, i - 3):i + 4]) for i in range(len(hr_l))])
    win_ok = (snr_l >= SNR_MIN) & (hr_l >= 40) & (hr_l <= 180) & (np.abs(hr_l - med) <= 12)
    votes, cover = np.zeros(len(lab)), np.zeros(len(lab))
    for s, ok in zip(starts, win_ok):
        votes[s:s + L] += ok
        cover[s:s + L] += 1
    frame_ok = votes >= 0.5 * np.maximum(cover, 1)
    a, b = vid[20:-20], lab[20:-20]
    lags = np.arange(-30, 31)
    r = np.array([np.corrcoef(np.roll(a, k), b)[0, 1] for k in lags])
    near = np.abs(lags) <= 4
    agree = np.abs(hr_l - hr_p) <= 5
    return {
        "frame_ok": frame_ok, "win_ok": win_ok, "hr_l": hr_l, "snr_l": snr_l, "hr_p": hr_p,
        "ok_frac": float(frame_ok.mean()), "snr_med": float(np.median(snr_l)),
        "agree_frac": float(agree.mean()), "agree_ok_frac": float(agree[win_ok].mean()) if win_ok.any() else 0.0,
        "r0": float(r[near][np.argmax(np.abs(r[near]))]), "lag_best": int(lags[np.argmax(np.abs(r))]),
        "r_best": float(r[np.argmax(np.abs(r))]), "r_lags": r,
        "lag_pos": int(lags[np.argmax(r)]), "r_pos": float(r.max()),
    }


SNR_MIN = 0.0  # dB

# Etiket-video zaman hizası (dl_quality.py raporu, 2026-10-02). label_quality.r_lags kuralında (r[k] = corr(-POS
# kaydırılmış k, etiket)) UBFC/PURE/MCD önden webcam tepesi k ~ -2 (parmak nabzı yüzden ~70-100 ms sonra gelir;
# test etiketleri de böyle). MCD yan kameraları sabit gecikmeli: 150'şer videonun ortalama korelasyon eğrisi
# önden webcam'e göre Iriun (telefon, Wi-Fi) 4 kare, USB 8 kare (~270 ms; ~yarım nabız periyodu, etiket fiilen
# ters) kayık. Bu kaydırmalar etiketi önden webcam hizasına getirir (bkz. shift_label).
REF_LAG = -2
CAMERA_SHIFT = {("mcd", "IriunWebcam"): 4, ("mcd", "USBVideo"): 8}
PER_VIDEO_SYNC = {"ubfcphys"}  # bilek sensörü; senkron kişiden kişiye değişiyor -> video başına hizalama


def shift_label(b, d):
    """b'[t] = b[t - d] (d > 0: etiketi geciktir); kenarlar uç değerle doldurulur."""
    if d == 0:
        return b
    if d > 0:
        return np.concatenate([np.full(d, b[0]), b[:-d]])
    return np.concatenate([b[-d:], np.full(-d, b[-1])])


def label_shift(q, source, camera):
    """Etiketi video ile hizalamak için shift_label'a verilecek kaydırma (kare)."""
    if source in PER_VIDEO_SYNC and q is not None:
        return -(q["lag_pos"] - REF_LAG)
    return CAMERA_SHIFT.get((source, camera), 0)


def video_decision(q, source):
    """Video eğitimde kalsın mı. Etiketin yarısından fazlası kötüyse (düşük SNR, imkânsız/sıçrayan nabız) çıkar.
    Video başına hizalanan kaynaklarda (UBFC-Phys) ayrıca hizalı korelasyon zayıfsa çıkar: etiket görüntüyle
    örtüşmüyor. POS'un nabız uyumu karar için kullanılmaz: MCD yan kameralarında POS başarısız (aynı oturumun
    önden POS'uyla %22-28 uyum) ama etiket doğru; ölçüt zor ama geçerli videoları atardı."""
    if q["ok_frac"] < 0.5:
        return False
    if source in PER_VIDEO_SYNC:
        return q["r_pos"] >= 0.4
    return True
