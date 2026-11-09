"""Yeni PURE klasör okuyucusunu eski ZIP okuyucusuyla aynı sinyal üzerinde karşılaştır."""
import json
from pathlib import Path
import sys
import zipfile

import cv2
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import dl_prepare as prep


def test_pure_folder_matches_zip_and_ignores_cache(tmp_path, monkeypatch):
    folder = tmp_path / "01-01"
    frames_dir = folder / "01-01"
    frames_dir.mkdir(parents=True)
    timestamps = [1_392_643_993_642_815_000 + i * 33_333_333 for i in range(90)]
    for i, t in enumerate(timestamps):
        cv2.imwrite(str(frames_dir / f"Image{t}.png"), np.full((8, 8, 3), i, np.uint8))
    meta = {"/FullPackage": [{"Timestamp": t, "Value": {"waveform": float(np.sin(i / 4))}}
                              for i, t in enumerate(timestamps)]}
    (folder / "01-01.json").write_text(json.dumps(meta))
    archive = tmp_path / "session.zip"
    with zipfile.ZipFile(archive, "w") as z:
        for p in folder.rglob("*"):
            if p.is_file():
                z.write(p, p.relative_to(folder))
    cache = folder / ".cache"
    cache.mkdir()
    (cache / "metadata.json").write_text("{}")
    monkeypatch.setattr(prep, "crop_frames", lambda frames, *a: (np.stack(list(frames)), 1.0))
    for name, reader, src in [("zip", prep.process_pure, archive),
                               ("folder", prep.process_pure_folder, folder)]:
        reader(src, str(tmp_path / (name + ".npz")), person="pure_01", source="pure")
    np.testing.assert_array_equal(np.load(tmp_path / "zip.npy"), np.load(tmp_path / "folder.npy"))
    with np.load(tmp_path / "zip.npz") as a, np.load(tmp_path / "folder.npz") as b:
        assert a.files == b.files
        for key in a.files:
            np.testing.assert_array_equal(a[key], b[key])


def test_pure_folder_rejects_missing_labels(tmp_path):
    cv2.imwrite(str(tmp_path / "Image123.png"), np.zeros((8, 8, 3), np.uint8))
    with pytest.raises(ValueError, match="PPG JSON"):
        prep.process_pure_folder(tmp_path, str(tmp_path / "result.npz"))
