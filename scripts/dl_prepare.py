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
    python scripts/dl_prepare.py --pure 60                   # PURE'un 60 oturumu (HF kopyası, indir-işle-sil)

İnmiş/işlenmiş dosyalar atlanır; yarıda kalırsa aynı komut tekrar çalıştırılır.
"""
import argparse
import glob
import os
import re
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


def _video_frames(path):
    cap = cv2.VideoCapture(path)
    while True:
        ok, bgr = cap.read()
        if not ok:
            break
        yield bgr
    cap.release()


def _ffmpeg_frames(path):
    """ffmpeg ile çözme (BGR). UBFC'nin sıkıştırılmamış rawvideo AVI'leri bazı OpenCV sürümlerinde (Kaggle)
    çözücü süreci çökertiyor (BrokenProcessPool); ffmpeg aynı pikselleri verir."""
    import subprocess
    info = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                           "-of", "csv=p=0", path], capture_output=True, text=True, check=True).stdout
    w, h = [int(v) for v in info.strip().split(",")[:2]]
    proc = subprocess.Popen(["ffmpeg", "-v", "error", "-i", path, "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
                            stdout=subprocess.PIPE)
    n = w * h * 3
    try:
        while True:
            buf = proc.stdout.read(n)
            if len(buf) < n:
                break
            yield np.frombuffer(buf, np.uint8).reshape(h, w, 3)
    finally:
        proc.stdout.close()
        proc.kill()
        proc.wait()


def crop_video(path, max_frames=None, det_scale=1, decoder="cv2"):
    import shutil
    frames = _ffmpeg_frames(path) if decoder == "ffmpeg" and shutil.which("ffmpeg") else _video_frames(path)
    return crop_frames(frames, max_frames, det_scale, path)


def crop_frames(frames_bgr, max_frames=None, det_scale=1, name=""):
    """Kareler (BGR) -> 72x72 RGB yüz kırpıntısı (uint8) ve yüz bulunma oranı.
    Toolbox'tan tek fark: yüz bulunamazsa tüm kare yerine son bulunan kutu kullanılır."""
    det = cv2.CascadeClassifier(HAAR)
    out, box, n_det, n_found, i = [], None, 0, 0, 0
    for bgr in frames_bgr:
        if max_frames and i >= max_frames:
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
    if not out:
        raise RuntimeError(f"video okunamadı: {name}")
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
    frames, rate = crop_video(os.path.join(subject_dir, "vid.avi"), decoder="ffmpeg")  # rawvideo: bkz. _ffmpeg_frames
    gt = load_ubfc_gt(subject_dir)
    # UBFC 30 fps; toolbox gibi PPG kare sayısına yeniden örneklenir
    bvp = np.interp(np.linspace(0, 1, len(frames)), np.linspace(0, 1, len(gt["bvp"])), gt["bvp"])
    t = np.arange(len(frames)) / FS
    f, b = resample(frames, t, bvp, t)
    save(dst, f, b, rate, **info)
    return len(f), rate


def process_pure(zip_path, dst, max_sec=None, **info):
    """PURE oturumu (zip): PNG kareler (ad = zaman damgası, ns) + JSON'da parmak oksimetresi dalga formu.
    Toolbox'ın PURE yükleyicisi gibi 'waveform' kullanılır; kare zamanlarına enterpole edilir."""
    import json
    import zipfile
    z = zipfile.ZipFile(zip_path)
    pngs = sorted((int(os.path.basename(n)[5:-4]), n) for n in z.namelist() if n.endswith(".png"))
    meta = json.loads(z.read(next(n for n in z.namelist() if n.endswith(".json"))))
    t_img = np.array([t for t, _ in pngs], dtype=float) / 1e9
    if max_sec:
        pngs = [p for p, t in zip(pngs, t_img) if t - t_img[0] <= max_sec + 0.1]
        t_img = t_img[:len(pngs)]
    ppg = meta["/FullPackage"]
    t_ppg = np.array([p["Timestamp"] for p in ppg], dtype=float) / 1e9
    wave = np.array([p["Value"]["waveform"] for p in ppg], dtype=float)
    bvp = np.interp(t_img, t_ppg, wave)
    decode = (cv2.imdecode(np.frombuffer(z.read(n), np.uint8), cv2.IMREAD_COLOR) for _, n in pngs)
    frames, rate = crop_frames(decode, None, 2, zip_path)
    n = min(len(frames), len(t_img))
    f, b = resample(frames[:n], t_img[:n], bvp[:n], t_img[:n])
    save(dst, f, b, rate, **info)
    return len(f), rate


