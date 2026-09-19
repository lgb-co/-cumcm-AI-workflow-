"""ARIMA 时间序列预测（Python 最小可运行模板）

步骤：ADF 平稳性检验 → 按 AIC 在给定阶数网格内定阶 → 拟合 → 预测未来若干期并给出置信区间。
接口：solve(series, steps) -> (预测均值, 置信区间, 最优阶数)；运行：python main.py
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_table  # noqa: E402

warnings.filterwarnings("ignore")


def build_demo() -> dict:
    rng = np.random.default_rng(42)
    t = np.arange(120)
    series = 20 + 0.15 * t + 3 * np.sin(2 * np.pi * t / 12) + rng.normal(scale=0.8, size=120)
    return {"series": series, "steps": 12, "orders": [(p, d, q) for p in range(3) for d in range(2) for q in range(3)]}


def solve(series, steps: int, orders):
    series = pd.Series(np.asarray(series, float))
    best = None
    for order in orders:
        try:
            fitted = ARIMA(series, order=order).fit()
        except Exception:
            continue
        if best is None or fitted.aic < best[0]:
            best = (float(fitted.aic), order, fitted)
    if best is None:
        raise RuntimeError("所有阶数均无法拟合，检查序列长度与平稳性")
    _, order, model = best
    forecast = model.get_forecast(steps=steps)
    mean = forecast.predicted_mean.to_numpy()
    conf = forecast.conf_int(alpha=0.05).to_numpy()
    return mean, conf, order, float(model.aic)


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    mean, conf, order, aic = solve(data["series"], int(data["steps"]), data["orders"])
    report("ARIMA", 最优阶数=order, AIC=round(aic, 2), 预测首期=round(float(mean[0]), 4),
           预测末期=round(float(mean[-1]), 4))
    save_table(__file__, "预测结果", {"期数": np.arange(1, len(mean) + 1),
                                      "预测值": np.round(mean, 4),
                                      "下界": np.round(conf[:, 0], 4),
                                      "上界": np.round(conf[:, 1], 4)})
