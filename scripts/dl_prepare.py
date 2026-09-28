#!/usr/bin/env python
"""
Derin öğrenme eğitimi için veri hazırlama (rPPG-Toolbox ön işlemesiyle aynı).

Her video için: Haar yüz kutusu x1.5 (30 karede bir yeniden tespit), 72x72 INTER_AREA, RGB,
30 fps'e doğrusal yeniden örnekleme; parmak PPG'si aynı zaman eksenine taşınır.
Çıktı: data/dl/<kaynak>/<ad>.npy (kareler uint8 [T,72,72,3]) + <ad>.npz (bvp float32 [T], fs, face_rate, bilgi)

Test kişileri (önceki karşılaştırmanın 28 videosu: UBFC 8 denek + MCD 10 kişi) eğitime ASLA girmez;
bunlar --test ile yalnızca yereldeki dosyalardan ayrı klasöre (data/dl/test) işlenir.

    python scripts/dl_prepare.py --test                      # 28 test videosu (yerel)
    python scripts/dl_prepare.py --mcd 60                    # test dışı 60 kişi, 3 kamera (indir-işle-sil)
    python scripts/dl_prepare.py --ubfc 10                   # UBFC'nin test dışı 10 deneği (indir-işle-sil)

İnmiş/işlenmiş dosyalar atlanır; yarıda kalırsa aynı komut tekrar çalıştırılır.
"""
import argparse
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

import cv2
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from rppg.io_utils import load_mcd_ppg, load_mcd_timestamps, load_ubfc_gt  # noqa: E402

FS = 30.0
SIZE = 72
DET_FREQ = 30
BOX_COEF = 1.5
HAAR = os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml")
MCD_HF = "https://huggingface.co/datasets/akramic/mcd_rppg/resolve/main/"
UBFC_HF = "https://huggingface.co/datasets/thachha901/UBFC/resolve/main/UBFC/"
UBFC_TEST = {"subject1", "subject3", "subject4", "subject5", "subject8", "subject9", "subject10", "subject11"}
MCD_TEST = {1020, 1024, 1035, 1091, 1097, 1099, 1107, 1113, 1115, 1149}


