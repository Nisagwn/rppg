#!/usr/bin/env python
"""
Eğitimdeki (Haar x1.5, rPPG-Toolbox) ve uygulamadaki (YuNet -> pico eşdeğeri x1.5, mobile/app.js) model kutusunun
aynı karelerde geometrik karşılaştırması: merkez kayması ve boyut oranı (Haar kutusuna göre), IoU.
Zamansal davranış (yumuşatma, 1 s sabit tutma) dahil değil; o, iki kırpıntıyla model hatası karşılaştırmasında
(dl_evaluate.py --test data/dl/test_app) ölçülür.

    python scripts/crop_compare.py --out results/kirpma_farki [--step 30]
"""
import argparse
import os
import sys

import cv2
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from dl_prepare import BOX_COEF, HAAR, MCD_TEST, AppCropper, _detect  # noqa: E402


def iou(a, b):
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    return inter / ((a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/MCD/db.csv")
    ap.add_argument("--root", default="data/MCD")
    ap.add_argument("--step", type=int, default=30, help="kaç karede bir karşılaştırılır")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    db = pd.read_csv(a.db)
    db = db[db.patient_id.isin(MCD_TEST)]
    haar, app, rows = cv2.CascadeClassifier(HAAR), AppCropper(), []
    for r in db.itertuples():
        cap = cv2.VideoCapture(os.path.join(a.root, r.video))
        i = 0
        while True:
            ok = cap.grab()
            if not ok:
                break
            if i % a.step == 0:
                _, bgr = cap.retrieve()
                rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
                h, f = _detect(haar, rgb, 1), app.detect(rgb)
                if h is not None and f is not None:
                    hb = (h[0], h[1], h[0] + h[2], h[1] + h[3])      # Haar x1.5 (sol üstten büyütülmüş)
                    s = f["s"] * BOX_COEF
                    ab = (f["cx"] - s / 2, f["cy"] - s / 2, f["cx"] + s / 2, f["cy"] + s / 2)
                    hs = h[2]
                    rows.append({"kamera": r.camera, "durum": r.step, "video": os.path.basename(r.video),
                                 "dx": ((ab[0] + ab[2]) - (hb[0] + hb[2])) / 2 / hs, "dy": ((ab[1] + ab[3]) - (hb[1] + hb[3])) / 2 / hs,
                                 "boyut_orani": s / hs, "iou": iou(hb, ab)})
            i += 1
        cap.release()
    df = pd.DataFrame(rows)
    os.makedirs(a.out, exist_ok=True)
    df.to_csv(os.path.join(a.out, "kutular.csv"), index=False)
    t = df.groupby("kamera").agg(kare=("iou", "size"), dx_medyan=("dx", "median"), dy_medyan=("dy", "median"),
                                 boyut_medyan=("boyut_orani", "median"), boyut_p10=("boyut_orani", lambda x: x.quantile(.1)),
                                 boyut_p90=("boyut_orani", lambda x: x.quantile(.9)), iou_medyan=("iou", "median"),
                                 iou_p10=("iou", lambda x: x.quantile(.1))).round(3)
    t.to_csv(os.path.join(a.out, "ozet.csv"))
    print(t.to_string())


if __name__ == "__main__":
    main()