# -------------------------------------------------------------------- indirme
def fetch(url, dst, retries=8):
    """İndirir; Hugging Face hız sınırında (429) Retry-After kadar bekler. HF_TOKEN ortam değişkeni varsa kullanılır."""
    import requests
    if os.path.exists(dst) and os.path.getsize(dst) > 0:
        return
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    tok = hf_token()
    headers = {"Authorization": f"Bearer {tok}"} if tok and "huggingface.co" in url else {}
    for k in range(retries):
        try:
            with requests.get(url, stream=True, timeout=120, headers=headers) as r:
                if r.status_code == 429:
                    time.sleep(float(r.headers.get("Retry-After", 30 * (k + 1))))
                    raise RuntimeError("429 hız sınırı")
                r.raise_for_status()
                with open(dst + ".part", "wb") as f:
                    for chunk in r.iter_content(1 << 20):
                        f.write(chunk)
            os.replace(dst + ".part", dst)
            return
        except Exception:
            if k == retries - 1:
                raise
            time.sleep(min(60, 5 * 2 ** k))


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


def label_polarity(frames, bvp, fs=FS):
    """Etiketin işaretini videodan bağımsız bir kestirimle (yüz kırpıntısının ortasında POS) karşılaştırır.
    Döndürür: (etiketi modelin kuralına getiren çarpan ±1, |korelasyon|).
    Ayar: POS bu kırpıntılarda modelin kuralına göre ters işaretli çıkar. Doğrulama: UBFC 20/20 ve PURE 12/12
    negatif korelasyon (etiket doğru), MCD 9/12 pozitif (etiket ters; elle de bulunmuştu, r ~ -0.75).
    Tek videoda güvenilir değil (MCD'de güvenli görünen 12 videonun 2'sinde yanlış): karar veri seti düzeyinde,
    korelasyonla ağırlıklı çoğunluk oyuyla verilir (dl_train.list_videos)."""
    from rppg.filtering import preprocess_bvp
    from rppg.methods import pos
    rgb = frames[:, 15:57, 15:57].reshape(len(frames), -1, 3).mean(axis=1).astype(float)
    a, b = preprocess_bvp(pos(rgb, fs), fs), preprocess_bvp(bvp, fs)
    best = 0.0
    for k in range(-4, 5):  # ±0.13 s: daha geniş aralık yarım periyot kaydırıp işareti çevirebilir
        c = np.corrcoef(np.roll(a, k)[20:-20], b[20:-20])[0, 1]
        if abs(c) > abs(best):
            best = c
    return (-1 if best > 0 else 1), abs(best)


UBFCPHYS_HF = "https://huggingface.co/datasets/jjuik2014/UBFC-Phys-all/resolve/main/"  # erişim: HF hesabı + koşul onayı


def process_ubfcphys(avi, bvp_csv, dst, max_sec=None, **info):
    """UBFC-Phys görevi: vid_sX_Tk.avi (35 fps) + bvp_sX_Tk.csv (Empatica E4, 64 Hz).
    Toolbox gibi PPG video süresine eşit aralıklı yayılır; işaret label_polarity ile denetlenir."""
    import subprocess
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate",
                        "-of", "csv=p=0", avi], capture_output=True, text=True)
    num, den = (r.stdout.strip() or "35/1").split("/")
    vfs = float(num) / float(den or 1)
    frames, rate = crop_video(avi, int(max_sec * vfs) + 2 if max_sec else None, 2, decoder="ffmpeg")
    ppg = pd.read_csv(bvp_csv, header=None).iloc[:, 0].to_numpy(dtype=float)
    t_v = np.arange(len(frames)) / vfs
    f, b = resample(frames, t_v, np.interp(t_v, np.arange(len(ppg)) / 64.0, ppg), t_v)
    sign, corr = label_polarity(f, b)       # etiket olduğu gibi saklanır; işaret eğitimde veri seti oyuyla
    save(dst, f, b, rate, polarity=sign, polarity_corr=corr, **info)
    return len(f), rate, sign, corr


def job_ubfcphys(zipname, raw_root, out_root, keep_raw, max_sec):
    """Bir zip (kişi ya da kişi grubu): indir, içindeki her görev videosunu çıkarıp işle, sil."""
    import re
    import zipfile
    zp = os.path.join(raw_root, zipname)
    done_mark = os.path.join(out_root, "ubfcphys", f".{zipname}.done")
    if os.path.exists(done_mark):
        return zipname, "var"
    fetch(UBFCPHYS_HF + zipname, zp)
    msgs = []
    with zipfile.ZipFile(zp) as z:
        names = z.namelist()
        for vid in sorted(n for n in names if re.search(r"vid_(s\d+_T\d)\.avi$", n)):
            key = re.search(r"vid_(s\d+_T\d)\.avi$", vid).group(1)
            dst = os.path.join(out_root, "ubfcphys", f"ubfcphys_{key}.npz")
            if os.path.exists(dst):
                continue
            bvp = next((n for n in names if n.endswith(f"bvp_{key}.csv")), None)
            if bvp is None:
                msgs.append(f"{key}: bvp yok")
                continue
            tmp = os.path.join(raw_root, "ubfcphys_tmp", key)
            os.makedirs(tmp, exist_ok=True)
            avi_p, bvp_p = z.extract(vid, tmp), z.extract(bvp, tmp)
            subj = key.split("_")[0]
            n, rate, sign, corr = process_ubfcphys(avi_p, bvp_p, dst, max_sec, person=f"ubfcphys_{subj}",
                                                   camera="UBFC-Phys", step=key.split("_")[1], source="ubfcphys")
            import shutil
            shutil.rmtree(tmp, ignore_errors=True)
            msgs.append(f"{key}: {n} kare, yüz %{100 * rate:.0f}, işaret {'+' if sign > 0 else '-'} (r={corr:.2f})")
    if not keep_raw:
        os.remove(zp)
    os.makedirs(os.path.dirname(done_mark), exist_ok=True)
    open(done_mark, "w").write("\n".join(msgs))
    return zipname, "; ".join(msgs) or "video bulunamadı"


