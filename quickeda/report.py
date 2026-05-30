"""把 profiler 的结构化结果 + charts 的图，拼成一份单文件 HTML 报告。

故意不引入 jinja2 等模板引擎，纯字符串拼接 → 零额外依赖、好读好改。
"""

from __future__ import annotations

import datetime as _dt
import html
from typing import Any

import pandas as pd

from . import charts

_CSS = """
* { box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display",
       "SF Pro Text", "Helvetica Neue", "PingFang SC", "Microsoft YaHei", sans-serif;
       margin: 0; background: #f5f5f7; color: #1d1d1f; line-height: 1.5;
       -webkit-font-smoothing: antialiased; }
.container { max-width: 1040px; margin: 0 auto; padding: 8px 24px 80px; }
header { background: #f5f5f7; padding: 56px 24px 28px; text-align: center; }
header .wrap { max-width: 1040px; margin: 0 auto; }
header h1 { margin: 0 0 8px; font-size: 40px; font-weight: 600;
            letter-spacing: -0.02em; }
header .sub { color: #6e6e73; font-size: 17px; font-weight: 400; }
.cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
         gap: 12px; margin: 20px 0 8px; }
.card { background: #fff; border-radius: 18px; padding: 20px 22px;
        box-shadow: 0 2px 14px rgba(0,0,0,.04); }
.card .k { font-size: 13px; color: #6e6e73; font-weight: 500; }
.card .v { font-size: 26px; font-weight: 600; margin-top: 6px;
           letter-spacing: -0.01em; }
h2 { margin: 52px 0 18px; font-size: 24px; font-weight: 600;
     letter-spacing: -0.01em; }
table { width: 100%; border-collapse: collapse; background: #fff;
        border-radius: 18px; overflow: hidden;
        box-shadow: 0 2px 14px rgba(0,0,0,.04); font-size: 14px; }
th, td { padding: 13px 18px; text-align: left; border-bottom: 1px solid #f0f0f2; }
th { background: #fafafa; font-weight: 600; color: #6e6e73; font-size: 13px; }
tr:last-child td { border-bottom: none; }
tr:hover td { background: #fbfbfd; }
.col-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(310px, 1fr));
            gap: 16px; }
.col-card { background: #fff; border-radius: 18px; padding: 20px;
            box-shadow: 0 2px 14px rgba(0,0,0,.04); }
.col-card h3 { margin: 0 0 3px; font-size: 16px; font-weight: 600; display: flex;
               justify-content: space-between; align-items: center; }
.badge { font-size: 11px; padding: 3px 10px; border-radius: 999px; font-weight: 600;
         letter-spacing: .01em; }
.b-numeric { background: #e8f1fe; color: #0071e3; }
.b-categorical { background: #e3f7ec; color: #1a9c54; }
.b-datetime { background: #fff2e0; color: #c2740a; }
.b-boolean { background: #efeafe; color: #7a5af0; }
.col-meta { font-size: 12.5px; color: #6e6e73; margin-bottom: 10px; }
.col-card img { width: 100%; border-radius: 10px; margin-top: 10px; }
.stat-row { display: flex; justify-content: space-between; font-size: 13px;
            padding: 3px 0; }
.stat-row .label { color: #6e6e73; }
.warn { color: #ff3b30; font-weight: 600; }
.center-img { text-align: center; }
.center-img img { max-width: 100%; border-radius: 18px;
                  box-shadow: 0 2px 14px rgba(0,0,0,.04); background: #fff;
                  padding: 12px; box-sizing: border-box; }
footer { text-align: center; color: #86868b; font-size: 13px; margin-top: 56px; }
footer a { color: #0071e3; text-decoration: none; }
"""


def _esc(x: Any) -> str:
    return html.escape(str(x))


def _stat_card(profile: dict) -> str:
    kind = profile["类型"]
    stat = profile.get("统计", {})
    rows = []

    if kind == "numeric" and stat:
        chart = charts.histogram  # 占位，实际图在下方注入
        for label in ("均值", "标准差", "最小值", "中位数", "最大值", "偏度"):
            rows.append(f'<div class="stat-row"><span class="label">{label}</span>'
                        f'<span>{_esc(stat.get(label, "-"))}</span></div>')
        if stat.get("异常值数量", 0) > 0:
            rows.append(f'<div class="stat-row"><span class="label">异常值(IQR)</span>'
                        f'<span class="warn">{stat["异常值数量"]}</span></div>')
    elif kind in ("categorical", "boolean") and stat:
        for item in stat.get("最常见取值", []):
            rows.append(
                f'<div class="stat-row"><span class="label">{_esc(item["值"])}</span>'
                f'<span>{item["次数"]} ({item["占比"]})</span></div>'
            )
    elif kind == "datetime" and stat:
        for label, val in stat.items():
            rows.append(f'<div class="stat-row"><span class="label">{label}</span>'
                        f'<span>{_esc(val)}</span></div>')
    return "".join(rows)


