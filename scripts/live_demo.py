#!/usr/bin/env python
"""
Canlı demo: webcam'den gerçek zamanlı nabız, solunum ve EVM görselleştirme.

    python scripts/live_demo.py                 # varsayılan kamera
    python scripts/live_demo.py --camera 1      # ikinci kamera
    python scripts/live_demo.py --video data/ornek.avi          # dosyadan
    python scripts/live_demo.py --video x.avi --headless --save out.mp4

Tuşlar:
    e : EVM (renk büyütme) aç/kapat — yüzün nabızla kızarıp solduğunu gösterir
    m : cilt maskesini göster/gizle
    r : takipçiyi sıfırla
    s : ekran görüntüsü kaydet (results/screenshots)
    q / ESC : çıkış
"""
import argparse
import collections
import os
import sys
import time

import cv2
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from rppg.camera import open_camera  # noqa: E402
from rppg.evm import StreamingEVM  # noqa: E402
from rppg.filtering import preprocess_bvp, resample_uniform  # noqa: E402
from rppg.hr import BPM_GRID, OnlineHRTracker, peak_bpm, spectrum_bpm, window_snr_from_spectrum  # noqa: E402
from rppg.methods import apply_method  # noqa: E402
from rppg.respiration import respiration_rate  # noqa: E402
from rppg.roi import FaceTracker, roi_rects, skin_mask  # noqa: E402
from rppg.signals import TraceExtractor  # noqa: E402

ROIS = ["forehead", "left_cheek", "right_cheek", "full"]
ROI_LABEL = {"forehead": "ALIN", "left_cheek": "SOL", "right_cheek": "SAG", "full": "YUZ"}
COLORS = {"forehead": (214, 120, 42), "left_cheek": (52, 104, 235), "right_cheek": (122, 175, 27),
          "full": (164, 58, 74)}
FS = 30.0
PANEL_W = 340


