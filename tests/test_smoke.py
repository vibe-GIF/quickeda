"""最小冒烟测试：保证核心流程不崩，且报告包含关键内容。

运行：pip install pytest && pytest
"""

import numpy as np
import pandas as pd

import quickeda
from quickeda.profiler import profile_dataframe


def _toy_df() -> pd.DataFrame:
    rng = np.random.default_rng(0)
    df = pd.DataFrame({
        "num": rng.normal(0, 1, 200),
        "num2": rng.normal(5, 2, 200),
        "cat": rng.choice(["a", "b", "c"], 200),
        "flag": rng.choice([True, False], 200),
    })
    df.loc[:9, "num"] = np.nan  # 制造缺失
    return df


def test_profile_dataframe_structure():
    result = profile_dataframe(_toy_df())
    assert result["overview"]["列数"] == 4
    assert len(result["columns"]) == 4
    # 缺失列应被记录
    assert "num" in result["missing_by_column"]
    # 数值列应有统计
    num_col = next(c for c in result["columns"] if c["名称"] == "num")
    assert num_col["类型"] == "numeric"
    assert "均值" in num_col["统计"]


def test_profile_writes_html(tmp_path):
    out = tmp_path / "report.html"
    path = quickeda.profile(_toy_df(), str(out), title="测试报告")
    assert out.exists()
    text = out.read_text(encoding="utf-8")
    assert "测试报告" in text
    assert "data:image/png" in text  # 图表已内嵌
    assert path == str(out)


def test_column_kinds():
    result = profile_dataframe(_toy_df())
    kinds = {c["名称"]: c["类型"] for c in result["columns"]}
    assert kinds["num"] == "numeric"
    assert kinds["cat"] == "categorical"
    assert kinds["flag"] == "boolean"
