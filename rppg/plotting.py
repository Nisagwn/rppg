"""Rapor şekilleri (matplotlib, Agg)."""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from .metrics import bland_altman  # noqa: E402
from .roi import ROI_NAMES_TR  # noqa: E402

# Doğrulanmış kategorik palet (sabit sıra) ve metin tonları
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"

plt.rcParams.update({
    "figure.facecolor": "#fcfcfb", "axes.facecolor": "#fcfcfb", "savefig.facecolor": "#fcfcfb",
    "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
    "axes.titlecolor": INK, "axes.titleweight": "bold", "axes.titlesize": 11, "font.size": 9.5,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.spines.top": False,
    "axes.spines.right": False, "lines.linewidth": 1.6, "legend.frameon": False,
})


def plot_result(result, traces, ref_hr=None, path="sonuc.png", title=""):
    fs = traces.fps
    t = np.arange(traces.n) / fs
    fig, ax = plt.subplots(4, 1, figsize=(10, 11), gridspec_kw={"height_ratios": [1, 1, 1.4, 1.2]})
    if result.roi_weights is not None:
        roi0 = result.roi_names[int(np.argmax(result.roi_weights.mean(axis=0)))]
    else:
        roi0 = result.roi_names[0] if result.roi_names else next(iter(traces.rgb))
    rgb = traces.rgb[roi0]
    for c, (lab, col) in enumerate(zip("RGB", ["#e34948", "#008300", "#2a78d6"])):
        x = rgb[:, c]
        ax[0].plot(t, (x - x.mean()) / (x.std() + 1e-9) + 3 * (1 - c), color=col, lw=0.9, label=lab)
    ax[0].set_title(f"Ham ROI izleri ({ROI_NAMES_TR.get(roi0, roi0)} — en yüksek ağırlıklı bölge), normalize")
    ax[0].set_yticks([])
    ax[0].legend(loc="upper left", bbox_to_anchor=(1.0, 1.0))
    ax[1].plot(t, result.bvp, color=SERIES[0], lw=0.9)
    ax[1].set_title(f"BVP sinyali — {result.config.method.upper()}")
    ax[1].set_xlim(t[0], min(t[-1], t[0] + 20))
    ax[1].set_xlabel("zaman (s)")
    ext = [result.centers[0], result.centers[-1], result.grid[0], result.grid[-1]]
    ax[2].imshow(result.spec.T, aspect="auto", origin="lower", extent=ext, cmap="Blues")
    ax[2].plot(result.centers, result.hr, color=SERIES[1], lw=2, label="tahmin")
    if ref_hr is not None:
        ax[2].plot(result.centers, ref_hr, color=INK, lw=1.2, ls="--", label="referans")
    ax[2].set_ylim(40, 180)
    ax[2].set_ylabel("BPM")
    ax[2].set_title("Spektrogram ve HR takibi")
    ax[2].legend(loc="upper right")
    ax[2].grid(False)
    ax[3].plot(result.centers, result.hr, color=SERIES[1], label="tahmin")
    if ref_hr is not None:
        ax[3].plot(result.centers, ref_hr, color=INK, ls="--", lw=1.2, label="referans")
    ax[3].set_ylabel("BPM")
    ax[3].set_xlabel("zaman (s)")
    ax[3].set_title("Nabız zaman serisi")
    ax[3].legend(loc="upper right")
    if title:
        fig.suptitle(title, fontweight="bold")
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def plot_roi_weights(result, path, title="ROI ağırlıkları (SNR füzyonu)"):
    if result.roi_weights is None:
        return
    fig, ax = plt.subplots(figsize=(9, 3.4))
    w = result.roi_weights
    bottom = np.zeros(len(w))
    for i, n in enumerate(result.roi_names):
        ax.fill_between(result.centers, bottom, bottom + w[:, i], color=SERIES[i], alpha=0.85,
                        label=ROI_NAMES_TR.get(n, n), lw=0)
        bottom += w[:, i]
    ax.set_ylim(0, 1)
    ax.set_xlabel("zaman (s)")
    ax.set_ylabel("ağırlık")
    ax.set_title(title)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.28), ncol=len(result.roi_names))
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def plot_bland_altman(est, ref, path, title="Bland-Altman"):
    ba = bland_altman(est, ref)
    fig, ax = plt.subplots(figsize=(6, 4.5))
    ax.scatter(ba["mean"], ba["diff"], s=14, color=SERIES[0], alpha=0.6, edgecolor="none")
    for y, lab, ls in [(ba["bias"], f"yanlılık {ba['bias']:.2f}", "-"),
                       (ba["loa_low"], f"−1.96σ {ba['loa_low']:.2f}", "--"),
                       (ba["loa_high"], f"+1.96σ {ba['loa_high']:.2f}", "--")]:
        ax.axhline(y, color=INK2, ls=ls, lw=1)
        ax.text(ax.get_xlim()[1], y, " " + lab, va="center", ha="left", color=INK2, fontsize=8)
    ax.set_xlabel("(tahmin + referans) / 2  [BPM]")
    ax.set_ylabel("tahmin − referans  [BPM]")
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(path, dpi=130, bbox_inches="tight")
    plt.close(fig)


def plot_heatmap(pivot, path, title, fmt="{:.1f}", cbar_label="MAE (BPM)", vmax=None):
    fig, ax = plt.subplots(figsize=(max(7.0, 1.2 + 1.05 * pivot.shape[1]), max(2.8, 0.9 + 0.42 * pivot.shape[0])))
    data = pivot.values.astype(float)
    im = ax.imshow(data, cmap="Blues", aspect="auto", vmin=0, vmax=vmax or np.nanmax(data))
    ax.set_xticks(range(pivot.shape[1]))
    ax.set_xticklabels(pivot.columns, rotation=30, ha="right")
    ax.set_yticks(range(pivot.shape[0]))
    ax.set_yticklabels(pivot.index)
    ax.grid(False)
    thr = (vmax or np.nanmax(data)) * 0.55
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            ax.text(j, i, fmt.format(data[i, j]), ha="center", va="center", fontsize=8,
                    color="white" if data[i, j] > thr else INK)
    cb = fig.colorbar(im, ax=ax, fraction=0.04)
    cb.set_label(cbar_label)
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def plot_bars(labels, values, path, title, ylabel="MAE (BPM)", highlight=None):
    fig, ax = plt.subplots(figsize=(8, 3.8))
    cols = [SERIES[1] if (highlight is not None and i == highlight) else SERIES[0] for i in range(len(values))]
    ax.bar(range(len(values)), values, color=cols, width=0.65)
    for i, v in enumerate(values):
        ax.text(i, v, f"{v:.2f}", ha="center", va="bottom", fontsize=8, color=INK2)
    ax.set_xticks(range(len(values)))
    ax.set_xticklabels(labels, rotation=20, ha="right")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)
