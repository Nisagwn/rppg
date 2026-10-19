#!/usr/bin/env python
"""
Eğitilmiş modellerin birleşimi (ensemble) ve test zamanı artırma (TTA), yeniden eğitim olmadan.

Her test videosunda her model için iki dalga hesaplanır ve önbelleğe yazılır:
  - düz:  ardışık 160 karelik parçalar (dl_evaluate ile aynı)
  - tta:  %50 örtüşmeli parçalar + yatay çevirme ortalaması (predict_video hop=80, flip=True)
Birleşim: modellerin parça başına standartlaştırılmış dalgalarının ortalaması (dalga düzeyinde; nabız düzeyinde
ortalama Viterbi'nin tek tutarlı izini bozar). Çıktı dl_evaluate ile aynı biçimde (grup, video, yöntem, MAE, p5),
böylece scripts/dl_compare.py ile eşleştirilmiş Wilcoxon yapılabilir.

    python scripts/dl_ensemble.py --test data/dl/test --out results/derin_ogrenme/birlesim/test \\
        --models "5. tur=results/derin_ogrenme/kaggle_tur5/last.pth" "7E=results/derin_ogrenme/kaggle_tur7_E/last.pth"
"""
import argparse
import itertools
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from dl_common import CHUNK, build_model, hr_from_bvp, predict_video, reference_hr  # noqa: E402
from dl_evaluate import group_of, table, test_videos  # noqa: E402


def znorm(x):
    return (x - x.mean()) / (x.std() + 1e-8)


def waves(models, test_dir, cache, device):
    """{(model, varyant): {video: dalga}}; önbellekte olan yeniden hesaplanmaz (CPU'da model başına ~10-20 dk)."""
    os.makedirs(cache, exist_ok=True)
    vids = test_videos(test_dir)
    out = {}
    for name, path in models:
        net = None
        for var, kw in (("düz", {}), ("tta", {"hop": CHUNK // 2, "flip": True})):
            d = out.setdefault((name, var), {})
            for p in vids:
                v = os.path.basename(p)[:-4]
                f = os.path.join(cache, f"{name}__{var}__{v}.npy".replace(" ", "_"))
                if os.path.exists(f):
                    d[v] = np.load(f)
                    continue
                if net is None:
                    net = build_model(device, path)
                d[v] = predict_video(net, np.asarray(np.load(p[:-4] + ".npy", mmap_mode="r")), device, **kw)
                np.save(f, d[v])
            print(f"  {name} {var}: {len(d)} video", flush=True)
    return vids, out


def score(vids, wave_of, label):
    rows = []
    for p in vids:
        meta = np.load(p)
        v = os.path.basename(p)[:-4]
        c, hr_a, hr_v = hr_from_bvp(wave_of(v))
        ref = reference_hr(meta["bvp"], c)
        for suffix, hr in (("", hr_a), ("+Viterbi", hr_v)):
            err = np.abs(hr - ref)
            rows.append({"grup": group_of(meta), "video": v.split("_", 1)[1], "yöntem": label + suffix,
                         "MAE": float(err.mean()), "p5": float(100 * np.mean(err <= 5))})
    return rows


def main():
    import torch
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--models", nargs="+", required=True, metavar="AD=YOL")
    ap.add_argument("--cache", default="", help="dalga önbelleği (varsayılan: <out>/dalgalar)")
    a = ap.parse_args()
    torch.set_num_threads(max(1, (os.cpu_count() or 2) - 2))   # GPU kullanılmaz
    device = torch.device("cpu")
    models = [tuple(m.split("=", 1)) for m in a.models]
    vids, W = waves(models, a.test, a.cache or os.path.join(a.out, "dalgalar"), device)

    rows = []
    names = [n for n, _ in models]
    for var in ("düz", "tta"):
        tag = "" if var == "düz" else " TTA"
        for n in names:
            rows += score(vids, lambda v, n=n: W[(n, var)][v], n + tag)
        for k in range(2, len(names) + 1):
            for combo in itertools.combinations(names, k):
                rows += score(vids, lambda v, combo=combo: np.mean([znorm(W[(n, var)][v]) for n in combo], 0),
                              " + ".join(combo) + tag)
    df = pd.DataFrame(rows)
    os.makedirs(a.out, exist_ok=True)
    df.to_csv(os.path.join(a.out, "test_sonuclari.csv"), index=False)
    t = table(df)
    t.round(2).to_csv(os.path.join(a.out, "test_ozet.csv"))
    print(t[t.index.str.endswith("+Viterbi")].round(2).to_string())


if __name__ == "__main__":
    main()
