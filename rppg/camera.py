"""
Webcam açma yardımcıları.

rPPG için kamera ayarları kritik: otomatik pozlama (AE) ve otomatik beyaz
dengesi (AWB) karelerin parlaklığını/rengini sürekli değiştirir ve nabız
sinyalinden ~10-100 kat büyük bozulmalar yaratır. Burada bunları kapatmayı
DENERİZ; her kamera/sürücü desteklemez, bu yüzden gerçek değerler
okunup kayıt meta verisine yazılır.
"""
from __future__ import annotations

import platform

import cv2


def open_camera(index: int = 0, width: int = 640, height: int = 480, fps: int = 30,
                lock_exposure: bool = True, exposure: float = None):
    system = platform.system()
    if system == "Windows":
        cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)   # DirectShow: ayarlar daha çok destekleniyor
        if not cap.isOpened():
            cap = cv2.VideoCapture(index, cv2.CAP_MSMF)
    elif system == "Darwin":
        cap = cv2.VideoCapture(index, cv2.CAP_AVFOUNDATION)
    else:
        cap = cv2.VideoCapture(index, cv2.CAP_V4L2)
    if not cap.isOpened():
        cap = cv2.VideoCapture(index)
    if not cap.isOpened():
        raise RuntimeError(f"Kamera açılamadı (index={index}). Başka bir uygulama kamerayı kullanıyor olabilir.")
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    cap.set(cv2.CAP_PROP_FPS, fps)
    if lock_exposure:
        # Önce kameranın kendi ayarına oturması için birkaç kare oku, sonra kilitle
        for _ in range(20):
            cap.read()
        if system == "Windows":
            cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)   # DSHOW: 0.25 = manuel
        else:
            cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)      # V4L2: 1 = manuel
        if exposure is not None:
            cap.set(cv2.CAP_PROP_EXPOSURE, exposure)
        cap.set(cv2.CAP_PROP_AUTO_WB, 0)
    return cap


def camera_properties(cap) -> dict:
    props = {
        "genislik": cap.get(cv2.CAP_PROP_FRAME_WIDTH),
        "yukseklik": cap.get(cv2.CAP_PROP_FRAME_HEIGHT),
        "fps_bildirilen": cap.get(cv2.CAP_PROP_FPS),
        "oto_pozlama": cap.get(cv2.CAP_PROP_AUTO_EXPOSURE),
        "pozlama": cap.get(cv2.CAP_PROP_EXPOSURE),
        "oto_beyaz_dengesi": cap.get(cv2.CAP_PROP_AUTO_WB),
        "kazanc": cap.get(cv2.CAP_PROP_GAIN),
        "backend": cap.getBackendName() if hasattr(cap, "getBackendName") else "",
    }
    return {k: (float(v) if isinstance(v, (int, float)) else v) for k, v in props.items()}
