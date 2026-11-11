"""PURE hedef testi MCD grubu altında raporlanmamalı."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from dl_evaluate import group_of


def test_pure_target_has_own_group():
    assert group_of({"source": "pure"}) == "PURE"
    assert group_of({"source": "ubfc"}) == "UBFC"
