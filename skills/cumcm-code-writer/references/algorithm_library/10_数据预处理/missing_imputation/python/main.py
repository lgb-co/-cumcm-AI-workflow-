"""缺失值插补（Python 最小可运行模板）

策略：按列类型选择——数值列用中位数或线性插值，类别列用众数；输出插补前后对照与影响评估。
接口：solve(df, numeric_method) -> (插补后数据, 影响报告)；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_table  # noqa: E402


def build_demo() -> dict:
    rng = np.random.default_rng(42)
    frame = pd.DataFrame({
        "年份": np.arange(2000, 2020),
        "GDP": 1000 + 45 * np.arange(20) + rng.normal(scale=20, size=20),
        "人口": 800 + 6 * np.arange(20) + rng.normal(scale=5, size=20),
        "类别": rng.choice(["甲", "乙", "丙"], size=20),
    })
    frame.loc[[3, 9, 15], "GDP"] = np.nan
    frame.loc[[5, 12], "人口"] = np.nan
    frame.loc[[7], "类别"] = np.nan
    return {"df": frame, "numeric_method": "interpolate"}


def solve(df, numeric_method: str = "interpolate"):
    data = df.copy()
    report_rows = []
    for column in data.columns:
        missing = int(data[column].isna().sum())
        if missing == 0:
            continue
        if pd.api.types.is_numeric_dtype(data[column]):
            if numeric_method == "interpolate":
                data[column] = data[column].interpolate(limit_direction="both")
            else:
                data[column] = data[column].fillna(data[column].median())
            method = "线性插值" if numeric_method == "interpolate" else "中位数"
        else:
            data[column] = data[column].fillna(data[column].mode().iloc[0])
            method = "众数"
        report_rows.append({"字段": column, "缺失数": missing,
                            "缺失率": round(missing / len(data), 4), "插补方法": method})
    impact = []
    for column in df.columns:
        if pd.api.types.is_numeric_dtype(df[column]):
            impact.append({"字段": column, "原始均值": round(float(df[column].mean()), 4),
                           "插补后均值": round(float(data[column].mean()), 4),
                           "原始标准差": round(float(df[column].std(ddof=1)), 4),
                           "插补后标准差": round(float(data[column].std(ddof=1)), 4)})
    return data, report_rows, impact


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    filled, report_rows, impact = solve(data["df"], str(data["numeric_method"]))
    report("缺失值插补", 字段数=len(data["df"].columns), 插补字段数=len(report_rows),
           剩余缺失=int(filled.isna().sum().sum()))
    save_table(__file__, "插补记录", report_rows)
    save_table(__file__, "影响评估", impact)
    save_table(__file__, "插补后数据", filled)
