"""Etiket hizalama kuralları (dl_common) ve doğrulama seçimi (dl_train.pick_val)."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import dl_common as c  # noqa: E402
import dl_sync_check as s  # noqa: E402
import dl_train as t  # noqa: E402

Q = {"ok_frac": 0.9, "r_pos": 0.1, "lag_pos": 0}


def test_model_sync_shift_aligns_label():
    """Etiket videodan 12 kare geç kaydedilmiş: tepe -12'de, kaydırma etiketi tahminle hizalar."""
    rng = np.random.default_rng(0)
    t_ = np.arange(1800) / 30.0
    pred = np.sin(2 * np.pi * 1.2 * t_) + 0.2 * rng.standard_normal(len(t_))
    label = c.shift_label(pred, 12)  # etiket[t] = tahmin[t - 12]
    r = s.lag_curve(pred, label)
    snk = {"lag_pos": int(s.LAGS[np.argmax(r)]), "r_pos": float(r.max())}
    assert snk["lag_pos"] == 12
    aligned = c.shift_label(label, c.label_shift(Q, "vipl", "source1", snk))
    assert s.LAGS[np.argmax(s.lag_curve(pred, aligned))] == 0


def test_video_decision_rules():
    good, weak = {"lag_pos": -13, "r_pos": 0.6}, {"lag_pos": 3, "r_pos": 0.2}
    assert c.video_decision(Q, "vipl", "source1", good)
    assert not c.video_decision(Q, "vipl", "source1", weak)
    assert not c.video_decision(Q, "vipl", "source1", None)   # hizalanmamış video eğitime girmez
    assert not c.video_decision(Q, "vipl", "source2", good)   # RealSense tümden çıkar
    assert not c.video_decision(Q, "mmpd", "Galaxy S22 Ultra", good)
    assert c.video_decision(Q, "mcd", "FullHDwebcam")         # eski kaynaklar değişmedi
    assert c.label_shift(Q, "mcd", "USBVideo") == 8


def test_pick_val_balances_sources():
    vids = [{"person": f"mcd_{i}", "source": "mcd", "npz": f"m{i}"} for i in range(3000)]
    vids += [{"person": f"vipl_p{i}", "source": "vipl", "npz": f"v{i}"} for i in range(300)]
    val = t.pick_val(vids, 40)
    counts = {src: sum(v["source"] == src for v in val) for src in ("mcd", "vipl")}
    assert counts == {"mcd": 20, "vipl": 20}
    assert all(t.is_val(v["person"]) for v in val)


def test_pick_val_is_stable_as_data_grows():
    mk = lambda src, i: {"person": f"{src}_{i}", "source": src, "npz": f"{src}{i}"}
    vids = [mk("mcd", i) for i in range(1000)] + [mk("vipl", i) for i in range(200)]
    first = [v["npz"] for v in t.pick_val(vids, 20)]
    vids += [mk("mcd", i) for i in range(1000, 3000)]  # hazırlama sürerken gelenler
    again = [v["npz"] for v in t.pick_val(vids, 20, first)]
    assert again == first


def test_pick_val_separates_cameras():
    mk = lambda cam, i: {"person": f"mcd_{i}", "source": "mcd", "camera": cam, "npz": f"{cam}{i}"}
    vids = [mk(c, i) for c in ("FullHDwebcam", "USBVideo", "IriunWebcam") for i in range(1000)]
    cams = [v["camera"] for v in t.pick_val(vids, 30)]
    assert {c: cams.count(c) for c in set(cams)} == {"FullHDwebcam": 10, "USBVideo": 10, "IriunWebcam": 10}


def test_source_shares():
    vids = [{"source": "mcd", "n": 900}] * 3000 + [{"source": "dlcn", "n": 900}] * 600 + [{"source": "pure", "n": 1800}] * 50
    natural, _ = t.source_shares(vids, {})
    assert abs(natural["mcd"] - 3000 * 900 / (3000 * 900 + 600 * 900 + 50 * 1800)) < 1e-9
    fixed, _ = t.source_shares(vids, {"mcd": 0.7, "dlcn": 0.08, "cohface": 0.03})  # cohface yok: eldekiler arasında
    assert abs(fixed["mcd"] - 0.7 / 0.78) < 1e-9 and fixed["pure"] == 0.0
