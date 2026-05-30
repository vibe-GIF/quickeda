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
body { font-family: -apple-system, "Segoe UI", "Microsoft YaHei", sans-serif;
       margin: 0; background: #f8fafc; color: #1e293b; line-height: 1.6; }
.container { max-width: 1100px; margin: 0 auto; padding: 32px 24px 80px; }
header { background: linear-gradient(135deg, #4f46e5, #7c3aed); color: #fff;
         padding: 40px 24px; }
header .wrap { max-width: 1100px; margin: 0 auto; }
header h1 { margin: 0 0 4px; font-size: 28px; }
header .sub { opacity: .85; font-size: 14px; }
.cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
         gap: 14px; margin: 24px 0 8px; }
.card { background: #fff; border-radius: 12px; padding: 18px 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,.06); }
.card .k { font-size: 12px; color: #64748b; }
.card .v { font-size: 22px; font-weight: 700; margin-top: 4px; }
h2 { margin: 40px 0 16px; font-size: 20px; border-left: 4px solid #4f46e5;
     padding-left: 12px; }
table { width: 100%; border-collapse: collapse; background: #fff; border-radius: 10px;
        overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,.06); font-size: 13px; }
th, td { padding: 10px 12px; text-align: left; border-bottom: 1px solid #f1f5f9; }
th { background: #f1f5f9; font-weight: 600; color: #475569; }
tr:hover td { background: #fafafe; }
.col-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(330px, 1fr));
            gap: 16px; }
.col-card { background: #fff; border-radius: 12px; padding: 16px;
            box-shadow: 0 1px 3px rgba(0,0,0,.06); }
.col-card h3 { margin: 0 0 2px; font-size: 15px; display: flex;
               justify-content: space-between; align-items: center; }
.badge { font-size: 11px; padding: 2px 8px; border-radius: 999px; font-weight: 600; }
.b-numeric { background: #dbeafe; color: #1d4ed8; }
.b-categorical { background: #dcfce7; color: #15803d; }
.b-datetime { background: #fef3c7; color: #b45309; }
.b-boolean { background: #f3e8ff; color: #7c3aed; }
.col-meta { font-size: 12px; color: #64748b; margin-bottom: 8px; }
.col-card img { width: 100%; border-radius: 6px; margin-top: 8px; }
.stat-row { display: flex; justify-content: space-between; font-size: 12px;
            padding: 2px 0; }
.stat-row .label { color: #64748b; }
.warn { color: #dc2626; font-weight: 600; }
.center-img { text-align: center; }
.center-img img { max-width: 100%; border-radius: 10px;
                  box-shadow: 0 1px 3px rgba(0,0,0,.06); }
footer { text-align: center; color: #94a3b8; font-size: 12px; margin-top: 48px; }
footer a { color: #6366f1; text-decoration: none; }
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
