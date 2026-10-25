"""Telefon veri kaydı (.rppgrec, mobile/app.js downloadRec) okuyucusu ve uygulama kutusu (dl_prepare.AppCropper) testleri."""
import json
import os
import struct
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from import_own import read_rec  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..")


def write_rec(path, n=95, fps=24.0, ref=72, size=72):
    """app.js downloadRec ile aynı düzen: "RPPGREC1" + uint32 LE başlık uzunluğu + JSON + n x size x size x 3 uint8."""
    t = np.arange(n) / fps
    px = (np.arange(n)[:, None, None, None] % 256 * np.ones((1, size, size, 3))).astype(np.uint8)
    head = {"format": "rppg-rec-1", "n": n, "size": size, "t": t.round(4).tolist(), "box": [[1, 2, 3]] * n,
            "t0_epoch_ms": 1.7e12, "cam": "ön", "result": {"hr": 74.0, "snr": 2.0, "reliable": True}, "ref_bpm": ref}
    hb = json.dumps(head).encode()
    with open(path, "wb") as f:
        f.write(b"RPPGREC1" + struct.pack("<I", len(hb)) + hb + px.tobytes())
    return head, px


def test_read_rec_round_trip(tmp_path):
    head, px = write_rec(tmp_path / "a.rppgrec")
    h, frames = read_rec(str(tmp_path / "a.rppgrec"))
    assert h["n"] == head["n"] and h["ref_bpm"] == 72
    assert frames.shape == (95, 72, 72, 3) and np.array_equal(frames, px)


def test_import_without_waveform_is_test_only(tmp_path):
    """Yalnızca oksimetre değeri: 30 fps'e taşınır, etiket = o nabızda sinüs, eğitimde kullanılmaz (label=sabit_nabiz)."""
    write_rec(tmp_path / "k.rppgrec", n=24 * 12, fps=24.0, ref=72)
    out = tmp_path / "out"
    subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "import_own.py"), str(tmp_path / "k.rppgrec"),
                    "--out", str(out), "--person", "p1"], check=True, capture_output=True)
    m = np.load(out / "own_p1_k.npz")
    assert str(m["label"]) == "sabit_nabiz" and str(m["source"]) == "own"
    frames = np.load(out / "own_p1_k.npy")
    assert abs(len(frames) - 11.96 * 30) < 2 and frames.shape[1:] == (72, 72, 3)
    f = np.fft.rfftfreq(len(m["bvp"]), 1 / 30)[np.argmax(np.abs(np.fft.rfft(m["bvp"])))]
    assert abs(60 * f - 72) < 6


def test_app_cropper_box_is_square_and_held():
    """Kutunun kare olduğu, ~1 s sabit tutulduğu ve yüz bulunmayınca None döndüğü (YuNet gerektirmeyen sahte tespit)."""
    from dl_prepare import AppCropper
    app = AppCropper()
    seq = iter([{"cx": 100.0, "cy": 80.0, "s": 40.0}] + [{"cx": 102.0, "cy": 80.0, "s": 40.0}] * 100)
    app.detect = lambda rgb: next(seq)
    rgb = np.zeros((240, 320, 3), np.uint8)
    boxes = [app(rgb, i / 30)[0] for i in range(20)]
    x0, y0, x1, y1 = boxes[0]
    assert x1 - x0 == y1 - y0 == 60                  # 40 x 1.5
    assert all(b == boxes[0] for b in boxes)         # küçük kayma: 1 s dolmadan kutu değişmez
    app.detect = lambda rgb: None
    assert app(rgb, 10.0)[0] is None                 # 1.5 s'den uzun süre yüz yok