def ubfcphys_zips(n):
    """Erişilebilir UBFC-Phys zip listesi; erişim yoksa (HF_TOKEN yok / koşullar onaylanmadı) boş liste."""
    import requests
    tree = requests.get("https://huggingface.co/api/datasets/jjuik2014/UBFC-Phys-all/tree/main", timeout=60).json()
    zips = sorted((x["path"] for x in tree if re.match(r"^(s\d+|UBFC_Phys_part\d+)\.zip$", x["path"])),
                  key=lambda p: (not p.startswith("s"), int(re.findall(r"\d+", p)[0])))
    headers = {"Authorization": f"Bearer {os.environ['HF_TOKEN']}"} if os.environ.get("HF_TOKEN") else {}
    r = requests.head(UBFCPHYS_HF + zips[0], headers=headers, allow_redirects=True, timeout=60)
    if r.status_code in (401, 403):
        print("UBFC-Phys: erişim yok — huggingface.co/datasets/jjuik2014/UBFC-Phys-all sayfasında koşulları kabul "
              "edip HF_TOKEN verin. Atlanıyor.", flush=True)
        return []
    return zips[:n]


MPU_FIGSHARE = "https://api.figshare.com/v2/articles/29377835"  # MPU-rPPG örnek alt kümesi (CC BY 4.0)


def process_mpu(video, csv_path, dst, max_sec=None, **info):
    """MPU-rPPG: 60 fps video + Output.csv (Count, PPG, HR, SPO2), kare başına bir PPG satırı."""
    ppg = pd.read_csv(csv_path)["PPG"].to_numpy(dtype=float)
    max_frames = int(max_sec * 60) if max_sec else None
    frames, rate = crop_video(video, max_frames, 2)
    n = min(len(frames), len(ppg))
    t = np.arange(n) / 60.0
    f, b = resample(frames[:n], t, ppg[:n], t)
    save(dst, f, b, rate, **info)
    return len(f), rate


def job_mpu(pair, raw_root, out_root, keep_raw, max_sec):
    vid_file, csv_file = pair
    name = f"mpu_{vid_file['id']}"
    dst = os.path.join(out_root, "mpu", name + ".npz")
    if os.path.exists(dst):
        return name, "var"
    vp = os.path.join(raw_root, f"{vid_file['id']}_{vid_file['name']}")
    cp = os.path.join(raw_root, f"{csv_file['id']}_{csv_file['name']}")
    fetch(csv_file["download_url"], cp)
    fetch(vid_file["download_url"], vp)
    n, rate = process_mpu(vp, cp, dst, max_sec, person=name, camera="MPU", step="mpu", source="mpu")
    if not keep_raw:
        os.remove(vp)
    return name, f"{n} kare, yüz %{100 * rate:.0f}"


def mpu_pairs():
    """Figshare'deki dosyalar sırayla (csv, video) çiftleri halinde."""
    import requests
    files = requests.get(MPU_FIGSHARE, timeout=60).json()["files"]
    pairs, csv = [], None
    for f in files:
        if f["name"].lower().endswith(".csv"):
            csv = f
        elif csv is not None:
            pairs.append((f, csv))
            csv = None
    return pairs


PURE_HF = "https://huggingface.co/datasets/Thinhnb29/PURE/resolve/main/PURE/"


def job_pure(session, raw_root, out_root, keep_raw):
    dst = os.path.join(out_root, "pure", session + ".npz")
    if os.path.exists(dst):
        return session, "var"
    zp = os.path.join(raw_root, session + ".zip")
    fetch(PURE_HF + session + ".zip", zp)
    n, rate = process_pure(zp, dst, None, person="pure_" + session[:2], camera="PURE", step=session[3:],
                           source="pure")
    if not keep_raw:
        os.remove(zp)
    return session, f"{n} kare, yüz %{100 * rate:.0f}"


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


