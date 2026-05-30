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
_ACCENT = "#4f46e5"
_GRID = "#e5e7eb"

try:
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS"]
    plt.rcParams["axes.unicode_minus"] = False
except Exception:  # pragma: no cover - 字体缺失时退回默认
    pass


def _fig_to_base64(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=90, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("ascii")


def histogram(series: pd.Series) -> str | None:
    clean = series.dropna()
    if clean.empty:
        return None
    fig, ax = plt.subplots(figsize=(3.2, 2.0))
    ax.hist(clean, bins=min(30, max(5, clean.nunique())), color=_ACCENT, alpha=0.85)
    ax.set_facecolor("white")
    ax.tick_params(labelsize=7)
    ax.grid(axis="y", color=_GRID, linewidth=0.6)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    return _fig_to_base64(fig)


def bar_counts(top_values: list[dict]) -> str | None:
    if not top_values:
        return None
    labels = [d["值"][:12] for d in top_values][::-1]
    counts = [d["次数"] for d in top_values][::-1]
    fig, ax = plt.subplots(figsize=(3.2, 2.0))
    ax.barh(labels, counts, color=_ACCENT, alpha=0.85)
    ax.tick_params(labelsize=7)
    ax.grid(axis="x", color=_GRID, linewidth=0.6)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    return _fig_to_base64(fig)


def correlation_heatmap(corr: pd.DataFrame) -> str | None:
    if corr is None or corr.shape[0] < 2:
        return None
    n = corr.shape[0]
    fig, ax = plt.subplots(figsize=(min(8, 0.6 * n + 1.5), min(7, 0.6 * n + 1)))
    im = ax.imshow(corr.values, cmap="RdBu_r", vmin=-1, vmax=1, aspect="auto")
    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    ax.set_xticklabels(corr.columns, rotation=45, ha="right", fontsize=7)
    ax.set_yticklabels(corr.columns, fontsize=7)
    # 数值标注：列数不多时才标，否则太挤
    if n <= 12:
        for i in range(n):
            for j in range(n):
                val = corr.values[i, j]
                ax.text(
                    j, i, f"{val:.2f}", ha="center", va="center",
                    color="white" if abs(val) > 0.5 else "black", fontsize=6,
                )
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    return _fig_to_base64(fig)


def missing_bar(missing_by_column: dict[str, int], total_rows: int) -> str | None:
    if not missing_by_column:
        return None
    items = sorted(missing_by_column.items(), key=lambda kv: kv[1], reverse=True)[:20]
    labels = [k[:18] for k, _ in items][::-1]
    pct = [v / total_rows * 100 for _, v in items][::-1]
    fig, ax = plt.subplots(figsize=(6, max(2, 0.3 * len(labels))))
    ax.barh(labels, pct, color="#ef4444", alpha=0.85)
    ax.set_xlabel("缺失比例 (%)", fontsize=8)
    ax.tick_params(labelsize=7)
    ax.grid(axis="x", color=_GRID, linewidth=0.6)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    return _fig_to_base64(fig)
