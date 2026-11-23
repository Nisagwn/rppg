"""Büyük arşiv incelemesi video gövdesini okumamalı veya kişi kimliği uydurmamalı."""
import io
from pathlib import Path
import sys
from zipfile import ZipFile

import numpy as np
from scipy.io import savemat

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from inspect_physdrive_zip import inspect_archive


def test_inventory_reads_only_small_labels(tmp_path, monkeypatch):
    label = io.BytesIO()
    savemat(label, {"BVP": np.arange(100, dtype=np.float32)})
    path = tmp_path / "fixture.zip"
    with ZipFile(path, "w") as archive:
        archive.writestr("PhysDrive/AMH1/AS/RGB.mp4", b"not a real video")
        archive.writestr("PhysDrive/AMH1/AS/IR.mp4", b"not a real video")
        archive.writestr("PhysDrive/AMH1/AS/Label/BVP.mat", label.getvalue())
    original = ZipFile.read

    def guarded_read(self, member, *args, **kwargs):
        assert not member.filename.endswith(".mp4"), "Video gövdesi okunmamalı"
        return original(self, member, *args, **kwargs)

    monkeypatch.setattr(ZipFile, "read", guarded_read)
    result, rows = inspect_archive(path)
    assert result["kinds"] == {"video": 2, "metadata_or_signal": 1}
    assert result["small_label_probes"][0]["variables"]["BVP"]["shape"] == [1, 100]
    assert not result["training_ready"]
    assert len(rows) == 3
    assert list(tmp_path.iterdir()) == [path]  # arşiv dosyaları çıkarılmadı


def test_large_labels_are_not_read_and_nested_zip_is_reported(tmp_path, monkeypatch):
    path = tmp_path / "nested.zip"
    with ZipFile(path, "w") as archive:
        archive.writestr("data.zip", b"nested")
        archive.writestr("Label/BVP.mat", b"too large")

    def forbidden_read(*args, **kwargs):
        raise AssertionError("Boyut sınırı üzerindeki etiket okunmamalı")

    monkeypatch.setattr(ZipFile, "read", forbidden_read)
    result, _ = inspect_archive(path, max_label_bytes=3)
    assert result["kinds"]["nested_archive"] == 1
    assert result["small_label_probes"][0]["status"] == "skipped_size_or_encryption"


def test_csv_metadata_and_unreadable_mat_are_reported(tmp_path):
    path = tmp_path / "metadata.zip"
    with ZipFile(path, "w") as archive:
        archive.writestr("a/Recording_Physiological_Data.csv", "time;BVP\n0;1\n1;2\n2;3\n")
        archive.writestr("b/BVP.mat", b"not a MAT file, header is incomplete")
    result, _ = inspect_archive(path)
    csv_probe, mat_probe = result["small_label_probes"]
    assert csv_probe["columns"] == ["time", "BVP"]
    assert csv_probe["delimiter"] == ";"
    assert mat_probe["status"] == "unreadable"


def test_seekable_archive_does_not_read_large_video_payload():
    class CountedStream(io.BytesIO):
        bytes_read = 0

        def read(self, size=-1):
            value = super().read(size)
            self.bytes_read += len(value)
            return value

    stream = CountedStream()
    with ZipFile(stream, "w") as archive:
        archive.writestr("RGB.mp4", bytes(1_000_000))
        archive.writestr("Label/BVP.mat", bytes(3))
    stream.seek(0)
    result, _ = inspect_archive(stream, max_label_bytes=1, archive_name="remote.zip")
    assert result["archive_name"] == "remote.zip"
    assert result["archive_bytes"] > 1_000_000
    assert stream.bytes_read < 50_000
    assert not stream.closed  # Kaynağın ömrü çağırana ait.