def job_test_dl(kind, key, raw_root, out_root, sub="test"):
    """Test videolarını Hugging Face'ten indirip işler (ör. Kaggle; yerelde --test ham dosyaları kullanır).
    Ön işleme yereldeki test kümesiyle aynı: tam çözünürlükte Haar, süre sınırı yok."""
    if kind == "ubfc":
        dst = os.path.join(out_root, sub, f"ubfc_{key}.npz")
        if os.path.exists(dst):
            return key, "var"
        sdir = os.path.join(raw_root, "ubfc_test", key)
        fetch(UBFC_HF + key + "/ground_truth.txt", os.path.join(sdir, "ground_truth.txt"))
        fetch(UBFC_HF + key + "/vid.avi", os.path.join(sdir, "vid.avi"))
        n, rate = process_ubfc(sdir, dst, person=key, camera="C920", step="ubfc", source="ubfc")
        os.remove(os.path.join(sdir, "vid.avi"))
        return key, f"{n} kare, yüz %{100 * rate:.0f}"
    row = key
    name = os.path.splitext(os.path.basename(row["video"]))[0]
    dst = os.path.join(out_root, sub, f"mcd_{name}.npz")
    if os.path.exists(dst):
        return name, "var"
    for rel in (row["meta"], row["ppg_sync"], row["video"]):
        fetch(MCD_HF + rel, os.path.join(raw_root, rel))
    n, rate = process_mcd(os.path.join(raw_root, row["video"]), os.path.join(raw_root, row["meta"]),
                          os.path.join(raw_root, row["ppg_sync"]), dst, None, person=int(row["patient_id"]),
                          camera=row["camera"], step=row["step"], source="mcd")
    os.remove(os.path.join(raw_root, row["video"]))
    return name, f"{n} kare, yüz %{100 * rate:.0f}"


def _init_worker():
    cv2.setNumThreads(1)  # çok süreçte OpenCV iş parçacıkları CPU'yu boğmasın


# ------------------------------------------------------------------ MMPD, VIPL-HR, COHFACE (Hugging Face kopyaları)
# Kopyalar erişim onaylı (gated): HF hesabıyla sayfada istek gönderilip onay beklenir, indirmede HF_TOKEN gerekir.
# Her veri setinde numarası 5'e bölünen kişiler ayrı test klasörüne (test_<kaynak>) gider, eğitime hiç girmez:
# MMPD ve VIPL-HR (kaynak 4) gerçek telefon kamerası videoları -> ilk telefon testi.
MMPD_HF, VIPL_HF, COHFACE_HF = "WeiQian98/mini_MMPD", "WeiQian98/VIPL-HR", "WeiQian98/COHFACE"
VIPL_SOURCES = ("source1", "source2", "source4")  # source3 kızılötesi (renksiz): RGB modele uygun değil
VIPL_ORDER = ("source4", "source1", "source2")    # indirme sırası: telefon 0.7 GB, webcam 7.6 GB, RealSense 33 GB


def is_new_test(person_no):
    return int(person_no) % 5 == 0


def hf_token():
    tok = os.environ.get("HF_TOKEN")
    p = os.path.join(os.path.expanduser("~"), ".cache", "huggingface", "token")
    if not tok and os.path.exists(p):
        tok = open(p).read().strip()
    return tok


def hf_url(repo, path):
    from urllib.parse import quote
    return f"https://huggingface.co/datasets/{repo}/resolve/main/{quote(path)}"


def hf_files(repo):
    """Kopyadaki dosya listesi; erişim yoksa (istek onaylanmadı / HF_TOKEN yok) uyarı ve boş liste."""
    import requests
    s = requests.get(f"https://huggingface.co/api/datasets/{repo}", timeout=60).json().get("siblings", [])
    files = [x["rfilename"] for x in s]
    probe = next((f for f in files if not f.startswith(".")), None)
    tok = hf_token()
    r = requests.head(hf_url(repo, probe), headers={"Authorization": f"Bearer {tok}"} if tok else {},
                      allow_redirects=True, timeout=60) if probe else None
    if r is None or r.status_code in (401, 403):
        print(f"{repo}: erişim yok — huggingface.co/datasets/{repo} sayfasında erişim isteyin, onaydan sonra HF_TOKEN "
              "verin. Atlanıyor.", flush=True)
        return []
    return files


def _frames_bgr_from_rgb(video, upscale=1):
    for fr in video:
        bgr = cv2.cvtColor(np.ascontiguousarray(fr), cv2.COLOR_RGB2BGR)
        yield cv2.resize(bgr, None, fx=upscale, fy=upscale, interpolation=cv2.INTER_CUBIC) if upscale > 1 else bgr


def _load_mat(path):
    """MATLAB v5 (scipy) ya da v7.3 (HDF5) -> dict; v7.3'te diziler ters eksen sıralı okunur."""
    try:
        from scipy.io import loadmat
        return {k: v for k, v in loadmat(path).items() if not k.startswith("__")}
    except NotImplementedError:
        import h5py
        with h5py.File(path, "r") as f:
            return {k: np.array(f[k]).transpose() for k in f.keys() if isinstance(f[k], h5py.Dataset)}


