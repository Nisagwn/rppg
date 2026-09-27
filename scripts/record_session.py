#!/usr/bin/env python
"""
Kendi veri setini kaydetmek için oturum kaydedici (bkz. docs/veri_toplama_protokolu.md).

    python scripts/record_session.py --subject K01 --condition gunisigi_sabit --duration 60

Çıktı klasörü: data/kayitlar/<subject>_<condition>_<zaman>/
    video.avi       kayıpsız FFV1 (desteklenmezse MJPG, uyarı verilir)
    frames.csv      kare_no, zaman_s (monotonik saat) -> FPS dalgalanmasını düzeltmek için
    meta.json       kamera ayarları (gerçek okunan değerler), koşul, notlar
    reference.csv   zaman_s, hr_bpm (referans cihaz okumaları; kayıt sonunda girilir
                    veya akıllı saat/oksimetre dışa aktarımından doldurulur)

Kayıt sırasında: SPACE = referans cihazdaki o anki nabzı yaz (konsola girilir),
q = erken bitir.
"""
import argparse
import csv
import json
import os
import sys
import threading
import time
from datetime import datetime

import cv2

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from rppg.camera import camera_properties, open_camera  # noqa: E402

KOSULLAR = ["gunisigi_sabit", "floresan_sabit", "los_isik", "ekran_isigi",
            "konusma", "bas_hareketi", "egzersiz_sonrasi"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--subject", required=True, help="anonim kod, ör. K01")
    ap.add_argument("--condition", required=True, help=f"ör. {', '.join(KOSULLAR)}")
    ap.add_argument("--duration", type=float, default=60)
    ap.add_argument("--camera", type=int, default=0)
    ap.add_argument("--out", default="data/kayitlar")
    ap.add_argument("--notes", default="")
    ap.add_argument("--no-lock", action="store_true")
    a = ap.parse_args()

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    d = os.path.join(a.out, f"{a.subject}_{a.condition}_{stamp}")
    os.makedirs(d, exist_ok=True)
    cap = open_camera(a.camera, lock_exposure=not a.no_lock)
    ok, f = cap.read()
    if not ok:
        sys.exit("Kameradan kare okunamadı.")
    H, W = f.shape[:2]
    vpath = os.path.join(d, "video.avi")
    writer = cv2.VideoWriter(vpath, cv2.VideoWriter_fourcc(*"FFV1"), 30, (W, H))
    codec = "FFV1"
    if not writer.isOpened():
        writer = cv2.VideoWriter(vpath, cv2.VideoWriter_fourcc(*"MJPG"), 30, (W, H))
        codec = "MJPG"
        print("UYARI: FFV1 kayıpsız codec yok, MJPG (kayıplı) kullanılıyor. Sonuçlar biraz kötüleşebilir.")

    print("Hazırlık: 5 saniye. Yüzünüzü kameraya dönün, sabit durun.")
    t_end_prep = time.perf_counter() + 5
    while time.perf_counter() < t_end_prep:
        ok, f = cap.read()
        v = f.copy()
        cv2.putText(v, f"HAZIRLIK {t_end_prep - time.perf_counter():.0f}", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 200, 255), 2)
        cv2.imshow("kayit", v)
        cv2.waitKey(1)

    refs = []
    pending = []

    def ask(t_press):
        try:
            val = input(f"[{t_press:.1f} s] Referans nabız (BPM): ").strip()
            if val:
                refs.append((t_press, float(val)))
        except (ValueError, EOFError):
            pass
        finally:
            pending.clear()

    frames_csv = open(os.path.join(d, "frames.csv"), "w", newline="")
    fw = csv.writer(frames_csv)
    fw.writerow(["kare_no", "zaman_s"])
    t0 = time.perf_counter()
    i = 0
    print("KAYIT BAŞLADI. SPACE: referans nabız gir, q: bitir")
    while True:
        ok, f = cap.read()
        t = time.perf_counter() - t0
        if not ok or t > a.duration:
            break
        writer.write(f)
        fw.writerow([i, f"{t:.6f}"])
        i += 1
        v = f.copy()
        cv2.circle(v, (20, 20), 8, (0, 0, 255), -1)
        cv2.putText(v, f"KAYIT {t:5.1f}/{a.duration:.0f} s", (36, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        cv2.imshow("kayit", v)
        k = cv2.waitKey(1) & 0xFF
        if k == ord("q"):
            break
        if k == ord(" ") and not pending:
            pending.append(1)
            threading.Thread(target=ask, args=(t,), daemon=True).start()
    frames_csv.close()
    writer.release()
    props = camera_properties(cap)
    cap.release()
    cv2.destroyAllWindows()

    dur = t if i else 0
    fps_real = i / dur if dur else 0
    print(f"\n{i} kare, {dur:.1f} s, gerçek fps ≈ {fps_real:.2f}")
    if not refs:
        print("Kayıt süresince referans girilmedi. Başta/sonda okuduğunuz değerleri girin (boş = atla).")
        for lbl, tt in (("başlangıç", 0.0), ("bitiş", dur)):
            try:
                val = input(f"  {lbl} nabız (BPM): ").strip()
                if val:
                    refs.append((tt, float(val)))
            except (ValueError, EOFError):
                pass
    with open(os.path.join(d, "reference.csv"), "w", newline="") as rf:
        w = csv.writer(rf)
        w.writerow(["zaman_s", "hr_bpm"])
        for tt, hr in sorted(refs):
            w.writerow([f"{tt:.2f}", hr])
    meta = {"subject": a.subject, "condition": a.condition, "notes": a.notes, "video_file": "video.avi",
            "codec": codec, "n_frames": i, "duration_s": dur, "fps_gercek": fps_real,
            "kamera": props, "tarih": stamp}
    json.dump(meta, open(os.path.join(d, "meta.json"), "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"Kaydedildi: {d}")
    if props.get("oto_pozlama") not in (0.25, 1.0):
        print("NOT: Kamera oto-pozlamayı kapatmayı desteklemiyor olabilir; meta.json'a bakın.")


if __name__ == "__main__":
    main()