def draw_panel(h, state):
    p = np.full((h, PANEL_W, 3), 250, np.uint8)
    ink, ink2 = (11, 11, 11), (78, 81, 82)
    cv2.putText(p, "NABIZ (BPM)", (16, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.55, ink2, 1, cv2.LINE_AA)
    bpm = state.get("hr")
    txt = f"{bpm:5.1f}" if bpm is not None else "  ---"
    cv2.putText(p, txt, (10, 95), cv2.FONT_HERSHEY_DUPLEX, 2.0, (40, 60, 227), 2, cv2.LINE_AA)
    wait = state.get("wait")
    if wait:
        cv2.putText(p, f"isiniyor... {wait:.0f} s", (16, 122), cv2.FONT_HERSHEY_SIMPLEX, 0.5, ink2, 1, cv2.LINE_AA)
    y = 150
    for label, key, fmt in [("SNR", "snr", "{:.1f} dB"), ("SOLUNUM", "rr", "{:.1f} /dk"),
                            ("HAREKET GUVENI", "conf", "{:.2f}"), ("FPS", "fps", "{:.1f}")]:
        v = state.get(key)
        cv2.putText(p, label, (16, y), cv2.FONT_HERSHEY_SIMPLEX, 0.45, ink2, 1, cv2.LINE_AA)
        cv2.putText(p, fmt.format(v) if v is not None else "-", (190, y), cv2.FONT_HERSHEY_SIMPLEX, 0.55, ink, 1, cv2.LINE_AA)
        y += 26
    # ROI ağırlıkları
    w = state.get("weights") or {}
    cv2.putText(p, "ROI AGIRLIKLARI", (16, y + 4), cv2.FONT_HERSHEY_SIMPLEX, 0.45, ink2, 1, cv2.LINE_AA)
    y += 14
    for n in ROIS:
        val = w.get(n, 0.0)
        cv2.rectangle(p, (80, y), (80 + int(230 * val), y + 12), COLORS[n], -1)
        cv2.putText(p, ROI_LABEL[n], (16, y + 11), cv2.FONT_HERSHEY_SIMPLEX, 0.42, ink, 1, cv2.LINE_AA)
        y += 18
    # BVP dalga biçimi (son 5 s)
    bvp = state.get("bvp")
    y0, gh = y + 14, 70
    cv2.putText(p, "BVP (son 5 s)", (16, y0), cv2.FONT_HERSHEY_SIMPLEX, 0.45, ink2, 1, cv2.LINE_AA)
    if bvp is not None and len(bvp) > 10:
        seg = bvp[-int(5 * FS):]
        seg = (seg - seg.min()) / (np.ptp(seg) + 1e-9)
        xs = np.linspace(16, PANEL_W - 16, len(seg)).astype(int)
        ys = (y0 + 8 + gh - seg * gh).astype(int)
        cv2.polylines(p, [np.stack([xs, ys], 1)], False, (214, 120, 42), 2, cv2.LINE_AA)
    # Spektrum
    spec = state.get("spec")
    y1 = y0 + gh + 34
    cv2.putText(p, "SPEKTRUM 42-180 BPM", (16, y1), cv2.FONT_HERSHEY_SIMPLEX, 0.45, ink2, 1, cv2.LINE_AA)
    if spec is not None and y1 + gh + 10 < h:
        m = BPM_GRID <= 180
        s = spec[m] / (spec[m].max() + 1e-12)
        xs = np.linspace(16, PANEL_W - 16, len(s)).astype(int)
        ys = (y1 + 8 + gh - s * gh).astype(int)
        cv2.polylines(p, [np.stack([xs, ys], 1)], False, (52, 104, 235), 2, cv2.LINE_AA)
        if bpm is not None:
            xb = int(16 + (bpm - 42) / (180 - 42) * (PANEL_W - 32))
            cv2.line(p, (xb, y1 + 8), (xb, y1 + 8 + gh), (40, 60, 227), 1)
    cv2.putText(p, "e:EVM  m:maske  r:sifirla  s:kaydet  q:cik", (10, h - 12),
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, ink2, 1, cv2.LINE_AA)
    if state.get("evm"):
        cv2.putText(p, "EVM ACIK", (220, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (40, 60, 227), 1, cv2.LINE_AA)
    return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--camera", type=int, default=0)
    ap.add_argument("--video")
    ap.add_argument("--method", default="pos", choices=["green", "ica", "chrom", "pos", "lgi"])
    ap.add_argument("--window", type=float, default=10.0)
    ap.add_argument("--headless", action="store_true")
    ap.add_argument("--save", help="çıktı videosu (.mp4/.avi)")
    ap.add_argument("--bbox", type=float, nargs=4)
    ap.add_argument("--no-lock", action="store_true", help="oto pozlamayı kilitlemeye çalışma")
    a = ap.parse_args()

    if a.video:
        cap = cv2.VideoCapture(a.video)
        src_fps = cap.get(cv2.CAP_PROP_FPS) or FS
    else:
        cap = open_camera(a.camera, lock_exposure=not a.no_lock)
        src_fps = None
    tracker = FaceTracker(detect_every=10, use_haar=a.bbox is None, initial_bbox=a.bbox)
    ex = TraceExtractor(tracker, ROIS, respiration=True)
    maxlen = int(30 * FS * 1.5)
    T = collections.deque(maxlen=maxlen)
    RGB = {n: collections.deque(maxlen=maxlen) for n in ROIS}
    MOT = collections.deque(maxlen=maxlen)
    CH = collections.deque(maxlen=maxlen)
    CY = collections.deque(maxlen=maxlen)
    motion_hist = collections.deque(maxlen=300)
    hr_tr = OnlineHRTracker()
    evm = None
    state = {"evm": False}
    show_mask = False
    writer = None
    last_upd, last_t, frame_i = -1.0, None, 0
    fps_est = collections.deque(maxlen=30)
    t_start = time.perf_counter()
    os.makedirs("results/screenshots", exist_ok=True)

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        t = frame_i / src_fps if src_fps else time.perf_counter() - t_start
        frame_i += 1
        if last_t is not None and t > last_t:
            fps_est.append(1.0 / (t - last_t))
        last_t = t
        bbox, motion, rgb, skin, dy, rects = ex.process(frame)
        if bbox is not None and np.all(np.isfinite(rgb["forehead"])):
            T.append(t)
            for n in ROIS:
                RGB[n].append(rgb[n])
            MOT.append(motion)
            CH.append(0.0 if not np.isfinite(dy) else dy)
            CY.append(bbox.center[1])

        dur = (T[-1] - T[0]) if len(T) > 1 else 0.0
        state["wait"] = max(0.0, 6.0 - dur) if dur < 6.0 else None
        if dur >= 6.0 and t - last_upd >= 0.5:
            dt = t - last_upd if last_upd > 0 else 0.5
            last_upd = t
            tt = np.array(T)
            sel = tt >= tt[-1] - a.window
            ts = tt[sel]
            specs, weights, bvps = {}, {}, {}
            for n in ROIS:
                _, u = resample_uniform(np.array(RGB[n])[sel], ts, FS)
                bvp = preprocess_bvp(apply_method(a.method, u, FS), FS)
                p = spectrum_bpm(bvp, FS)
                snr = window_snr_from_spectrum(BPM_GRID, p, peak_bpm(BPM_GRID, p))
                specs[n], bvps[n] = p, bvp
                weights[n] = (10 ** (snr / 10)) ** 2
            tot = sum(weights.values()) + 1e-12
            weights = {k: v / tot for k, v in weights.items()}
            fused = sum(weights[n] * specs[n] for n in ROIS)
            fused /= fused.sum()
            m_win = float(np.mean(np.array(MOT)[sel]))
            motion_hist.append(m_win)
            ref = 2 * np.median(motion_hist) + 1e-9
            conf = float(np.clip(1.0 / (1.0 + (m_win / ref) ** 2), 0.1, 1.0))
            hr = hr_tr.update(fused, dt, conf)
            best = max(weights, key=weights.get)
            state.update(hr=hr, spec=fused, weights=weights, bvp=bvps[best], conf=conf,
                         snr=window_snr_from_spectrum(BPM_GRID, fused, hr))
            if dur >= 15.0:
                _, u_ch = resample_uniform(np.array(CH), tt, FS)
                _, u_cy = resample_uniform(np.array(CY), tt, FS)
                _, _, rr, _ = respiration_rate(u_ch, FS, u_cy, win_sec=min(30.0, dur))
                state["rr"] = rr
        state["fps"] = float(np.mean(fps_est)) if fps_est else None

        # --- görselleştirme
        if state["evm"]:
            if evm is None:
                evm = StreamingEVM(FS, 0.8, 2.2, alpha=80, level=3)
            view = evm.process(frame)
        else:
            view = frame.copy()
        if bbox is not None:
            x, y, w, h = bbox.as_int()
            cv2.rectangle(view, (x, y), (x + w, y + h), (200, 200, 200), 1)
            for n in ROIS:
                rx, ry, rw, rh = rects[n]
                wv = (state.get("weights") or {}).get(n, 0.33)
                cv2.rectangle(view, (rx, ry), (rx + rw, ry + rh), COLORS[n], 1 + int(3 * wv))
                if show_mask and rw > 0 and rh > 0:
                    m = skin_mask(frame[ry:ry + rh, rx:rx + rw])
                    view[ry:ry + rh, rx:rx + rw][m == 0] = (view[ry:ry + rh, rx:rx + rw][m == 0] * 0.3).astype(np.uint8)
        else:
            cv2.putText(view, "YUZ BULUNAMADI", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
        if view.shape[0] < 600:   # küçük kaynaklarda paneli sığdırmak için büyüt
            sc = 600 / view.shape[0]
            view = cv2.resize(view, (int(view.shape[1] * sc), 600), interpolation=cv2.INTER_LINEAR)
        canvas = np.hstack([view, draw_panel(view.shape[0], state)])
        if a.save:
            if writer is None:
                fourcc = cv2.VideoWriter_fourcc(*("mp4v" if a.save.endswith(".mp4") else "MJPG"))
                writer = cv2.VideoWriter(a.save, fourcc, src_fps or FS, (canvas.shape[1], canvas.shape[0]))
            writer.write(canvas)
        if not a.headless:
            cv2.imshow("rPPG canli demo", canvas)
            k = cv2.waitKey(1) & 0xFF
            if k in (ord("q"), 27):
                break
            if k == ord("e"):
                state["evm"] = not state["evm"]
                evm = None
            if k == ord("m"):
                show_mask = not show_mask
            if k == ord("r"):
                hr_tr.reset()
            if k == ord("s"):
                path = f"results/screenshots/ekran_{int(time.time())}.png"
                cv2.imwrite(path, canvas)
                print("kaydedildi:", path)
    cap.release()
    if writer is not None:
        writer.release()
    if not a.headless:
        cv2.destroyAllWindows()
    if state.get("hr") is not None:
        print(f"Son nabız tahmini: {state['hr']:.1f} BPM")


if __name__ == "__main__":
    main()