def process_mmpd(mat_path, dst, **info):
    """mini MMPD: 'video' [T,60,80,3] (0-1 ya da 0-255), 'GT_ppg' kare başına PPG (30 fps, Samsung S22 Ultra).
    80x60 karede yüz küçük: Haar için 4x büyütülür. Koşul bilgisi (ışık, hareket, ten rengi...) meta'ya yazılır."""
    m = _load_mat(mat_path)
    video = np.asarray(m["video"])
    if video.ndim == 4 and video.shape[-1] != 3 and video.shape[1] == 3:
        video = video.transpose(0, 2, 3, 1)
    if video.dtype != np.uint8:
        video = np.round(video * (255.0 if video.max() <= 1.5 else 1.0)).clip(0, 255).astype(np.uint8)
    bvp = np.asarray(m["GT_ppg"], dtype=float).reshape(-1)
    n = min(len(video), len(bvp))
    frames, rate = crop_frames(_frames_bgr_from_rgb(video[:n], upscale=4), None, 1, mat_path)
    cond = {k: str(np.asarray(m[k]).reshape(-1)[0]) for k in
            ("light", "motion", "exercise", "skin_color", "gender", "glasser", "hair_cover", "makeup") if k in m}
    t = np.arange(len(frames)) / FS
    f, b = resample(frames, t, bvp[:len(frames)], t)
    sign, corr = label_polarity(f, b)
    save(dst, f, b, rate, polarity=sign, polarity_corr=corr, **cond, **info)
    return len(f), rate, cond


def _read_numbers(path):
    with open(path, encoding="utf-8", errors="ignore") as fh:
        return np.array([float(x) for x in re.findall(r"-?\d+(?:\.\d+)?", fh.read())])


ROTATIONS = (None, cv2.ROTATE_90_CLOCKWISE, cv2.ROTATE_90_COUNTERCLOCKWISE, cv2.ROTATE_180)


def best_rotation(path, n_frames=90, step=15):
    """Videonun ilk saniyelerinde dört yönü dener; Haar'ın en çok yüz bulduğu döndürme (None: döndürme yok).
    VIPL-HR'ın telefon (Huawei P9) videoları yan yatık kaydedilmiş: dik yüz arayan Haar hiç bulamıyor."""
    det = cv2.CascadeClassifier(HAAR)
    hits = dict.fromkeys(range(len(ROTATIONS)), 0)
    for i, bgr in enumerate(_video_frames(path)):
        if i >= n_frames:
            break
        if i % step:
            continue
        sc = 640.0 / max(bgr.shape[:2])
        small = cv2.resize(bgr, None, fx=sc, fy=sc, interpolation=cv2.INTER_AREA) if sc < 1 else bgr
        for k, r in enumerate(ROTATIONS):
            img = small if r is None else cv2.rotate(small, r)
            hits[k] += len(det.detectMultiScale(img)) > 0
    k = max(hits, key=lambda j: (hits[j], j == 0))   # eşitlikte döndürmeme tercih edilir
    return ROTATIONS[k]


def process_vipl(avi, wave_csv, time_txt, dst, max_sec=None, **info):
    """VIPL-HR: video.avi + wave.csv (parmak oksimetresi BVP, 60 Hz) + time.txt (kare zaman damgaları, ms; kaynak
    2'de yok). Zaman damgası yoksa ya da PPG süresi videodan >%5 farklıysa PPG videoya eşit aralıkla yayılır."""
    vfs = cv2.VideoCapture(avi).get(cv2.CAP_PROP_FPS) or 30.0
    rot = best_rotation(avi)
    src = _video_frames(avi) if rot is None else (cv2.rotate(f, rot) for f in _video_frames(avi))
    frames, rate = crop_frames(src, int(max_sec * vfs) + 2 if max_sec else None, 2, avi)
    info["rotation"] = "yok" if rot is None else {cv2.ROTATE_90_CLOCKWISE: "90 sağa",
                                                  cv2.ROTATE_90_COUNTERCLOCKWISE: "90 sola", cv2.ROTATE_180: "180"}[rot]
    wave = pd.read_csv(wave_csv).iloc[:, 0].to_numpy(dtype=float)
    ts = _read_numbers(time_txt) if time_txt and os.path.exists(time_txt) else np.array([])
    if len(ts) >= len(frames) and np.all(np.diff(ts[:len(frames)]) > 0):
        t_v = (ts[:len(frames)] - ts[0]) / 1000.0
    else:
        t_v = np.arange(len(frames)) / vfs
    dur_w = len(wave) / 60.0
    if abs(dur_w - t_v[-1]) / max(t_v[-1], 1e-6) > 0.05:
        t_w = np.linspace(0, t_v[-1], len(wave))      # süreler tutmuyor: UBFC'deki gibi eşit aralıkla yay
    else:
        t_w = np.arange(len(wave)) / 60.0
    f, b = resample(frames, t_v, np.interp(t_v, t_w, wave), t_v)
    sign, corr = label_polarity(f, b)
    save(dst, f, b, rate, polarity=sign, polarity_corr=corr, **info)
    return len(f), rate, info["rotation"]


