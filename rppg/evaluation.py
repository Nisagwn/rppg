"""Çoklu konfigürasyon değerlendirmesi (ablasyon çalışması)."""
from __future__ import annotations

from itertools import product
from typing import Dict, List, Sequence

import numpy as np
import pandas as pd

from .io_utils import gt_window_hr
from .metrics import summarize
from .pipeline import Config, estimate
from .signals import Traces

ROI_SETS: Dict[str, tuple] = {
    "alın": ("forehead",),
    "yanaklar": ("left_cheek", "right_cheek"),
    "tüm_yüz": ("full",),
    "alın+yanaklar": ("forehead", "left_cheek", "right_cheek"),
    "4_bölge": ("forehead", "left_cheek", "right_cheek", "full"),
}

METHOD_LIST = ["green", "ica", "chrom", "pos", "lgi"]


def config_grid(methods: Sequence[str] = METHOD_LIST, roi_sets: Dict[str, tuple] = ROI_SETS) -> List[tuple]:
    """(etiketler, Config) listesi.
    Tek ROI: klasik (argmax) ve Viterbi.  Çoklu ROI: {mean, snr} x {argmax, viterbi}."""
    out = []
    for m, (rs_name, rois) in product(methods, roi_sets.items()):
        fusions = ["mean"] if len(rois) == 1 else ["mean", "snr"]
        for fu, tr in product(fusions, ["argmax", "viterbi"]):
            cfg = Config(method=m, rois=rois, fusion=fu, tracker=tr, motion_aware=(tr == "viterbi"))
            labels = {"yöntem": m, "roi": rs_name, "füzyon": fu, "takip": tr}
            out.append((labels, cfg))
    return out


def evaluate(videos: List[dict], configs: List[tuple], win_sec: float = 10.0) -> pd.DataFrame:
    """
    videos: [{"name":..., "traces": Traces, "gt": dict, **ek_etiketler}]
    Her video x konfigürasyon için pencere düzeyi metrikler + video düzeyi hata.
    """
    rows = []
    for v in videos:
        tr: Traces = v["traces"]
        ref_cache = {}
        for labels, cfg in configs:
            try:
                r = estimate(tr, cfg)
            except Exception as e:  # pragma: no cover
                print(f"  ! {v['name']} {cfg.name}: {e}")
                continue
            key = (len(r.centers), cfg.win_sec)
            if key not in ref_cache:
                ref_cache[key] = gt_window_hr(v["gt"], r.centers, cfg.win_sec)
            ref = ref_cache[key]
            s = summarize(r.hr, ref)
            row = {"video": v["name"], **{k: v[k] for k in v if k not in ("name", "traces", "gt")},
                   **labels, "config": cfg.name, **s,
                   "video_hata": abs(r.hr_mean - float(np.mean(ref)))}
            rows.append(row)
    return pd.DataFrame(rows)


def summary(df: pd.DataFrame, by=("yöntem", "roi", "füzyon", "takip")) -> pd.DataFrame:
    g = df.groupby(list(by)).agg(MAE=("MAE", "mean"), RMSE=("RMSE", "mean"), r=("r", "mean"),
                                 **{"≤5BPM%": ("<=5BPM%", "mean")}, video_MAE=("video_hata", "mean"))
    return g.sort_values("MAE").reset_index()
