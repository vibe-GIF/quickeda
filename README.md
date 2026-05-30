<div align="center">

# 📊 QuickEDA

**一行命令，秒出数据探索分析报告**

输入一个 CSV，自动生成一份精美、可分享的 HTML 数据分析报告——
概览、缺失值、异常值、分布、相关性，全都帮你看好。

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-orange.svg)](#-参与贡献)

[English](#english) · [快速开始](#-快速开始) · [功能](#-功能特性) · [示例](#-示例)

</div>

---

## 💡 为什么做这个

每次拿到一份新数据，你是不是都要重复写一堆代码：
`df.head()`、`df.info()`、`df.describe()`、`df.isnull().sum()`、画分布图、看相关性……

**QuickEDA 把这些一次性帮你做完**，而且输出的不是一屏 print，而是一份能直接发给同事 / 老师 / 队友的 HTML 报告。

```bash
quickeda data.csv
# ✓ 报告已生成：data_report.html  （耗时 0.42s）
```

## ✨ 功能特性

| | 功能 | 说明 |
|---|---|---|
| 📋 | **数据集概览** | 行列数、内存占用、缺失/重复一目了然 |
| 🕳️ | **缺失值分析** | 自动定位哪些列缺失、缺多少 |
| 📈 | **数值列画像** | 均值/中位数/偏度 + 直方图 + IQR 异常值检测 |
| 🏷️ | **类别列画像** | 唯一值、Top 取值、占比 + 条形图 |
| 🔗 | **相关性分析** | 相关系数热力图 + 自动列出强相关列对 |
| 📄 | **单文件 HTML** | 图表内嵌，一个文件随便发，无需联网 |
| 🇨🇳 | **中文友好** | 报告全中文，图表正确显示中文 |

## 🚀 快速开始

### 安装

```bash
pip install quickeda
```

或从源码安装：

```bash
git clone https://github.com/vibe-GIF/quickeda.git
cd quickeda
pip install -e .
```

### 命令行用法

```bash
# 最简单：生成 data_report.html
quickeda data.csv

# 指定输出 + 标题 + 生成后自动打开浏览器
quickeda data.csv -o report.html -t "销售数据分析" --open

# 读 GBK 编码 / 分号分隔的 CSV
quickeda data.csv --encoding gbk --sep ";"

# 也支持 Excel / Parquet
quickeda data.xlsx
```

### Python 代码里用

```python
import quickeda

# 传文件路径
quickeda.profile("data.csv", "report.html")

# 或直接传一个 DataFrame
import pandas as pd
df = pd.read_csv("data.csv")
quickeda.profile(df, title="我的数据", open_browser=True)
```

## 🎬 示例

仓库自带一个示例数据生成脚本（含缺失值、异常值、重复行、强相关列，专门用来演示）：

```bash
python examples/generate_sample.py   # 生成 sample_sales.csv
quickeda sample_sales.csv --open     # 生成并打开报告
```

报告长这样（节选）：

```
📊 数据探查报告
┌─────────┬─────────┬──────────┬──────────┐
│ 行数     │ 列数     │ 缺失比例   │ 重复行数   │
│ 1015    │ 8       │ 2.01%    │ 15       │
└─────────┴─────────┴──────────┴──────────┘

② 缺失值分布   → income 8% · spend 5% · city 3%
③ 相关性分析   → income × age  r=0.81（强相关）
④ 逐列画像     → 每列附分布图 / 条形图
```

> 💡 想直接看效果？把生成的 `sample_sales_report.html` 用浏览器打开即可。

## 🗺️ Roadmap

- [ ] 支持时间序列趋势图
- [ ] 报告导出 PDF
- [ ] 目标列（target）分组对比分析
- [ ] 英文报告模板切换
- [ ] Jupyter Notebook 内联展示

欢迎在 [Issues](https://github.com/vibe-GIF/quickeda/issues) 提需求 🙌

## 🤝 参与贡献

非常欢迎 PR！无论是修 bug、加功能还是改文档：

1. Fork 本仓库
2. 新建分支 `git checkout -b feature/xxx`
3. 提交 PR

如果这个项目帮到了你，点个 ⭐ Star 是对我最大的支持！

## 📄 License

[MIT](LICENSE) © 2026

---

<a name="english"></a>

## English

**QuickEDA** — One command, instant Exploratory Data Analysis report.

Point it at a CSV and get a polished, shareable single-file HTML report:
dataset overview, missing values, outliers, distributions, and correlations.

```bash
pip install quickeda
quickeda data.csv          # -> data_report.html
```

```python
import quickeda
quickeda.profile("data.csv", "report.html")
```

Supports CSV / TSV / Excel / Parquet / JSON. Zero config. MIT licensed.
If it helps you, a ⭐ would mean a lot!