def process_cohface(avi, hdf5, dst, **info):
    """COHFACE: data.avi (640x480, 20 fps, yoğun MPEG-4 sıkıştırma) + data.hdf5 ('pulse' 256 Hz, 'time' s)."""
    import h5py
    vfs = cv2.VideoCapture(avi).get(cv2.CAP_PROP_FPS) or 20.0
    frames, rate = crop_video(avi, None, 1)
    with h5py.File(hdf5, "r") as h:
        pulse, t_p = np.array(h["pulse"], dtype=float), np.array(h["time"], dtype=float)
    t_v = np.arange(len(frames)) / vfs
    f, b = resample(frames, t_v, np.interp(t_v, t_p - t_p[0], pulse), t_v)
    sign, corr = label_polarity(f, b)
    save(dst, f, b, rate, polarity=sign, polarity_corr=corr, **info)
    return len(f), rate


def _new_dst(out_root, src, person_no, name):
    sub = f"test_{src}" if is_new_test(person_no) else src
    return os.path.join(out_root, sub, f"{src}_{name}.npz")


def job_mmpd(rel, raw_root, out_root, keep_raw):
    sm = re.search(r"p(\d+)_(\d+)\.mat$", rel)
    pno, k = int(sm.group(1)), int(sm.group(2))
    dst = _new_dst(out_root, "mmpd", pno, f"p{pno}_{k}")
    if os.path.exists(dst):
        return rel, "var"
    local = os.path.join(raw_root, rel)
    fetch(hf_url(MMPD_HF, rel), local)
    n, rate, cond = process_mmpd(local, dst, person=f"mmpd_p{pno}", camera="Galaxy S22 Ultra", step=str(k),
                                 source="mmpd")
    if not keep_raw:
        os.remove(local)
    return rel, f"{n} kare, yüz %{100 * rate:.0f}, " + ", ".join(f"{a}={b}" for a, b in cond.items())


def job_vipl(d, raw_root, out_root, keep_raw, max_sec):
    p, v, s = d.split("/")[1:4]
    pno = int(p[1:])
    dst = _new_dst(out_root, "vipl", pno, f"{p}_{v}_{s}")
    if os.path.exists(dst):
        return d, "var"
    local = os.path.join(raw_root, d)
    for fn in ("video.avi", "wave.csv"):
        fetch(hf_url(VIPL_HF, f"{d}/{fn}"), os.path.join(local, fn))
    tt = None
    try:
        fetch(hf_url(VIPL_HF, f"{d}/time.txt"), os.path.join(local, "time.txt"), retries=1)
        tt = os.path.join(local, "time.txt")
    except Exception:  # kaynak 2'de zaman damgası dosyası yok
        pass
    n, rate, rot = process_vipl(os.path.join(local, "video.avi"), os.path.join(local, "wave.csv"), tt, dst, max_sec,
                                person=f"vipl_{p}", camera=s, step=v, source="vipl")
    if not keep_raw:
        import shutil
        shutil.rmtree(local, ignore_errors=True)
    return d, f"{n} kare, yüz %{100 * rate:.0f}, döndürme {rot}"


def job_cohface(d, raw_root, out_root, keep_raw):
    pno, k = (int(x) for x in d.split("/"))
    dst = _new_dst(out_root, "cohface", pno, f"{pno}_{k}")
    if os.path.exists(dst):
        return d, "var"
    local = os.path.join(raw_root, d)
    for fn in ("data.avi", "data.hdf5"):
        fetch(hf_url(COHFACE_HF, f"{d}/{fn}"), os.path.join(local, fn))
    n, rate = process_cohface(os.path.join(local, "data.avi"), os.path.join(local, "data.hdf5"), dst,
                              person=f"cohface_{pno}", camera="COHFACE", step=str(k), source="cohface")
    if not keep_raw:
        import shutil
        shutil.rmtree(local, ignore_errors=True)
    return d, f"{n} kare, yüz %{100 * rate:.0f}"


def new_jobs(kind, n, raw_root, out_root, keep_raw, max_sec):
    """MMPD/VIPL/COHFACE işleri; test kişileri önce (değerlendirme erken hazır olsun)."""
    if kind == "mmpd":
        files = sorted((f for f in hf_files(MMPD_HF) if f.endswith(".mat")),
                       key=lambda f: (not is_new_test(re.search(r"p(\d+)_", f).group(1)), f))
        return [(job_mmpd, (f, os.path.join(raw_root, "mmpd"), out_root, keep_raw)) for f in files[:n]]
    if kind == "vipl":
        dirs = sorted({f.rsplit("/", 1)[0] for f in hf_files(VIPL_HF)
                       if f.endswith("/video.avi") and f.split("/")[3] in VIPL_SOURCES},
                      key=lambda d: (not is_new_test(d.split("/")[1][1:]),       # önce test kişileri,
                                     VIPL_ORDER.index(d.split("/")[3]), d))         # sonra telefon (küçük, en değerli)
        return [(job_vipl, (d, os.path.join(raw_root, "vipl"), out_root, keep_raw, max_sec)) for d in dirs[:n]]
    dirs = sorted({f.rsplit("/", 1)[0] for f in hf_files(COHFACE_HF) if f.endswith("/data.avi")},
                  key=lambda d: (not is_new_test(d.split("/")[0]), d))
    return [(job_cohface, (d, os.path.join(raw_root, "cohface"), out_root, keep_raw)) for d in dirs[:n]]


