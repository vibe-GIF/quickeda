"""核心分析引擎:读取数据集并计算各类描述性统计。

输出统一为普通 Python 字典 / 列表，方便 report.py 渲染，也方便单独调用。
"""

from __future__ import annotations

import os
from typing import Any

import numpy as np
import pandas as pd


def load_data(path: str, **read_kwargs: Any) -> pd.DataFrame:
    """根据文件后缀自动选择读取方式，支持 csv / tsv / excel / parquet / json。"""
    ext = os.path.splitext(path)[1].lower()
    if ext in (".csv",):
        return pd.read_csv(path, **read_kwargs)
    if ext in (".tsv", ".txt"):
        read_kwargs.setdefault("sep", "\t")
        return pd.read_csv(path, **read_kwargs)
    if ext in (".xlsx", ".xls"):
        return pd.read_excel(path, **read_kwargs)
    if ext in (".parquet",):
        return pd.read_parquet(path, **read_kwargs)
    if ext in (".json",):
        return pd.read_json(path, **read_kwargs)
    raise ValueError(f"暂不支持的文件格式：{ext}（支持 csv/tsv/xlsx/parquet/json）")


def _human_bytes(num: float) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if num < 1024.0:
            return f"{num:.1f} {unit}"
        num /= 1024.0
    return f"{num:.1f} TB"


def _column_kind(series: pd.Series) -> str:
    """把列归类为 numeric / categorical / datetime / boolean，便于分别统计。"""
    if pd.api.types.is_bool_dtype(series):
        return "boolean"
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"
    if pd.api.types.is_numeric_dtype(series):
        return "numeric"
    return "categorical"


def _overview(df: pd.DataFrame) -> dict[str, Any]:
    n_rows, n_cols = df.shape
    n_cells = n_rows * n_cols
    n_missing = int(df.isna().sum().sum())
    n_duplicates = int(df.duplicated().sum())
    return {
        "行数": n_rows,
        "列数": n_cols,
        "总单元格数": n_cells,
        "缺失单元格数": n_missing,
        "缺失比例": f"{(n_missing / n_cells * 100) if n_cells else 0:.2f}%",
        "重复行数": n_duplicates,
        "内存占用": _human_bytes(df.memory_usage(deep=True).sum()),
    }


def _numeric_stats(series: pd.Series) -> dict[str, Any]:
    clean = series.dropna()
    if clean.empty:
        return {}
    desc = clean.describe()
    q1, q3 = clean.quantile(0.25), clean.quantile(0.75)
    iqr = q3 - q1
    outlier_mask = (clean < q1 - 1.5 * iqr) | (clean > q3 + 1.5 * iqr)
    return {
        "均值": round(float(desc["mean"]), 4),
        "标准差": round(float(desc["std"]), 4) if not np.isnan(desc["std"]) else 0,
        "最小值": round(float(desc["min"]), 4),
        "中位数": round(float(clean.median()), 4),
        "最大值": round(float(desc["max"]), 4),
        "偏度": round(float(clean.skew()), 4) if len(clean) > 2 else 0,
        "异常值数量": int(outlier_mask.sum()),
        "零值数量": int((clean == 0).sum()),
    }


def _categorical_stats(series: pd.Series, top_n: int = 5) -> dict[str, Any]:
    clean = series.dropna()
    vc = clean.value_counts()
    top = [
        {"值": str(idx), "次数": int(cnt), "占比": f"{cnt / len(clean) * 100:.1f}%"}
        for idx, cnt in vc.head(top_n).items()
    ]
    return {
        "唯一值数量": int(clean.nunique()),
        "最常见取值": top,
    }


def _column_profile(series: pd.Series) -> dict[str, Any]:
    kind = _column_kind(series)
    n = len(series)
    n_missing = int(series.isna().sum())
    profile: dict[str, Any] = {
        "名称": str(series.name),
        "类型": kind,
        "原始dtype": str(series.dtype),
        "缺失数量": n_missing,
        "缺失比例": f"{(n_missing / n * 100) if n else 0:.1f}%",
        "唯一值数量": int(series.nunique(dropna=True)),
    }
    if kind == "numeric":
        profile["统计"] = _numeric_stats(series)
    elif kind in ("categorical", "boolean"):
        profile["统计"] = _categorical_stats(series)
    elif kind == "datetime":
        clean = series.dropna()
        if not clean.empty:
            profile["统计"] = {
                "最早": str(clean.min()),
                "最晚": str(clean.max()),
            }
    return profile


def _correlations(df: pd.DataFrame, threshold: float = 0.5) -> dict[str, Any]:
    numeric = df.select_dtypes(include=[np.number])
    if numeric.shape[1] < 2:
        return {"matrix": None, "high_pairs": []}
    corr = numeric.corr(numeric_only=True)
    high_pairs = []
    cols = corr.columns.tolist()
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            val = corr.iloc[i, j]
            if pd.notna(val) and abs(val) >= threshold:
                high_pairs.append(
                    {"列A": cols[i], "列B": cols[j], "相关系数": round(float(val), 3)}
                )
    high_pairs.sort(key=lambda d: abs(d["相关系数"]), reverse=True)
    return {"matrix": corr, "high_pairs": high_pairs}


def profile_dataframe(df: pd.DataFrame) -> dict[str, Any]:
    """对 DataFrame 做完整画像，返回结构化字典。"""
    return {
        "overview": _overview(df),
        "columns": [_column_profile(df[col]) for col in df.columns],
        "correlations": _correlations(df),
        "missing_by_column": {
            str(col): int(df[col].isna().sum())
            for col in df.columns
            if df[col].isna().sum() > 0
        },
    }