def _column_section(df: pd.DataFrame, columns: list[dict]) -> str:
    cards = []
    for prof in columns:
        name = prof["名称"]
        kind = prof["类型"]
        img_tag = ""
        if kind == "numeric":
            b64 = charts.histogram(df[name])
            if b64:
                img_tag = f'<img src="data:image/png;base64,{b64}" alt="histogram">'
        elif kind in ("categorical", "boolean"):
            top = prof.get("统计", {}).get("最常见取值", [])
            b64 = charts.bar_counts(top)
            if b64:
                img_tag = f'<img src="data:image/png;base64,{b64}" alt="bar">'

        missing_cls = ' class="warn"' if prof["缺失数量"] > 0 else ""
        cards.append(f"""
        <div class="col-card">
          <h3>{_esc(name)} <span class="badge b-{kind}">{kind}</span></h3>
          <div class="col-meta">
            唯一值 {prof['唯一值数量']} ·
            缺失 <span{missing_cls}>{prof['缺失数量']} ({prof['缺失比例']})</span> ·
            {_esc(prof['原始dtype'])}
          </div>
          {_stat_card(prof)}
          {img_tag}
        </div>""")
    return f'<div class="col-grid">{"".join(cards)}</div>'


def _high_corr_table(pairs: list[dict]) -> str:
    if not pairs:
        return "<p style='color:#64748b'>未发现强相关（|r| ≥ 0.5）的数值列对。</p>"
    rows = "".join(
        f"<tr><td>{_esc(p['列A'])}</td><td>{_esc(p['列B'])}</td>"
        f"<td>{p['相关系数']}</td></tr>"
        for p in pairs
    )
    return (f"<table><thead><tr><th>列 A</th><th>列 B</th><th>相关系数</th></tr>"
            f"</thead><tbody>{rows}</tbody></table>")


def build_html(df: pd.DataFrame, result: dict, title: str = "数据探查报告") -> str:
    ov = result["overview"]
    cards = "".join(
        f'<div class="card"><div class="k">{_esc(k)}</div>'
        f'<div class="v">{_esc(v)}</div></div>'
        for k, v in ov.items()
    )

    corr = result["correlations"]
    heatmap_b64 = charts.correlation_heatmap(corr["matrix"])
    heatmap_html = (
        f'<div class="center-img"><img src="data:image/png;base64,{heatmap_b64}"></div>'
        if heatmap_b64 else
        "<p style='color:#64748b'>数值列不足 2 个，无法计算相关性矩阵。</p>"
    )

    missing_b64 = charts.missing_bar(result["missing_by_column"], ov["行数"])
    missing_html = (
        f'<div class="center-img"><img src="data:image/png;base64,{missing_b64}"></div>'
        if missing_b64 else
        "<p style='color:#64748b'>🎉 没有任何缺失值。</p>"
    )

    now = _dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_esc(title)}</title><style>{_CSS}</style></head>
<body>
<header><div class="wrap">
  <h1>📊 {_esc(title)}</h1>
  <div class="sub">由 QuickEDA 生成 · {now}</div>
</div></header>
<div class="container">
  <h2>① 数据集概览</h2>
  <div class="cards">{cards}</div>

  <h2>② 缺失值分布</h2>
  {missing_html}

  <h2>③ 相关性分析</h2>
  {heatmap_html}
  <h3 style="font-size:15px;margin-top:20px;">强相关列对</h3>
  {_high_corr_table(corr['high_pairs'])}

  <h2>④ 逐列画像（{len(result['columns'])} 列）</h2>
  {_column_section(df, result['columns'])}

  <footer>
    Generated by <a href="https://github.com/vibe-GIF/quickeda">QuickEDA</a> ·
    一行命令，秒出数据分析报告
  </footer>
</div></body></html>"""