def process_dlcn(h5_path, dst, **info):
    """DLCN (Kaggle: dalaoplan/rppg-dlcn): 'imgs' [T,128,128,3] RGB yüz kırpıntıları (MTCNN kutusu x1.2, ilk karede
    bulunup sabit; Logitech C922, 30 fps), 'bvp' kare sayısına enterpole edilmiş CMS50E parmak PPG'si.
    Kutu bizimkinden (Haar x1.5) dar: kırpıntı doğrudan 72x72'ye küçültülür (ölçek çeşitliliği)."""
    import h5py
    with h5py.File(h5_path, "r") as h:
        imgs, bvp = h["imgs"], np.array(h["bvp"], dtype=float).reshape(-1)
        n = min(len(imgs), len(bvp))
        frames = np.empty((n, SIZE, SIZE, 3), dtype=np.uint8)
        for k in range(0, n, 300):  # parça parça: gzip'li dizi belleğe toptan alınmaz
            blk = imgs[k:k + 300]
            for j, im in enumerate(blk):
                frames[k + j] = cv2.resize(im, (SIZE, SIZE), interpolation=cv2.INTER_AREA)
    sign, corr = label_polarity(frames, bvp[:n])
    save(dst, frames, bvp[:n].astype(np.float32), 1.0, polarity=sign, polarity_corr=corr, **info)
    return n, sign, corr


def job_dlcn(path, out_root):
    sm = re.search(r"[Pp](\d+)_(\d+)\.h5$", path)
    pno, v = int(sm.group(1)), int(sm.group(2))
    dst = _new_dst(out_root, "dlcn", pno, f"P{pno}_{v}")
    if os.path.exists(dst):
        return os.path.basename(path), "var"
    n, sign, corr = process_dlcn(path, dst, person=f"dlcn_P{pno}", camera="C922",
                                 step=("dinlenme" if v <= 4 else "egzersiz") + f"_v{v}", source="dlcn")
    return os.path.basename(path), f"{n} kare, işaret {'+' if sign > 0 else '-'} (r={corr:.2f})"


def dlcn_files(root, n):
    """Kaggle girdi klasöründe DLCN .h5 dosyaları (büyük/küçük harf duyarsız; Kaggle yolu sürüme göre değişiyor)."""
    files = [p for p in glob.glob(os.path.join(root, "**", "*.h5"), recursive=True)
             if re.fullmatch(r"p\d+_\d+\.h5", os.path.basename(p), re.I)]
    if not files:
        found = sorted(glob.glob(os.path.join(root, "*")) + glob.glob(os.path.join(root, "*", "*")))[:20]
        print(f"DLCN .h5 bulunamadı ({root}); 'Add Input' ile dalaoplan/rppg-dlcn eklendi mi? Klasörde: {found}",
              flush=True)
    files.sort(key=lambda p: (not is_new_test(re.search(r"(\d+)_", os.path.basename(p)).group(1)), p))
    return files[:n]