# ------------------------------------------------------------------ ön işleme
def _detect(det, rgb, scale=2):
    """Toolbox HC: en geniş Haar yüzü, merkez sabit x1.5 büyütme.
    Hız için eğitim videolarında yarım çözünürlükte aranır (scale=2), kutu geri ölçeklenir."""
    small = cv2.resize(rgb, (rgb.shape[1] // scale, rgb.shape[0] // scale), interpolation=cv2.INTER_AREA)         if scale > 1 else rgb
    faces = det.detectMultiScale(small)
    if len(faces) == 0:
        return None
    x, y, w, h = [float(v) * scale for v in faces[np.argmax(faces[:, 2])]]
    x = max(0.0, x - (BOX_COEF - 1) / 2 * w)
    y = max(0.0, y - (BOX_COEF - 1) / 2 * h)
    return int(x), int(y), int(BOX_COEF * w), int(BOX_COEF * h)


def crop_video(path, max_frames=None, det_scale=1):
    """Kareler -> 72x72 RGB yüz kırpıntısı (uint8) ve yüz bulunma oranı.
    Toolbox'tan tek fark: yüz bulunamazsa tüm kare yerine son bulunan kutu kullanılır."""
    det = cv2.CascadeClassifier(HAAR)
    cap = cv2.VideoCapture(path)
    out, box, n_det, n_found, i = [], None, 0, 0, 0
    while True:
        ok, bgr = cap.read()
        if not ok or (max_frames and i >= max_frames):
            break
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        if i % DET_FREQ == 0:
            n_det += 1
            b = _detect(det, rgb, det_scale)
            if b is not None:
                box, n_found = b, n_found + 1
        if box is None:
            crop = rgb
        else:
            x, y, w, h = box
            crop = rgb[y:min(y + h, rgb.shape[0]), x:min(x + w, rgb.shape[1])]
        out.append(cv2.resize(crop, (SIZE, SIZE), interpolation=cv2.INTER_AREA))
        i += 1
    cap.release()
    if not out:
        raise RuntimeError(f"video okunamadı: {path}")
    return np.stack(out), n_found / max(n_det, 1)


def resample(frames, t_frames, bvp, t_bvp):
    """Kareleri ve PPG'yi eşit aralıklı 30 fps ızgarasına doğrusal enterpolasyonla taşır."""
    n = min(len(frames), len(t_frames))
    frames, t_frames = frames[:n], np.asarray(t_frames[:n], dtype=float) - t_frames[0]
    grid = np.arange(0.0, t_frames[-1], 1.0 / FS)
    j = np.clip(np.searchsorted(t_frames, grid, side="right") - 1, 0, n - 2)
    w = ((grid - t_frames[j]) / np.maximum(t_frames[j + 1] - t_frames[j], 1e-6)).clip(0, 1)
    w = w[:, None, None, None].astype(np.float32)
    out = np.empty((len(grid),) + frames.shape[1:], dtype=np.uint8)
    for k in range(0, len(grid), 256):  # bellek: blok blok
        sl = slice(k, k + 256)
        blk = frames[j[sl]].astype(np.float32) * (1 - w[sl]) + frames[j[sl] + 1].astype(np.float32) * w[sl]
        out[sl] = np.round(blk).clip(0, 255).astype(np.uint8)
    lab = np.interp(grid, np.asarray(t_bvp, dtype=float) - t_bvp[0], bvp)
    return out, lab.astype(np.float32)


def save(dst, frames, bvp, face_rate, **meta):
    """Kareler <ad>.npy (eğitimde memory-map), etiket + bilgi <ad>.npz (en son yazılır = tamamlandı işareti)."""
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if face_rate >= 0.5 or "test" in os.path.basename(os.path.dirname(dst)):  # eğitimde kullanılmayacaksa diske yazma
        np.save(dst[:-4] + ".part.npy", frames)
        os.replace(dst[:-4] + ".part.npy", dst[:-4] + ".npy")
    np.savez(dst + ".part.npz", bvp=bvp, fs=FS, face_rate=face_rate, n=len(frames), **meta)
    os.replace(dst + ".part.npz", dst)


def process_mcd(video, meta, ppg, dst, max_sec=None, **info):
    ts = load_mcd_timestamps(meta)
    max_frames = int(np.searchsorted(ts, ts[0] + max_sec)) + 2 if max_sec else None
    frames, rate = crop_video(video, max_frames, 2 if max_sec else 1)  # test videoları tam çözünürlük (toolbox)
    bvp = load_mcd_ppg(ppg)
    n = min(len(ts), len(bvp), len(frames))
    f, b = resample(frames[:n], ts[:n], bvp[:n], ts[:n])
    save(dst, f, b, rate, **info)
    return len(f), rate


def process_ubfc(subject_dir, dst, **info):
    frames, rate = crop_video(os.path.join(subject_dir, "vid.avi"))
    gt = load_ubfc_gt(subject_dir)
    # UBFC 30 fps; toolbox gibi PPG kare sayısına yeniden örneklenir
    bvp = np.interp(np.linspace(0, 1, len(frames)), np.linspace(0, 1, len(gt["bvp"])), gt["bvp"])
    t = np.arange(len(frames)) / FS
    f, b = resample(frames, t, bvp, t)
    save(dst, f, b, rate, **info)
    return len(f), rate


# -------------------------------------------------------------------- indirme
def fetch(url, dst, retries=3):
    import requests
    if os.path.exists(dst) and os.path.getsize(dst) > 0:
        return
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    for k in range(retries):
        try:
            with requests.get(url, stream=True, timeout=120) as r:
                r.raise_for_status()
                with open(dst + ".part", "wb") as f:
                    for chunk in r.iter_content(1 << 20):
                        f.write(chunk)
            os.replace(dst + ".part", dst)
            return
        except Exception:
            if k == retries - 1:
                raise
            time.sleep(5 * (k + 1))


def job_mcd(row, raw_root, out_root, keep_raw, max_sec):
    name = os.path.splitext(os.path.basename(row["video"]))[0]
    dst = os.path.join(out_root, "mcd", name + ".npz")
    if os.path.exists(dst):
        return name, "var"
    for rel in (row["meta"], row["ppg_sync"], row["video"]):
        fetch(MCD_HF + rel, os.path.join(raw_root, rel))
    vid = os.path.join(raw_root, row["video"])
    n, rate = process_mcd(vid, os.path.join(raw_root, row["meta"]), os.path.join(raw_root, row["ppg_sync"]), dst, max_sec,
                          person=int(row["patient_id"]), camera=row["camera"], step=row["step"], source="mcd")
    if not keep_raw:
        os.remove(vid)
    return name, f"{n} kare, yüz %{100 * rate:.0f}"


def job_ubfc(subject, raw_root, out_root, keep_raw):
    dst = os.path.join(out_root, "ubfc", subject + ".npz")
    if os.path.exists(dst):
        return subject, "var"
    sdir = os.path.join(raw_root, subject)
    fetch(UBFC_HF + subject + "/ground_truth.txt", os.path.join(sdir, "ground_truth.txt"))
    fetch(UBFC_HF + subject + "/vid.avi", os.path.join(sdir, "vid.avi"))
    n, rate = process_ubfc(sdir, dst, person=subject, camera="C920", step="ubfc", source="ubfc")
    if not keep_raw:
        os.remove(os.path.join(sdir, "vid.avi"))
    return subject, f"{n} kare, yüz %{100 * rate:.0f}"


def job_test(kind, args, out_root):
    if kind == "ubfc":
        sdir = args
        name = os.path.basename(sdir)
        dst = os.path.join(out_root, "test", f"ubfc_{name}.npz")
        if os.path.exists(dst):
            return name, "var"
        n, rate = process_ubfc(sdir, dst, person=name, camera="C920", step="ubfc", source="ubfc")
    else:
        row, root = args
        name = os.path.splitext(os.path.basename(row["video"]))[0]
        dst = os.path.join(out_root, "test", f"mcd_{name}.npz")
        if os.path.exists(dst):
            return name, "var"
        n, rate = process_mcd(os.path.join(root, row["video"]), os.path.join(root, row["meta"]),
                              os.path.join(root, row["ppg_sync"]), dst, None, person=int(row["patient_id"]),
                              camera=row["camera"], step=row["step"], source="mcd")
    return name, f"{n} kare, yüz %{100 * rate:.0f}"


def _init_worker():
    cv2.setNumThreads(1)  # çok süreçte OpenCV iş parçacıkları CPU'yu boğmasın


def run(jobs, workers):
    """İşleri paralel çalıştırır; başarısız iş sayısını döndürür."""
    t0, failed = time.time(), 0
    with ProcessPoolExecutor(workers, initializer=_init_worker) as ex:
        futs = {ex.submit(fn, *args): i for i, (fn, args) in enumerate(jobs)}
        for k, fut in enumerate(as_completed(futs), 1):
            try:
                name, msg = fut.result()
                print(f"  [{k}/{len(jobs)}] {name}: {msg}  ({time.time() - t0:.0f} s)", flush=True)
            except Exception as e:
                failed += 1
                print(f"  [{k}/{len(jobs)}] HATA: {e!r}", flush=True)
    return failed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/dl")
    ap.add_argument("--raw", default="data/dl/_raw", help="geçici indirme klasörü")
    ap.add_argument("--test", action="store_true", help="yereldeki 28 test videosunu işle")
    ap.add_argument("--mcd", type=int, default=0, help="test dışı kaç MCD kişisi")
    ap.add_argument("--mcd-skip", type=int, default=0, help="listede ilk kaç kişiyi atla (parça parça indirmek için)")
    ap.add_argument("--cameras", default="FullHDwebcam,USBVideo,IriunWebcam")
    ap.add_argument("--ubfc", type=int, default=0, help="UBFC'nin test dışı kaç deneği (video başına 1.8 GB)")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--keep-raw", action="store_true")
    ap.add_argument("--max-sec", type=float, default=120, help="eğitim videosundan saklanacak süre (disk için)")
    a = ap.parse_args()
    failed = 0

    if a.test:
        from rppg.io_utils import find_ubfc_subjects
        jobs = [(job_test, ("ubfc", s, a.out)) for s in find_ubfc_subjects("data/UBFC")
                if os.path.basename(s) in UBFC_TEST]
        db = pd.read_csv("data/MCD/db.csv")
        db = db[db.patient_id.isin(MCD_TEST) & (db.camera == "FullHDwebcam")]
        jobs += [(job_test, ("mcd", (r._asdict(), "data/MCD"), a.out)) for r in db.itertuples()
                 if os.path.exists(os.path.join("data/MCD", r.video))]
        print(f"Test kümesi: {len(jobs)} video")
        failed = run(jobs, a.workers)

    if a.mcd:
        from scripts.evaluate_mcd import _available_videos
        db_path = os.path.join(a.raw, "db.csv")
        fetch(MCD_HF + "db.csv", db_path)
        db = pd.read_csv(db_path)
        db = db[db.video.isin(_available_videos()) & db.camera.isin(a.cameras.split(","))
                & ~db.patient_id.isin(MCD_TEST)]
        people = db.patient_id.drop_duplicates().tolist()[a.mcd_skip:a.mcd_skip + a.mcd]
        rows = db[db.patient_id.isin(people)]
        print(f"MCD: {len(people)} kişi, {len(rows)} video")
        failed += run([(job_mcd, (r._asdict(), a.raw, a.out, a.keep_raw, a.max_sec)) for r in rows.itertuples()], a.workers)

    if a.ubfc:
        import requests
        tree = requests.get("https://huggingface.co/api/datasets/thachha901/UBFC/tree/main/UBFC", timeout=60).json()
        subjects = sorted({x["path"].split("/")[1] for x in tree} - UBFC_TEST, key=lambda s: int(s[7:]))[:a.ubfc]
        print(f"UBFC: {len(subjects)} denek (test dışı)")
        failed += run([(job_ubfc, (s, os.path.join(a.raw, "ubfc"), a.out, a.keep_raw)) for s in subjects],
            max(1, min(a.workers, 2)))  # video başına 1.8 GB; aynı anda en çok 2
    if failed:
        sys.exit(f"{failed} video başarısız; tekrar çalıştırın (tamamlananlar atlanır)")


if __name__ == "__main__":
    main()
