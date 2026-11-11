"""PURE hedef testi MCD grubu altında raporlanmamalı."""
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from dl_evaluate import group_of


def test_pure_target_has_own_group():
    assert group_of({"source": "pure"}) == "PURE"
    assert group_of({"source": "ubfc"}) == "UBFC"


def test_evaluation_explicit_files_does_not_read_whole_directory(monkeypatch):
    import dl_evaluate as evaluation

    pulse = np.sin(2 * np.pi * 1.2 * np.arange(900) / 30)

    def load(path, **kwargs):
        if str(path).endswith(".npz"):
            return {"source": "ubfc", "bvp": pulse}
        return np.zeros((900, 2, 2, 3), dtype=np.uint8)

    def forbidden_scan(folder):
        raise AssertionError("Açık dosya listesi varken klasör taranmamalı")

    monkeypatch.setattr(evaluation.np, "load", load)
    monkeypatch.setattr(evaluation, "test_videos", forbidden_scan)
    monkeypatch.setattr(evaluation, "predict_video", lambda *args, **kwargs: pulse)
    rows = evaluation.evaluate(object(), "cpu", "unused", "candidate", files=["ubfc_subject1.npz"])
    assert len(rows) == 2
    assert {r["video"] for r in rows} == {"subject1"}
