#!/usr/bin/env python
"""
Telefon uygulamasının "Veri kaydı (60 s)" dosyalarını (.rppgrec) eğitim/test verisine (data/dl biçimi) çevirir.

Dosya: "RPPGREC1" + başlık uzunluğu (uint32 LE) + JSON başlık + n x 72 x 72 x 3 uint8 kırpıntı (uygulamanın modele
verdiği girdinin aynısı: yüz kutusu x1.5, ham RGB). Başlıkta kare zamanları (s), kutular, uygulamanın sonucu ve
kullanıcının girdiği oksimetre değeri (ref_bpm) var.

Etiket iki türlü olabilir:
  --ppg dalga.csv   oksimetrenin dalga kaydı (ör. CMS50E bilgisayar yazılımı); sütunlar: zaman (UNIX ms) ve değer.
                    Kayıt başı (t0_epoch_ms) ile hizalanır; --lag ile saniye cinsinden kaydırılabilir. EĞİTİMDE kullanılabilir.
  (yoksa)           ref_bpm (ya da --hr) frekansında sinüs: label="sabit_nabiz". Dalganın zamanlaması bilinmediği için
                    eğitimde (Pearson kaybı) KULLANILMAZ; yalnızca test içindir (dl_evaluate referansı = bu nabız).

    python scripts/import_own.py indirilenler/*.rppgrec --out data/dl/test_telefon --person nisa
    python scripts/import_own.py kayit.rppgrec --ppg cms50e.csv --out data/dl/own --person nisa
"""
import argparse
import json
import os
import struct
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from dl_prepare import FS, resample, save  # noqa: E402

MAGIC = b"RPPGREC1"


def read_rec(path):
    with open(path, "rb") as f:
        if f.read(8) != MAGIC:
            raise ValueError(f"{path}: .rppgrec dosyası değil")
        (hl,) = struct.unpack("<I", f.read(4))
        head = json.loads(f.read(hl).decode("utf-8"))
        s = int(head["size"])
        px = np.frombuffer(f.read(), np.uint8)
    n = len(px) // (s * s * 3)
    if n != head["n"]:
        raise ValueError(f"{path}: başlık {head['n']} kare diyor, dosyada {n}")
    return head, px[: n * s * s * 3].reshape(n, s, s, 3)


def read_ppg(path):
    """İlk sütun zaman (UNIX ms), ikinci sütun dalga değeri; başlık satırı olabilir."""
    df = pd.read_csv(path)
    df = df.apply(pd.to_numeric, errors="coerce").dropna()
    return df.iloc[:, 0].to_numpy(float), df.iloc[:, 1].to_numpy(float)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("rec", nargs="+")
    ap.add_argument("--out", required=True)
    ap.add_argument("--person", required=True, help="kişi kimliği (kişiye göre bölme için; gerçek ad yerine takma ad)")
    ap.add_argument("--ppg", default="", help="oksimetre dalga kaydı (yalnızca tek dosya verildiğinde)")
    ap.add_argument("--lag", type=float, default=0.0, help="dalganın kayda göre gecikmesi (s)")
    ap.add_argument("--hr", type=float, default=0.0, help="ref_bpm yoksa kullanılacak nabız")
    a = ap.parse_args()
    if a.ppg and len(a.rec) != 1:
        sys.exit("--ppg yalnızca tek kayıtla kullanılabilir")
    rows = []
    for p in a.rec:
        head, frames = read_rec(p)
        t = np.asarray(head["t"], float)
        gaps = np.diff(t)
        if a.ppg:
            tp, vp = read_ppg(a.ppg)
            te = head["t0_epoch_ms"] + 1000 * (t + a.lag)
            if te[0] < tp[0] or te[-1] > tp[-1]:
                sys.exit(f"{p}: dalga kaydı videoyu kapsamıyor")
            bvp, label, ref = np.interp(te, tp, vp), "dalga", None
        else:
            ref = head.get("ref_bpm") or a.hr
            if not ref:
                print(f"{p}: oksimetre değeri yok (uygulamada Kaydet'e basılmamış); --hr ile verin, atlandı")
                continue
            bvp, label = np.sin(2 * np.pi * ref / 60 * t), "sabit_nabiz"
        f, b = resample(frames, t, bvp, t)
        name = os.path.splitext(os.path.basename(p))[0]
        cam = "telefon_arka" if str(head.get("cam", "")).startswith("arka") else "telefon_on"
        save(os.path.join(a.out, f"own_{a.person}_{name}.npz"), f, b, 1.0, person=a.person, camera=cam, step="own",
             source="own", label=label, ref_bpm=ref or np.nan, app_bpm=head["result"]["hr"], ua=head.get("ua", ""))
        rows.append({"dosya": name, "kare": len(t), "süre_s": round(t[-1], 1), "fps": round((len(t) - 1) / t[-1], 1),
                     "en_uzun_boşluk_s": round(gaps.max(), 2), "etiket": label, "oksimetre": ref,
                     "uygulama": round(head["result"]["hr"], 1), "kamera": cam})
    if rows:
        print(pd.DataFrame(rows).to_string(index=False))
        print(f"{len(rows)} kayıt -> {a.out} (30 fps; {FS:g} Hz ızgara)")


if __name__ == "__main__":
    main()
