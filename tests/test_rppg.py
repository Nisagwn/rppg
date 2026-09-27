"""Birim ve uçtan uca testler:  python -m pytest -q"""
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from rppg.filtering import bandpass, detrend_tarvainen, resample_uniform  # noqa: E402
from rppg.hr import BPM_GRID, OnlineHRTracker, hr_fft, snr_db, spectrogram, viterbi_track  # noqa: E402
from rppg.methods import METHODS  # noqa: E402
from rppg.metrics import bland_altman, mae, pearson  # noqa: E402
from rppg.pipeline import Config, estimate  # noqa: E402
from rppg.roi import FaceTracker, skin_mask  # noqa: E402
from rppg.signals import extract_traces  # noqa: E402
from rppg.synthetic import make_scenario  # noqa: E402

FS = 30.0


def synth_rgb(hr=75.0, n=900, illum=0.0, seed=0):
    """Nabız + (opsiyonel) beyaz ışık dalgalanması içeren RGB izi."""
    rng = np.random.default_rng(seed)
    t = np.arange(n) / FS
    pulse = np.sin(2 * np.pi * hr / 60 * t)
    base = np.array([200.0, 150.0, 120.0])
    pv = np.array([0.33, 0.77, 0.53])
    light = 1 + illum * np.sin(2 * np.pi * 1.9 * t + 0.3)     # 114 BPM'de bozucu
    rgb = base * (1 + 0.003 * pv * pulse[:, None]) * light[:, None]
    return rgb + rng.normal(0, 0.05, rgb.shape)


@pytest.mark.parametrize("name", list(METHODS))
def test_methods_recover_hr_clean(name):
    rgb = synth_rgb(78.0)
    bvp = METHODS[name](rgb, FS)
    assert abs(hr_fft(bandpass(bvp, FS, 0.7, 3.5), FS) - 78.0) < 2.0


@pytest.mark.parametrize("name", ["chrom", "pos", "lgi"])
def test_chrominance_methods_reject_white_illumination(name):
    rgb = synth_rgb(72.0, illum=0.01)          # bozucu, nabızdan ~4 kat güçlü
    bvp = METHODS[name](rgb, FS)
    assert abs(hr_fft(bandpass(bvp, FS, 0.7, 3.5), FS) - 72.0) < 2.0


def test_green_fails_under_white_illumination():
    rgb = synth_rgb(72.0, illum=0.01)
    bvp = METHODS["green"](rgb, FS)
    assert abs(hr_fft(bandpass(bvp, FS, 0.7, 3.5), FS) - 72.0) > 10.0


def test_detrend_removes_slow_drift():
    t = np.arange(900) / FS
    x = np.sin(2 * np.pi * 1.2 * t) + 5 * t / t[-1]
    y = detrend_tarvainen(x, 100)
    assert abs(np.polyfit(t, y, 1)[0]) < 0.05


def test_snr_higher_for_clean_signal():
    t = np.arange(900) / FS
    clean = np.sin(2 * np.pi * 1.25 * t)
    noisy = clean + np.random.default_rng(0).normal(0, 2, len(t))
    assert snr_db(clean, FS) > snr_db(noisy, FS) + 5


def test_viterbi_ignores_single_window_spike():
    t = np.arange(int(60 * FS)) / FS
    x = np.sin(2 * np.pi * 1.3 * t)
    centers, S = spectrogram(x, FS, 10, 1)
    S = S.copy()
    spike = np.exp(-0.5 * ((BPM_GRID - 150) / 1.0) ** 2)
    S[25] = spike / spike.sum()                     # tek pencerede sahte tepe
    path = viterbi_track(S, BPM_GRID, 1.0, 4.0)
    assert abs(path[25] - 78) < 3
    argmax = BPM_GRID[np.argmax(S, 1)]
    assert abs(argmax[25] - 150) < 1


def test_online_tracker_converges():
    tr = OnlineHRTracker()
    p = np.exp(-0.5 * ((BPM_GRID - 88) / 2) ** 2)
    for _ in range(10):
        est = tr.update(p / p.sum(), 0.5)
    assert abs(est - 88) < 1


def test_resample_uniform():
    ts = np.cumsum(np.r_[0, np.random.default_rng(1).uniform(0.025, 0.042, 299)])
    grid, y = resample_uniform(np.sin(ts), ts, 30.0)
    assert np.allclose(y, np.sin(grid), atol=1e-2)


def test_metrics():
    e, r = np.array([70, 80, 90.0]), np.array([72, 78, 91.0])
    assert mae(e, r) == pytest.approx(5 / 3)
    assert pearson(e, r) > 0.9
    assert bland_altman(e, r)["bias"] == pytest.approx(-1 / 3)


def test_skin_mask_detects_skin_color():
    patch = np.zeros((20, 20, 3), np.uint8)
    patch[:, :10] = (120, 150, 200)    # cilt (BGR)
    patch[:, 10:] = (200, 60, 30)      # mavi arka plan
    m = skin_mask(patch)
    assert m[:, :8].mean() > 200 and m[:, 12:].mean() < 20


