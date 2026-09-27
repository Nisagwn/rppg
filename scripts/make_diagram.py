#!/usr/bin/env python
"""Rapor için sistem akış şeması (docs/sistem_akisi.png)."""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

INK, INK2, EDGE = "#0b0b0b", "#52514e", "#c9c8c2"
NEW = "#eb6834"
BLUE = "#2a78d6"


def box(ax, x, y, w, h, title, sub, new=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08",
                                fc="#ffffff", ec=NEW if new else EDGE, lw=2 if new else 1.2))
    ax.text(x + w / 2, y + h * 0.64, title, ha="center", va="center", fontsize=9.5, weight="bold", color=INK)
    ax.text(x + w / 2, y + h * 0.3, sub, ha="center", va="center", fontsize=7.6, color=INK2)


def arrow(ax, x1, y1, x2, y2):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=11, color=INK2, lw=1.1))


fig, ax = plt.subplots(figsize=(12, 5.2))
fig.patch.set_facecolor("#fcfcfb")
ax.set_xlim(-0.05, 12)
ax.set_ylim(0, 5.2)
ax.axis("off")
W, H = 2.1, 0.95
row1 = [("Video / Webcam", "kare + zaman damgası", False),
        ("Yüz tespiti + takip", "Haar kaskad · NCC şablon\nalt-piksel · EMA", False),
        ("ROI + cilt maskesi", "YCrCb eşik · morfoloji\nzamanda yumuşak maske", True),
        ("Uzamsal ortalama", "ROI başına R,G,B izi\n30 Hz yeniden örnekleme", False),
        ("rPPG yöntemi", "GREEN · ICA · CHROM\nPOS · LGI", False)]
row2 = [("Ön işleme", "Tarvainen detrend\nButterworth 0.7–3.5 Hz", False),
        ("Pencere spektrumu", "10 s kayan · Hann\nROI başına SNR", False),
        ("SNR ağırlıklı füzyon", "w = SNR^γ\nspektral birleştirme", True),
        ("Viterbi takibi", "hareket farkında güven\n(canlı: ileri Bayes)", True),
        ("Nabız HR(t)", "BPM zaman serisi\nBland-Altman", False)]
xs = [0.15 + i * 2.37 for i in range(5)]
y1, y2 = 3.7, 2.05
for x, (t, s, n) in zip(xs, row1):
    box(ax, x, y1, W, H, t, s, n)
for x, (t, s, n) in zip(xs, row2):
    box(ax, x, y2, W, H, t, s, n)
for i in range(4):
    arrow(ax, xs[i] + W, y1 + H / 2, xs[i + 1], y1 + H / 2)
    arrow(ax, xs[i] + W, y2 + H / 2, xs[i + 1], y2 + H / 2)
arrow(ax, xs[4] + W / 2, y1, xs[0] + W / 2, y2 + H)
# alt kollar: kareler + yüz kutusu -> solunum ve EVM
yb = 0.45
box(ax, xs[0], yb, W, H, "Solunum", "göğüs ROI · Farnebäck\noptik akış · 0.1–0.5 Hz", False)
box(ax, xs[1], yb, W, H, "EVM", "Gauss piramidi · YIQ\nzamansal bant geçiren · ×α", False)
lx = 0.06
ax.plot([xs[0], lx, lx], [y1 + H / 2, y1 + H / 2, yb + H / 2], color=INK2, lw=1.1)
arrow(ax, lx, yb + H / 2, xs[0], yb + H / 2)
ax.plot([lx, lx, xs[1] + W / 2], [yb + H / 2, 0.22, 0.22], color=INK2, lw=1.1)
arrow(ax, xs[1] + W / 2, 0.22, xs[1] + W / 2, yb)
ax.text(lx - 0.02, (y1 + yb + H) / 2 + 0.3, "kareler +\nyüz kutusu", fontsize=7.5, color=INK2, rotation=90, va="center")
ax.add_patch(FancyBboxPatch((7.6, 0.8), 0.35, 0.22, boxstyle="round,pad=0.01", fc="#fff", ec=NEW, lw=2))
ax.text(8.05, 0.91, "özgün katkı", va="center", fontsize=8.5, color=INK2)
ax.add_patch(FancyBboxPatch((9.4, 0.8), 0.35, 0.22, boxstyle="round,pad=0.01", fc="#fff", ec=EDGE, lw=1.2))
ax.text(9.85, 0.91, "klasik adım", va="center", fontsize=8.5, color=INK2)
ax.set_title("Sistem akışı", loc="left", fontsize=12, weight="bold", color=INK)
out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "docs", "sistem_akisi.png")
fig.savefig(out, dpi=150, bbox_inches="tight")
print(out)
