"""QuickEDA — 一行命令，秒出数据探索分析（EDA）报告。

最简用法：
    >>> import quickeda
    >>> quickeda.profile("data.csv")           # 生成 data_report.html
    >>> quickeda.profile("data.csv", "out.html")

或在命令行：
    $ quickeda data.csv -o report.html
"""

from __future__ import annotations

import os
from typing import Any

import pandas as pd

from .profiler import load_data, profile_dataframe
from .report import build_html

__version__ = "0.1.0"
__all__ = ["profile", "profile_dataframe", "load_data", "build_html", "__version__"]


def profile(
    data: "str | pd.DataFrame",
    output: str | None = None,
    *,
    title: str = "数据探查报告",
    open_browser: bool = False,
    **read_kwargs: Any,
) -> str:
    """对数据做画像并写出 HTML 报告，返回报告文件路径。

    参数
    ----
    data: CSV/Excel/Parquet 等文件路径，或一个已经加载好的 DataFrame。
    output: 报告输出路径；缺省时根据输入文件名自动生成 `<name>_report.html`。
    title: 报告标题。
    open_browser: 生成后是否自动用浏览器打开。
    read_kwargs: 透传给 pandas 读取函数（如 sep=";"、encoding="gbk"）。
    """
    if isinstance(data, pd.DataFrame):
        df = data
        default_out = "report.html"
    else:
        df = load_data(data, **read_kwargs)
        default_out = os.path.splitext(os.path.basename(data))[0] + "_report.html"

    output = output or default_out
    result = profile_dataframe(df)
    html_text = build_html(df, result, title=title)

    with open(output, "w", encoding="utf-8") as f:
        f.write(html_text)

    if open_browser:
        import webbrowser

        webbrowser.open("file://" + os.path.abspath(output))
    return output
