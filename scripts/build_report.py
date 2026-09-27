#!/usr/bin/env python
"""
Rapor şablonundaki {{TABLO_*}} yer tutucularını deney çıktılarından doldurur,
docs/05_rapor.md ve (pandoc varsa) docs/05_rapor.docx üretir.

    python scripts/build_report.py
"""
import os
import re
import shutil
import subprocess

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DOCS = os.path.join(ROOT, "docs")


def section(md_path, header_prefix):
    """SONUCLAR.md içinden başlığı header_prefix ile başlayan bölümün tablosunu döndürür."""
    if not os.path.exists(md_path):
        return f"*(Henüz üretilmedi: {os.path.relpath(md_path, ROOT)})*"
    txt = open(md_path, encoding="utf-8").read()
    parts = re.split(r"\n(?=## )", txt)
    for p in parts:
        if p.startswith(header_prefix):
            lines = [l for l in p.split("\n")[1:] if l.strip()]
            return "\n".join(lines)
    return "*(tablo bulunamadı)*"


def main():
    syn = os.path.join(ROOT, "results", "synthetic", "SONUCLAR.md")
    mask = os.path.join(ROOT, "results", "maske_deneyi", "SONUCLAR.md")
    s = open(os.path.join(DOCS, "rapor_sablon.md"), encoding="utf-8").read()
    s = s.replace("{{TABLO_A}}", section(syn, "## A."))
    s = s.replace("{{TABLO_B}}", section(syn, "## B."))
    s = s.replace("{{TABLO_D}}", section(syn, "## D."))
    mt = ("Tablo 4a: Ortalama mutlak hata (BPM).\n\n" + section(mask, "## Ortalama mutlak hata") +
          "\n\nTablo 4b: Titreme frekansına kilitlenme oranı (%).\n\n" + section(mask, "## Titreme frekansına"))
    s = s.replace("{{TABLO_MASKE}}", mt)
    out_md = os.path.join(DOCS, "05_rapor.md")
    open(out_md, "w", encoding="utf-8").write(s)
    print("yazıldı:", out_md)
    if shutil.which("pandoc"):
        out_docx = os.path.join(DOCS, "05_rapor.docx")
        cmd = ["pandoc", out_md, "-o", out_docx, "--resource-path", DOCS, "--toc", "--toc-depth=2",
               "-M", "toc-title=İçindekiler"]
        subprocess.run(cmd, check=True, cwd=DOCS)
        print("yazıldı:", out_docx)
    else:
        print("pandoc bulunamadı; .docx üretilmedi (https://pandoc.org/installing.html)")


if __name__ == "__main__":
    main()
