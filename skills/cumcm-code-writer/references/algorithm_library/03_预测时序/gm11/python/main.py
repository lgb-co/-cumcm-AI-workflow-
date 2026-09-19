"""灰色预测 GM(1,1)（Python 最小可运行模板）

步骤：级比检验 → 一次累加生成 → 构造 B、Y 求参数 a、b → 还原预测 → 后验差比检验。
接口：solve(series, steps) -> (拟合值, 预测值, 精度指标)；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_table  # noqa: E402


def build_demo() -> dict:
    return {"series": [2.7, 3.1, 3.6, 4.2, 4.9, 5.7, 6.6], "steps": 3}


def solve(series, steps: int):
    x0 = np.asarray(series, float)
    ratio = x0[:-1] / x0[1:]
    n = len(x0)
    low, high = np.exp(-2 / (n + 1)), np.exp(2 / (n + 1))
    ratio_ok = bool(((ratio > low) & (ratio < high)).all())
    x1 = np.cumsum(x0)
    z1 = 0.5 * (x1[1:] + x1[:-1])
    B = np.column_stack([-z1, np.ones(n - 1)])
    Y = x0[1:]
    a, b = np.linalg.lstsq(B, Y, rcond=None)[0]
    fitted = np.concatenate([[x0[0]], (x0[0] - b / a) * (np.exp(-a * np.arange(1, n)) - np.exp(-a * np.arange(0, n - 1)))])
    forecast = (x0[0] - b / a) * (np.exp(-a * np.arange(n, n + steps)) - np.exp(-a * np.arange(n - 1, n + steps - 1)))
    residual = x0 - fitted
    c = float(residual.std(ddof=1) / x0.std(ddof=1))
    return fitted, forecast, float(a), float(b), c, ratio_ok


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    fitted, forecast, a, b, c, ratio_ok = solve(data["series"], int(data["steps"]))
    report("GM(1,1)", a=round(a, 4), b=round(b, 4), 后验差比C=round(c, 4),
           精度="合格" if c < 0.35 else "需检查", 级比检验="通过" if ratio_ok else "不通过",
           预测值=np.round(forecast, 4).tolist())
    save_table(__file__, "拟合与预测", {"序号": [f"第{i}期" for i in range(1, len(fitted) + len(forecast) + 1)],
                                       "类型": ["拟合"] * len(fitted) + ["预测"] * len(forecast),
                                       "数值": np.round(np.concatenate([fitted, forecast]), 4)})
