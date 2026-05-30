"""生成一份带「真实瑕疵」的示例数据集，用来演示 QuickEDA 的报告效果。

故意制造：缺失值、异常值、重复行、强相关列、类别不平衡 —— 这些都是
EDA 报告该一眼看出来的东西。

运行：
    python examples/generate_sample.py
会在当前目录生成 sample_sales.csv
"""

import sys

import numpy as np
import pandas as pd

try:  # Windows 控制台默认 GBK，切到 UTF-8 以免打印中文报错
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

rng = np.random.default_rng(42)
N = 1000

# 基础数值列
age = rng.normal(35, 10, N).clip(18, 80).round().astype(int)
# income 与 age 正相关（制造一对强相关列）
income = (age * 1200 + rng.normal(0, 8000, N)).clip(2000, None).round(2)
# 注入异常值
income[rng.choice(N, 10, replace=False)] *= 8

spend = (income * 0.3 + rng.normal(0, 3000, N)).clip(0, None).round(2)

city = rng.choice(
    ["北京", "上海", "广州", "深圳", "成都", "杭州"],
    N, p=[0.3, 0.25, 0.15, 0.15, 0.1, 0.05],  # 故意不平衡
)
channel = rng.choice(["线上", "线下", "代理"], N, p=[0.6, 0.3, 0.1])
is_member = rng.choice([True, False], N, p=[0.4, 0.6])

date = pd.to_datetime("2024-01-01") + pd.to_timedelta(
    rng.integers(0, 365, N), unit="D"
)

df = pd.DataFrame({
    "user_id": range(1, N + 1),
    "age": age,
    "income": income,
    "spend": spend,
    "city": city,
    "channel": channel,
    "is_member": is_member,
    "signup_date": date,
})

# 注入缺失值
for col, frac in [("income", 0.08), ("city", 0.03), ("spend", 0.05)]:
    idx = rng.choice(N, int(N * frac), replace=False)
    df.loc[idx, col] = np.nan

# 注入重复行
df = pd.concat([df, df.iloc[:15]], ignore_index=True)

df.to_csv("sample_sales.csv", index=False, encoding="utf-8-sig")
print(f"✓ 已生成 sample_sales.csv（{len(df)} 行，含缺失/异常/重复，专门用来演示）")
