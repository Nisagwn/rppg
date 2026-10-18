#!/usr/bin/env python
"""
Mobil uygulamanın gerçek veride doğrulanması.

Her gerçek video kesiti (UBFC-rPPG, MCD-rPPG) Chrome'a sahte kamera olarak verilir; uygulama
(mobile/) tarayıcıda gerçek zamanlı ölçüm yapar. Her saniyelik ölçüm parmak PPG referansıyla
ve aynı kesitte Python hattının (POS, 4 bölge, ortalama füzyon, Viterbi) sonucuyla karşılaştırılır.

    python scripts/validate_mobile.py                      # tüm UBFC + MCD önden webcam kesitleri
    python scripts/validate_mobile.py --max-clips 4        # hızlı deneme
    python scripts/validate_mobile.py --mcd-cameras FullHDwebcam,IriunWebcam
    python scripts/validate_mobile.py --mcd-cameras USBVideo --clips 1024_USBVideo_after,1035_USBVideo_before

Gerekenler: Node.js 22+, Chrome/Edge (CHROME ortam değişkeni ile de verilebilir).
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile

import cv2
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from rppg.io_utils import find_ubfc_subjects, gt_window_hr, load_mcd_item, load_ubfc_gt  # noqa: E402
from rppg.pipeline import Config, estimate  # noqa: E402
from rppg.roi import FaceTracker  # noqa: E402
from rppg.signals import extract_traces  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..")
E2E = os.path.join(ROOT, "mobile", "test", "e2e.mjs")
PY_CFG = Config("pos", ("forehead", "left_cheek", "right_cheek", "full"), "mean", "viterbi", True)
FPS = 30


def clips(a):
    out = []
    for subj in find_ubfc_subjects(os.path.join(ROOT, "data", "UBFC")):
        out.append({"kaynak": "UBFC", "ad": os.path.basename(subj), "kamera": "webcam (önden)", "durum": "oyun",
                    "video": os.path.join(subj, "vid.avi"), "gt": load_ubfc_gt(subj), "s0": 0.0})
    db_path = os.path.join(ROOT, "data", "MCD", "db.csv")
    if os.path.exists(db_path):
        db = pd.read_csv(db_path)
        db = db[db.camera.isin(a.mcd_cameras.split(","))]
        for r in db.itertuples():
            if not all(os.path.exists(os.path.join(ROOT, "data", "MCD", p)) for p in (r.video, r.meta, r.ppg_sync)):
                continue
            it = load_mcd_item(os.path.join(ROOT, "data", "MCD"), r.video, r.meta, r.ppg_sync)
            out.append({"kaynak": "MCD", "ad": os.path.splitext(os.path.basename(r.video))[0],
                        "kamera": {"FullHDwebcam": "webcam (önden)", "IriunWebcam": "telefon",
                                   "USBVideo": "USB (yan)"}[r.camera],
                        "durum": {"before": "dinlenme", "after": "egzersiz sonrası"}[r.step],
                        "video": it["video"], "gt": it["gt"], "s0": 30.0, "ts": it["timestamps"]})
    if a.clips:   # yalnızca adı verilen kesitler (başarısız kesitlerde hızlı deneme için)
        want = set(a.clips.split(","))
        out = [c for c in out if c["ad"] in want]
    return out[:a.max_clips] if a.max_clips else out


def read_clip(path, s0, dur, ts=None):
    """[s0, s0+dur] aralığını 30 fps ızgaraya en yakın kareyle taşır. MCD videolarının bir kısmı 24 fps
    (çoğu Iriun, bazı önden webcam); kareler 30 fps sayılırsa zaman 1.25 kat hızlanır, HR o kadar şişer."""
    c = cv2.VideoCapture(path)
    vfps = c.get(cv2.CAP_PROP_FPS) or FPS
    src_t, src_f, i = [], [], 0
    while True:
        ok, f = c.read()
        if not ok:
            break
        t = ts[i] if ts is not None and i < len(ts) else i / vfps   # MCD: kare zaman damgası (etiketle aynı eksen)
        i += 1
        if t < s0 - 0.5:
            continue
        if t > s0 + dur + 0.5:
            break
        h, w = f.shape[:2]
        s = 640 / max(h, w)
        if s < 1:
            f = cv2.resize(f, (int(w * s) // 2 * 2, int(h * s) // 2 * 2), interpolation=cv2.INTER_AREA)
        src_t.append(t)
        src_f.append(f)
    if not src_f:
        return []
    src_t = np.array(src_t)
    grid = s0 + np.arange(int(min(dur, src_t[-1] - s0) * FPS)) / FPS
    idx = np.clip(np.searchsorted(src_t, grid), 1, len(src_t) - 1)
    idx -= (grid - src_t[idx - 1]) < (src_t[idx] - grid)
    return [src_f[k] for k in idx]


def write_y4m(path, frames):
    h, w = frames[0].shape[:2]
    with open(path, "wb") as f:
        f.write(f"YUV4MPEG2 W{w} H{h} F{FPS}:1 Ip A1:1 C420jpeg\n".encode())
        for fr in frames:
            f.write(b"FRAME\n")
            f.write(cv2.cvtColor(fr, cv2.COLOR_BGR2YUV_I420).tobytes())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--duration", type=float, default=40.0, help="kesit süresi (s)")
    ap.add_argument("--max-clips", type=int)
    ap.add_argument("--clips", help="virgülle ayrılmış kesit adları (ör. 1024_USBVideo_after)")
    ap.add_argument("--no-python", action="store_true", help="Python hattını çalıştırma (hızlı deneme)")
    ap.add_argument("--app-args", default="", help="uygulamaya ek URL parametreleri (ör. yuz=eski)")
    ap.add_argument("--mcd-cameras", default="FullHDwebcam")
    ap.add_argument("--out", default="results/mobil_dogrulama")
    a = ap.parse_args()
    os.makedirs(os.path.join(a.out, "teshis"), exist_ok=True)

    rows = []
    items = clips(a)
    print(f"{len(items)} kesit doğrulanacak ({a.duration:.0f} s)")
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        for i, c in enumerate(items, 1):
            frames = read_clip(c["video"], c["s0"], a.duration, c.get("ts"))
            dur = len(frames) / FPS
            y4m, logf = os.path.join(tmp, "clip.y4m"), os.path.join(tmp, "log.json")
            diagf = os.path.join(a.out, "teshis", c["ad"] + ".json")
            write_y4m(y4m, frames)
            if os.path.exists(logf):
                os.remove(logf)
            try:
                subprocess.run(["node", E2E, "--video", y4m, "--expect", "0", "--seconds", str(dur - 1), "--log", logf,
                                "--diag", diagf] + (["--params", a.app_args] if a.app_args else []),
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=dur + 60)
            except subprocess.TimeoutExpired:
                print(f"  ! {c['ad']}: tarayıcı zaman aşımı")
            log = json.load(open(logf)) if os.path.exists(logf) else []
            # teşhis: ısınmadan sonra (t >= 10) yüz kutusu olan karelerin oranı ve ölçümün durduğu saniyeler
            diag = [r for r in (json.load(open(diagf)) if os.path.exists(diagf) else []) if r["t"] >= 10]
            nfr = sum(r["frames"] for r in diag)
            yuz = sum(r["face"] for r in diag) / nfr if nfr else float("nan")
            tries = sum(r["tries"] for r in diag)
            tespit = sum(r["hits"] for r in diag) / tries if tries else float("nan")
            kapi = {g: sum(r["gate"] == g for r in diag) for g in ("yuz_yok", "isinma", "model_isinma", "olcum")}

            # uygulama: t anındaki ölçüm son 10 s'yi kapsar -> pencere merkezi t - 5
            t = np.array([r["t"] for r in log]) if log else np.zeros(0)
            hr = np.array([r["hr"] for r in log]) if log else np.zeros(0)
            m = (t >= 10) & (t <= dur - 1)
            if m.sum():
                ref = gt_window_hr(c["gt"], c["s0"] + t[m] - 5, 10.0)
                err = np.abs(hr[m] - ref)
                app_mae, app_5 = float(err.mean()), float((err <= 5).mean() * 100)
            else:
                app_mae = app_5 = float("nan")

            pref = gt_window_hr(c["gt"], c["s0"] + np.arange(5, dur - 4), 10.0)
            py_mae = float("nan")
            if not a.no_python:
                try:
                    tr = extract_traces(iter(frames), FPS, FaceTracker())
                    res = estimate(tr, PY_CFG)
                    pref = gt_window_hr(c["gt"], c["s0"] + res.centers, 10.0)
                    py_mae = float(np.mean(np.abs(res.hr - pref)))
                except RuntimeError as e:   # Haar yan açılı yüzü bulamazsa (MCD USB) kesit atlanmasın, Python sütunu boş kalsın
                    print(f"  ! {c['ad']}: Python hattı: {e}")

            row = {k: c[k] for k in ("kaynak", "ad", "kamera", "durum")}
            row.update({"pencere": int(m.sum()), "uygulama_MAE": app_mae, "uygulama_≤5BPM%": app_5,
                        "python_MAE": py_mae, "referans_ort": float(np.mean(pref)),
                        "yuz_kare%": yuz * 100, "tespit%": tespit * 100,
                        **{f"sn_{g}": n for g, n in kapi.items()}})
            rows.append(row)
            print(f"  [{i}/{len(items)}] {c['kaynak']} {c['ad']:28s} uygulama {app_mae:5.2f}  python {py_mae:5.2f}  "
                  f"(ref {row['referans_ort']:.0f} BPM, {row['pencere']} pencere, yüz %{yuz * 100:.0f}, "
                  f"tespit %{tespit * 100:.0f}, duraklar {kapi})")

    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(a.out, "kesitler.csv"), index=False)
    g = df.groupby(["kaynak", "kamera", "durum"]).agg(
        kesit=("ad", "count"), uygulama_MAE=("uygulama_MAE", "mean"),
        **{"uygulama_≤5BPM%": ("uygulama_≤5BPM%", "mean")}, python_MAE=("python_MAE", "mean")).round(2)
    lines = ["# Mobil Uygulama — Gerçek Veri Doğrulaması", "",
             f"Her kesit ({a.duration:.0f} s) Chrome'a sahte kamera olarak verildi; uygulama tarayıcıda gerçek zamanlı "
             "ölçtü. Referans: parmak PPG'sinden 10 s pencere başına spektral tepe. İlk 10 s (ısınma) hariç.", "",
             "## Özet", "", g.reset_index().to_markdown(index=False), "",
             f"**Genel:** uygulama MAE {df.uygulama_MAE.mean():.2f} BPM, pencerelerin %{df['uygulama_≤5BPM%'].mean():.0f}'i "
             f"≤5 BPM; aynı kesitlerde Python hattı MAE {df.python_MAE.mean():.2f} BPM ({len(df)} kesit).", "",
             "## Kesitler", "", df.round(2).to_markdown(index=False), ""]
    open(os.path.join(a.out, "SONUCLAR.md"), "w", encoding="utf-8").write("\n".join(lines))
    print("\n".join(lines[:9]))


if __name__ == "__main__":
    main()