@pytest.mark.slow
def test_end_to_end_synthetic_occlusion():
    v = make_scenario("occlusion", seed=0, duration=25)
    tr = extract_traces(v.frames(), v.cfg.fps, FaceTracker(use_haar=False, initial_bbox=v.face_bbox()))
    from rppg.io_utils import gt_window_hr
    good = estimate(tr, Config("pos", ("forehead", "left_cheek", "right_cheek"), "snr", "viterbi"))
    bad = estimate(tr, Config("pos", ("forehead",), "mean", "argmax", False))
    ref = gt_window_hr(v.ground_truth(), good.centers, 10)
    assert mae(good.hr, ref) < 3.0
    assert mae(bad.hr, ref) > mae(good.hr, ref)
    # SNR füzyonu alın ağırlığını düşürmeli
    fi = good.roi_names.index("forehead")
    assert good.roi_weights[:, fi].mean() < 0.2


def test_soft_mask_resists_illumination_flicker_at_threshold():
    """Eşik sınırında renkleri olan yüzeyde ikili maske ışık titremesine kilitlenir,
    yumuşak maske kilitlenmez (Özgün katkı 4)."""
    from rppg.signals import TraceExtractor
    H = W = 120
    img = np.zeros((H, W, 3), np.float32)
    # Sol yarı: normal cilt. Sağ yarı: rengi ciltten farklı, parlaklığı (Y) alt eşiği (40)
    # kesen koyu kırmızımsı bölge (gölge/saç kenarı gibi). Işık titremesi bu pikselleri
    # ikili maskeye sokup çıkarır -> ortalamanın RENGİ titreme frekansında değişir.
    img[:, :W // 2] = (120, 150, 200)
    for x in range(W // 2, W):
        img[:, x] = np.array([30, 32, 60]) * (0.8 + 0.4 * (x - W // 2) / (W // 2))
    img += np.random.default_rng(0).normal(0, 2, img.shape).astype(np.float32)
    n, hr, f_il = 600, 72.0, 1.75
    t = np.arange(n) / FS
    pv = np.array([0.53, 0.77, 0.33], np.float32)
    res = {}
    for mode in ["binary", "soft"]:
        rng = np.random.default_rng(1)
        ex = TraceExtractor(FaceTracker(use_haar=False, initial_bbox=(0, 0, W, H)), ["full"],
                            respiration=False, mask_mode=mode)
        rgb = []
        for i in range(n):
            f = img * (1 + 0.003 * pv * np.sin(2 * np.pi * hr / 60 * t[i])) * (1 + 0.01 * np.sin(2 * np.pi * f_il * t[i]))
            f = np.clip(f + rng.normal(0, 1, f.shape), 0, 255).astype(np.uint8)
            rgb.append(ex.process(f)[2]["full"])
        bvp = METHODS["pos"](np.array(rgb), FS)
        res[mode] = hr_fft(bandpass(bvp, FS, 0.7, 3.5), FS)
    assert abs(res["soft"] - hr) < 3
    assert abs(res["binary"] - f_il * 60) < 3


def test_haar_cascade_available():
    """OpenCV 5 CascadeClassifier'ı kaldırdı; requirements <5 sabitlemesinin çalıştığını doğrular."""
    import cv2
    assert hasattr(cv2, "CascadeClassifier"), "opencv-python<5 kurulmalı"
    t = FaceTracker()
    assert not t.cascade.empty()


def test_mcd_loader_aligns_ppg_with_frame_timestamps(tmp_path):
    """MCD-rPPG biçimi: meta'da kare zaman damgası, ppg_sync'te kare başına PPG; referans HR doğru çıkmalı."""
    from datetime import datetime, timedelta

    from rppg.io_utils import gt_window_hr, load_mcd_item
    n, fps, hr = 24 * 40, 24.0, 72.0
    t0 = datetime(2023, 11, 13, 14, 10, 51, 689451)
    (tmp_path / "meta").mkdir()
    (tmp_path / "ppg_sync").mkdir()
    with open(tmp_path / "meta" / "x.txt", "w") as f:
        for i in range(n + 11):  # meta'da kareden birkaç satır fazla olabiliyor
            f.write(f"{i + 1}  {t0 + timedelta(seconds=i / fps)}\n")
    ppg = 128 + 20 * np.sin(2 * np.pi * hr / 60 * np.arange(n) / fps)
    with open(tmp_path / "ppg_sync" / "x.txt", "w") as f:
        for v in ppg:
            f.write(f"{int(v)} 0.005\n")
    item = load_mcd_item(str(tmp_path), "video/x.avi", "meta/x.txt", "ppg_sync/x.txt")
    assert len(item["timestamps"]) == n and item["timestamps"][0] == 0
    assert abs(item["timestamps"][-1] - (n - 1) / fps) < 1e-3
    ref = gt_window_hr(item["gt"], np.array([10.0, 20.0, 30.0]), 10.0)
    assert np.all(np.abs(ref - hr) < 2)
