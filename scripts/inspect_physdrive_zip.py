#!/usr/bin/env python
"""PhysDrive ZIP envanteri; videoları açmadan, çıkarmadan ve GPU kullanmadan.

python scripts/inspect_physdrive_zip.py --zip "PhysDrive(Pub).zip" --out PATH
Çıktıları özel tutun. Kişi kimliği, örnekleme hızı veya etiket hizalaması tahmin edilmez.
"""
import argparse
from collections import Counter
import csv
import io
import json
from pathlib import Path, PurePosixPath
from zipfile import ZipFile

from scipy.io import loadmat
from scipy.io.matlab import MatReadError


VIDEO_SUFFIXES = {".mp4", ".avi", ".mov", ".mkv"}


def category(name):
    p = PurePosixPath(name.replace("\\", "/"))
    if p.suffix.lower() in VIDEO_SUFFIXES:
        return "video"
    if p.suffix.lower() in {".mat", ".csv", ".txt", ".json"}:
        return "metadata_or_signal"
    if p.suffix.lower() in {".zip", ".7z", ".rar", ".tar", ".gz"}:
        return "nested_archive"
    return "other"


def inspect_archive(path, max_samples=6, max_label_bytes=2_000_000, archive_name=None):
    if isinstance(path, (str, Path)):
        path = Path(path)
        archive_bytes, name = path.stat().st_size, path.name
    else:
        # HfFileSystem gibi seek destekli kaynak: tüm ZIP'i belleğe/diske indirme.
        position = path.tell()
        archive_bytes = path.seek(0, 2)
        path.seek(position)
        name = archive_name or "remote_archive.zip"
    if max_samples < 0 or max_label_bytes < 1:
        raise ValueError("Örnek sayısı negatif, boyut sınırı sıfır olamaz")
    rows = []
    with ZipFile(path, allowZip64=True) as archive:
        infos = [i for i in archive.infolist() if not i.is_dir()]
        for info in infos:
            rows.append({"path": info.filename, "kind": category(info.filename),
                         "bytes": info.file_size, "compressed_bytes": info.compress_size,
                         "crc32": f"{info.CRC:08x}", "encrypted": bool(info.flag_bits & 1)})
        candidates = [i for i in infos if PurePosixPath(i.filename).name.lower() in
                      {"bvp.mat", "bvp_filt.mat", "hr.mat", "recording_physiological_data.csv"}]
        probes = []
        for info in sorted(candidates, key=lambda i: i.filename)[:max_samples]:
            probe = {"path": info.filename, "bytes": info.file_size}
            if info.file_size > max_label_bytes or info.flag_bits & 1:
                probe["status"] = "skipped_size_or_encryption"
                probes.append(probe)
                continue
            try:
                data = archive.read(info)
                if info.filename.lower().endswith(".mat"):
                    mat = loadmat(io.BytesIO(data))
                    probe["variables"] = {k: {"shape": list(v.shape), "dtype": str(v.dtype)}
                                          for k, v in mat.items() if not k.startswith("__")}
                else:
                    text = data.decode("utf-8-sig")
                    dialect = csv.Sniffer().sniff(text[:8192], delimiters=",;\t")
                    first = next(csv.reader(io.StringIO(text), dialect), [])
                    has_header = csv.Sniffer().has_header(text[:8192])
                    probe.update({"delimiter": dialect.delimiter, "has_header_inferred": has_header,
                                  "columns": first if has_header else [], "first_row_columns": len(first)})
                probe["status"] = "read"
            except (ValueError, OSError, RuntimeError, IndexError, MatReadError, csv.Error) as exc:
                # Bazı MATLAB v7.3 dosyaları HDF5 gerektirir; format doğrulanmadan eğitim yapılmaz.
                probe.update(status="unreadable", error_type=type(exc).__name__)
            probes.append(probe)
    videos = [r["path"] for r in rows if r["kind"] == "video"]
    result = {
        "archive_name": name, "archive_bytes": archive_bytes,
        "files": len(rows), "kinds": dict(Counter(r["kind"] for r in rows)),
        "uncompressed_bytes": sum(r["bytes"] for r in rows),
        "compressed_payload_bytes": sum(r["compressed_bytes"] for r in rows),
        "top_level_entries": sorted({PurePosixPath(r["path"].replace('\\', '/')).parts[0] for r in rows}),
        "video_samples": videos[:12], "small_label_probes": probes,
        "training_ready": False,
        "pending_checks": [
            "Gerçek katılımcı eşlemesi: farklı araç/ışık/oturumlar aynı kişiyi temsil edebilir.",
            "RGB kare zamanları ile BVP zaman ekseni, örnekleme hızı, süre ve polarite doğrulaması.",
            "Kişi bazında sabit eğitim/doğrulama/test ayrımı ve küçük oturumda ön işleme kontrolü.",
            "Kaggle işleme ve veri saklama koşullarının erişim izniyle uyumu.",
        ],
    }
    return result, rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--zip", dest="archive")
    source.add_argument("--hf-repo", help="İzinli özel HF dataset deposu: kullanici/depo")
    parser.add_argument("--hf-file", default="PhysDrive(Pub).zip")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    if args.hf_repo:
        import os
        from huggingface_hub import HfFileSystem
        fs = HfFileSystem(token=os.environ.get("HF_TOKEN"))
        with fs.open(f"datasets/{args.hf_repo}/{args.hf_file}", "rb", block_size=1024 * 1024,
                     cache_type="blockcache") as stream:
            result, rows = inspect_archive(stream, archive_name=PurePosixPath(args.hf_file).name)
    else:
        result, rows = inspect_archive(args.archive)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "physdrive_onkontrol.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (out / "archive_inventory.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["path", "kind", "bytes", "compressed_bytes", "crc32", "encrypted"])
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"Ön kontrol tamamlandı; eğitim başlatılmadı. Raporlar: {out}")


if __name__ == "__main__":
    main()
