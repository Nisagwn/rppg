#!/usr/bin/env python
"""
UBFC-rPPG veri setini resmi Google Drive klasöründen indirir (bkz. docs/03_veri_seti_indirme.md).

    python scripts/download_ubfc.py                          # DATASET_2'den 5 denek
    python scripts/download_ubfc.py --subjects 10            # 10 denek
    python scripts/download_ubfc.py --dataset DATASET_1 --subjects 0   # DATASET_1'in tamamı

İnmiş dosyalar atlanır; yarıda kalırsa aynı komutu tekrar çalıştırın.
Google Drive "Too many users have viewed or downloaded this file" derse dosya kotası
dolmuştur: birkaç saat (en fazla 24 saat) sonra tekrar deneyin ya da tarayıcıdan indirin.
"""
import argparse
import os
import re
import sys

try:
    import gdown
except ImportError:
    sys.exit("gdown kurulu değil: python -m pip install gdown")

FOLDER_ID = "1o0XU4gTIo46YfwaWjIgbtCncc-oF44Xk"  # https://sites.google.com/view/ybenezeth/ubfcrppg


def _subject_key(path):
    m = re.search(r"(\d+)", path.split(os.sep)[1] if os.sep in path else path)
    return int(m.group(1)) if m else 10**6


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="data/UBFC")
    ap.add_argument("--dataset", default="DATASET_2", choices=["DATASET_1", "DATASET_2"])
    ap.add_argument("--subjects", type=int, default=5, help="kaç denek (0 = hepsi)")
    a = ap.parse_args()

    print("Drive klasörü listeleniyor...")
    files = gdown.download_folder(id=FOLDER_ID, skip_download=True, quiet=True)
    files = [f for f in files if f.path.replace("/", os.sep).startswith(a.dataset + os.sep)]
    subjects = sorted({f.path.replace("/", os.sep).split(os.sep)[1] for f in files}, key=_subject_key)
    if a.subjects:
        subjects = subjects[:a.subjects]
    print(f"{a.dataset}: {len(subjects)} denek -> {a.root}")

    ok, failed = 0, []
    for f in files:
        rel = f.path.replace("/", os.sep)
        if rel.split(os.sep)[1] not in subjects:
            continue
        dst = os.path.join(a.root, rel)
        if os.path.exists(dst) and os.path.getsize(dst) > 0:
            ok += 1
            continue
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        print(f"  {rel}")
        try:
            if gdown.download(id=f.id, output=dst + ".part", quiet=False) is None:
                raise RuntimeError("indirilemedi")
            os.replace(dst + ".part", dst)
            ok += 1
        except Exception as e:  # kota dolu, bağlantı hatası
            failed.append(rel)
            print(f"    HATA: {str(e).strip().splitlines()[0] if str(e).strip() else e}")
            if os.path.exists(dst + ".part"):
                os.remove(dst + ".part")

    print(f"\nTamam: {ok} dosya, başarısız: {len(failed)}")
    if failed:
        print("Başarısız dosyalar için birkaç saat sonra aynı komutu tekrar çalıştırın.")
        sys.exit(1)
    print(f"Değerlendirme: python scripts/evaluate_ubfc.py --root {a.root}")


if __name__ == "__main__":
    main()
