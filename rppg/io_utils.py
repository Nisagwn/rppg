"""Video okuma ve veri seti yükleyicileri (UBFC-rPPG, kendi kayıtlarımız)."""
from __future__ import annotations

import csv
import json
import os
from typing import Iterator, List, Optional

import cv2
import numpy as np

from .hr import BPM_GRID, peak_bpm, spectrum_bpm


def video_info(path: str):
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise FileNotFoundError(f"Video açılamadı: {path}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    if fps <= 1 or fps > 240:
        fps = 30.0
    return fps, n, w, h


def iter_frames(path: str, max_frames: Optional[int] = None, resize_width: Optional[int] = None
                ) -> Iterator[np.ndarray]:
    cap = cv2.VideoCapture(path)
    i = 0
    while True:
        ok, f = cap.read()
        if not ok or (max_frames is not None and i >= max_frames):
            break
        if resize_width and f.shape[1] > resize_width:
            s = resize_width / f.shape[1]
            f = cv2.resize(f, (resize_width, int(f.shape[0] * s)), interpolation=cv2.INTER_AREA)
        yield f
        i += 1
    cap.release()


# ----------------------------------------------------------------- UBFC-rPPG
def find_ubfc_subjects(root: str) -> List[str]:
    out = []
    for dirpath, _, files in os.walk(root):
        if "vid.avi" in files and ("ground_truth.txt" in files or "gtdump.xmp" in files):
            out.append(dirpath)
    return sorted(out)


def load_ubfc_gt(subject_dir: str) -> dict:
    """
    DATASET_2: ground_truth.txt -> 1. satır PPG (BVP), 2. satır HR, 3. satır zaman (s)
    DATASET_1: gtdump.xmp (CSV) -> sütunlar: zaman (ms), HR, SpO2, PPG
    """
    p2 = os.path.join(subject_dir, "ground_truth.txt")
    p1 = os.path.join(subject_dir, "gtdump.xmp")
    if os.path.exists(p2):
        with open(p2) as f:
            lines = [l for l in f.read().split("\n") if l.strip()]
        bvp = np.array([float(v) for v in lines[0].split()])
        hr = np.array([float(v) for v in lines[1].split()]) if len(lines) > 1 else None
        t = np.array([float(v) for v in lines[2].split()]) if len(lines) > 2 else None
    elif os.path.exists(p1):
        rows = list(csv.reader(open(p1)))
        arr = np.array([[float(v) for v in r[:4]] for r in rows if len(r) >= 4])
        t, hr, bvp = arr[:, 0] / 1000.0, arr[:, 1], arr[:, 3]
    else:
        raise FileNotFoundError(f"Ground truth bulunamadı: {subject_dir}")
    if t is None or len(t) != len(bvp):
        t = np.arange(len(bvp)) / 30.0
    t = t - t[0]
    return {"bvp": bvp, "t": t, "hr": hr, "source": "ubfc"}


# ------------------------------------------------------------------ MCD-rPPG
def load_mcd_timestamps(meta_path: str) -> np.ndarray:
    """meta/*.txt: her satır 'kare_no  YYYY-MM-DD HH:MM:SS.ffffff' -> saniye (0'dan)."""
    from datetime import datetime
    ts = []
    with open(meta_path) as f:
        for line in f:
            parts = line.split()
            if len(parts) >= 3:
                # tam saniyeye denk gelen karelerde kesir yazılmamış olabilir ('15:07:14')
                fmt = "%Y-%m-%d %H:%M:%S.%f" if "." in parts[2] else "%Y-%m-%d %H:%M:%S"
                ts.append(datetime.strptime(f"{parts[1]} {parts[2]}", fmt).timestamp())
    ts = np.array(ts)
    return ts - ts[0]


def load_mcd_ppg(ppg_sync_path: str) -> np.ndarray:
    """ppg_sync/*.txt: her video karesi için bir satır; 1. sütun PPG (resmi rppglib.load_ppg ile aynı)."""
    with open(ppg_sync_path) as f:
        return np.array([float(l.split()[0]) for l in f if l.strip()])


def load_mcd_item(root: str, video_rel: str, meta_rel: str, ppg_rel: str) -> dict:
    """Video yolu, kare zaman damgaları ve karelere hizalı PPG referansı."""
    ppg = load_mcd_ppg(os.path.join(root, ppg_rel))
    ts = load_mcd_timestamps(os.path.join(root, meta_rel))
    n = min(len(ppg), len(ts))
    return {"video": os.path.join(root, video_rel), "timestamps": ts[:n],
            "gt": {"bvp": ppg[:n], "t": ts[:n], "source": "mcd"}}


# --------------------------------------------------- Kendi kayıtlarımız
def load_recording(rec_dir: str) -> dict:
    """scripts/record_session.py çıktısını yükler."""
    meta = json.load(open(os.path.join(rec_dir, "meta.json"), encoding="utf-8"))
    video = os.path.join(rec_dir, meta["video_file"])
    ts = np.loadtxt(os.path.join(rec_dir, "frames.csv"), delimiter=",", skiprows=1, usecols=1)
    ref_path = os.path.join(rec_dir, "reference.csv")
    gt = None
    if os.path.exists(ref_path):
        ref = np.loadtxt(ref_path, delimiter=",", skiprows=1, ndmin=2)
        if len(ref):
            gt = {"t": ref[:, 0], "hr_inst": ref[:, 1], "source": "reference"}
    return {"meta": meta, "video": video, "timestamps": ts, "gt": gt}


# ------------------------------------------------------ GT pencere HR
def gt_window_hr(gt: dict, centers: np.ndarray, win_sec: float, fs_resample: float = 30.0) -> np.ndarray:
    """Tahmin pencereleriyle aynı merkezlerde referans HR."""
    if "hr_inst" in gt:
        t, h = np.asarray(gt["t"]), np.asarray(gt["hr_inst"])
        if len(t) == 1:
            return np.full(len(centers), h[0])
        out = []
        for c in centers:
            m = (t >= c - win_sec / 2) & (t <= c + win_sec / 2)
            out.append(h[m].mean() if m.any() else np.interp(c, t, h))
        return np.array(out)
    t, bvp = np.asarray(gt["t"]), np.asarray(gt["bvp"], dtype=float)
    grid = np.arange(0, t[-1], 1.0 / fs_resample)
    x = np.interp(grid, t, bvp)
    L = int(win_sec * fs_resample)
    out = []
    for c in centers:
        s = int(round((c - win_sec / 2) * fs_resample))
        s = max(0, min(s, len(x) - L))
        out.append(peak_bpm(BPM_GRID, spectrum_bpm(x[s:s + L], fs_resample)))
    return np.array(out)
