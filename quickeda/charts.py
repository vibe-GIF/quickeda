"""用 matplotlib 画图并编码成 base64，直接内嵌进 HTML，报告就是单文件、可分享。"""

from __future__ import annotations

import base64
import io

import matplotlib

matplotlib.use("Agg")  # 无界面后端，服务器 / CI 上也能跑
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# 统一配色，保证报告观感一致
_ACCENT = "#6366f1"
_ACCENT_EDGE = "#4f46e5"
_DANGER = "#f43f5e"
_GRID = "#eef2f7"
_TEXT = "#475569"
_DPI = 150  # 高清渲染，retina 屏 / README 头图都清晰

try:
    plt.rcParams.update({
        "font.sans-serif": ["Microsoft YaHei", "SimHei", "Arial Unicode MS"],
        "axes.unicode_minus": False,
        "axes.edgecolor": "#cbd5e1",
        "axes.linewidth": 0.8,
        "text.color": _TEXT,
        "axes.labelcolor": _TEXT,
        "xtick.color": _TEXT,
        "ytick.color": _TEXT,
        "figure.facecolor": "white",
    })
except Exception:  # pragma: no cover - 字体缺失时退回默认
    pass


def _fig_to_base64(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=_DPI, bbox_inches="tight",
                facecolor="white", pad_inches=0.06)
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("ascii")


def histogram(series: pd.Series) -> str | None:
    clean = series.dropna()
    if clean.empty:
        return None
    fig, ax = plt.subplots(figsize=(3.4, 2.0))
    ax.hist(
        clean, bins=min(30, max(5, clean.nunique())),
        color=_ACCENT, edgecolor="white", linewidth=0.5, alpha=0.95,
    )
    ax.set_facecolor("white")
    ax.tick_params(labelsize=7, length=0)
    ax.grid(axis="y", color=_GRID, linewidth=1.0, zorder=0)
    ax.set_axisbelow(True)
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    return _fig_to_base64(fig)


def bar_counts(top_values: list[dict]) -> str | None:
    if not top_values:
        return None
    labels = [d["值"][:12] for d in top_values][::-1]
    counts = [d["次数"] for d in top_values][::-1]
    fig, ax = plt.subplots(figsize=(3.4, 2.0))
    bars = ax.barh(labels, counts, color=_ACCENT, alpha=0.95,
                   height=0.66, zorder=3)
    # 在条形末端标注数值，省去读刻度
    for bar, c in zip(bars, counts):
        ax.text(bar.get_width(), bar.get_y() + bar.get_height() / 2,
                f" {c}", va="center", ha="left", fontsize=6.5, color=_TEXT)
    ax.tick_params(labelsize=7, length=0)
    ax.margins(x=0.18)
    ax.grid(axis="x", color=_GRID, linewidth=1.0, zorder=0)
    ax.set_axisbelow(True)
    for spine in ("top", "right", "bottom"):
        ax.spines[spine].set_visible(False)
    ax.set_xticks([])
    return _fig_to_base64(fig)


def correlation_heatmap(corr: pd.DataFrame) -> str | None:
    if corr is None or corr.shape[0] < 2:
        return None
    n = corr.shape[0]
    fig, ax = plt.subplots(figsize=(min(8, 0.62 * n + 1.6), min(7, 0.62 * n + 1.1)))
    # coolwarm 比 RdBu_r 更柔和、现代
    im = ax.imshow(corr.values, cmap="coolwarm", vmin=-1, vmax=1, aspect="auto")
    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    ax.set_xticklabels(corr.columns, rotation=45, ha="right", fontsize=7.5)
    ax.set_yticklabels(corr.columns, fontsize=7.5)
    ax.tick_params(length=0)
    # 细白线分隔格子，更干净
    ax.set_xticks(np.arange(-0.5, n, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, n, 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=2)
    for spine in ax.spines.values():
        spine.set_visible(False)
    if n <= 12:  # 列数不多时标数值，否则太挤
        for i in range(n):
            for j in range(n):
                val = corr.values[i, j]
                ax.text(
                    j, i, f"{val:.2f}", ha="center", va="center",
                    color="white" if abs(val) > 0.55 else "#334155", fontsize=6.5,
                )
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.ax.tick_params(labelsize=6.5, length=0)
    cbar.outline.set_visible(False)
    return _fig_to_base64(fig)


def missing_bar(missing_by_column: dict[str, int], total_rows: int) -> str | None:
    if not missing_by_column:
        return None
    items = sorted(missing_by_column.items(), key=lambda kv: kv[1], reverse=True)[:20]
    labels = [k[:18] for k, _ in items][::-1]
    pct = [v / total_rows * 100 for _, v in items][::-1]
    fig, ax = plt.subplots(figsize=(6, max(2, 0.42 * len(labels) + 0.5)))
    bars = ax.barh(labels, pct, color=_DANGER, alpha=0.92, height=0.6, zorder=3)
    for bar, p in zip(bars, pct):
        ax.text(bar.get_width(), bar.get_y() + bar.get_height() / 2,
                f" {p:.1f}%", va="center", ha="left", fontsize=8, color=_TEXT)
    ax.set_xlabel("缺失比例 (%)", fontsize=8.5)
    ax.tick_params(labelsize=8.5, length=0)
    ax.margins(x=0.12)
    ax.grid(axis="x", color=_GRID, linewidth=1.0, zorder=0)
    ax.set_axisbelow(True)
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    return _fig_to_base64(fig)
