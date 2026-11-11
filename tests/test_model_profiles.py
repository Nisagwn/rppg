"""Bir hazır modelin çıkarım profili mevcut modelin ayarlarını değiştirmemeli."""
from pathlib import Path
import sys

import pytest

torch = pytest.importorskip("torch")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from dl_common import MD_CONFIG, build_model

pytestmark = pytest.mark.skipif(
    not (ROOT / "external/rPPG-Toolbox/neural_methods/model/FactorizePhys/FactorizePhys.py").exists(),
    reason="Harici Toolbox modelleri kurulu değil")


def test_official_profile_does_not_change_baseline():
    before = dict(MD_CONFIG)
    candidate = build_model(torch.device("cpu"), None, md_config={"MD_FSAM": False})
    baseline = build_model(torch.device("cpu"), None)
    assert not candidate.use_fsam and baseline.use_fsam
    assert candidate.md_config["MD_FSAM"] is False
    assert baseline.md_config["MD_FSAM"] is True
    assert MD_CONFIG == before


def test_wrong_chunk_profile_is_rejected():
    with pytest.raises(ValueError, match="160 kare"):
        build_model(torch.device("cpu"), None, md_config={"FRAME_NUM": 180})


def test_official_ibvp_only_ignores_disabled_attention_weights():
    p = ROOT / "external/rPPG-Toolbox/final_model_release/iBVP_FactorizePhys_FSAM_Res.pth"
    if not p.exists():
        pytest.skip("iBVP hazır ağırlıkları yok")
    model = build_model(torch.device("cpu"), str(p), md_config={"MD_FSAM": False})
    assert model.load_report["missing"] == []
    assert len(model.load_report["unexpected"]) == 4
    assert all(name.startswith("rppg_head.fsam.") for name in model.load_report["unexpected"])