def run(jobs, workers):
    """İşleri paralel çalıştırır; başarısız iş sayısını döndürür.
    Bir işçi süreç çökerse (ör. çözücü segfault) havuz bozulur ve bekleyen tüm işler düşer; o zaman kalan
    işler her biri kendi tek kullanımlık sürecinde yeniden denenir, böylece çökme yalnızca o işi etkiler."""
    from concurrent.futures.process import BrokenProcessPool
    t0, failed, done, broken = time.time(), 0, set(), False
    with ProcessPoolExecutor(workers, initializer=_init_worker) as ex:
        futs = {ex.submit(fn, *args): i for i, (fn, args) in enumerate(jobs)}
        for fut in as_completed(futs):
            i = futs[fut]
            try:
                name, msg = fut.result()
                done.add(i)
                print(f"  [{len(done)}/{len(jobs)}] {name}: {msg}  ({time.time() - t0:.0f} s)", flush=True)
            except BrokenProcessPool:
                broken = True
            except Exception as e:
                done.add(i)
                failed += 1
                print(f"  [{len(done)}/{len(jobs)}] HATA: {e!r}", flush=True)
    if broken:
        rest = [i for i in range(len(jobs)) if i not in done]
        print(f"  işçi süreç çöktü; kalan {len(rest)} iş tek tek yeniden deneniyor", flush=True)
        for i in rest:
            fn, args = jobs[i]
            with ProcessPoolExecutor(1, initializer=_init_worker) as ex:
                try:
                    name, msg = ex.submit(fn, *args).result()
                    print(f"  [tekrar] {name}: {msg}  ({time.time() - t0:.0f} s)", flush=True)
                except Exception as e:
                    failed += 1
                    print(f"  [tekrar] HATA ({args[0] if args else '?'}): {e!r}", flush=True)
    return failed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/dl")
    ap.add_argument("--raw", default="data/dl/_raw", help="geçici indirme klasörü")
    ap.add_argument("--test", action="store_true", help="yereldeki 28 test videosunu işle")
    ap.add_argument("--test-download", action="store_true", help="28 test videosunu HF'ten indirip işle (Kaggle)")
    ap.add_argument("--test-cameras", default="FullHDwebcam",
                    help="--test-download: test kişilerinin hangi MCD kameraları (ör. IriunWebcam,USBVideo)")
    ap.add_argument("--test-sub", default="test", help="--test-download çıktı alt klasörü")
    ap.add_argument("--no-test-ubfc", dest="test_ubfc", action="store_false", help="--test-download: UBFC'yi atla")
    ap.add_argument("--mcd", type=int, default=0, help="test dışı kaç MCD kişisi")
    ap.add_argument("--mcd-skip", type=int, default=0, help="listede ilk kaç kişiyi atla (parça parça indirmek için)")
    ap.add_argument("--cameras", default="FullHDwebcam,USBVideo,IriunWebcam")
    ap.add_argument("--ubfc", type=int, default=0, help="UBFC'nin test dışı kaç deneği (video başına 1.8 GB)")
    ap.add_argument("--pure", type=int, default=0, help="kaç PURE oturumu (10 kişi x 6 hareket = 60; HF kopyası)")
    ap.add_argument("--ubfcphys", type=int, default=0, help="kaç UBFC-Phys zip'i (kişi başına ~15 GB; HF_TOKEN gerekir)")
    ap.add_argument("--mmpd", type=int, default=0, help="kaç mini MMPD videosu (660; telefon; HF erişimi gerekir)")
    ap.add_argument("--vipl", type=int, default=0, help="kaç VIPL-HR video klasörü (kaynak 1, 2, 4; ~2400)")
    ap.add_argument("--cohface", type=int, default=0, help="kaç COHFACE videosu (164)")
    ap.add_argument("--dlcn", type=int, default=0, help="kaç DLCN videosu (784; --dlcn-dir'deki .h5 dosyaları)")
    ap.add_argument("--dlcn-dir", default="/kaggle/input", help="DLCN .h5 dosyalarının klasörü (alt klasörler aranır)")
    ap.add_argument("--mpu", type=int, default=0, help="kaç MPU-rPPG örnek kaydı (PPG zamanlaması güvenilmez; varsayılan kapalı)")
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

    if a.test_download:
        db_path = os.path.join(a.raw, "db.csv")
        fetch(MCD_HF + "db.csv", db_path)
        db = pd.read_csv(db_path)
        db = db[db.patient_id.isin(MCD_TEST) & db.camera.isin(a.test_cameras.split(","))]
        jobs = [(job_test_dl, ("ubfc", s, a.raw, a.out, a.test_sub)) for s in sorted(UBFC_TEST)] if a.test_ubfc else []
        jobs += [(job_test_dl, ("mcd", r._asdict(), a.raw, a.out, a.test_sub)) for r in db.itertuples()]
        print(f"Test kümesi (indir): {len(jobs)} video")
        failed += run(jobs, max(1, min(a.workers, 2)))

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
    if a.ubfcphys:
        zips = ubfcphys_zips(a.ubfcphys)
        if zips:
            print(f"UBFC-Phys: {len(zips)} zip", flush=True)
            failed += run([(job_ubfcphys, (z, os.path.join(a.raw, "ubfcphys"), a.out, a.keep_raw, a.max_sec))
                           for z in zips], max(1, min(a.workers, 2)))

    if a.dlcn:
        files = dlcn_files(a.dlcn_dir, a.dlcn)
        print(f"dlcn: {len(files)} video ({a.dlcn_dir})", flush=True)
        failed += run([(job_dlcn, (f, a.out)) for f in files], a.workers)

    for kind in ("cohface", "mmpd", "vipl"):
        n = getattr(a, kind)
        if n:
            jobs = new_jobs(kind, n, a.raw, a.out, a.keep_raw, a.max_sec)
            print(f"{kind}: {len(jobs)} video", flush=True)
            failed += run(jobs, a.workers)

    if a.mpu:
        pairs = mpu_pairs()[:a.mpu]
        print(f"MPU-rPPG: {len(pairs)} kayıt", flush=True)
        failed += run([(job_mpu, (pr, os.path.join(a.raw, "mpu"), a.out, a.keep_raw, a.max_sec)) for pr in pairs], 1)

    if a.pure:
        import requests
        tree = requests.get("https://huggingface.co/api/datasets/Thinhnb29/PURE/tree/main/PURE", timeout=60).json()
        sessions = sorted(os.path.basename(x["path"])[:-4] for x in tree if x["path"].endswith(".zip"))[:a.pure]
        print(f"PURE: {len(sessions)} oturum")
        failed += run([(job_pure, (s, os.path.join(a.raw, "pure"), a.out, a.keep_raw)) for s in sessions],
                      max(1, min(a.workers, 2)))  # oturum başına ~700 MB zip
    if failed:
        sys.exit(f"{failed} video başarısız; tekrar çalıştırın (tamamlananlar atlanır)")


if __name__ == "__main__":
    main()
