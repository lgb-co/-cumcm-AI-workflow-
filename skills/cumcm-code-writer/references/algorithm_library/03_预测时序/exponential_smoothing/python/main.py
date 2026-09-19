"""指数平滑预测 · Holt 线性趋势（Python 最小可运行模板）

模型：水平项与趋势项递推，α、β 由网格搜索最小化拟合 RMSE。
接口：solve(series, steps) -> (预测值, 最优参数, RMSE)；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_table  # noqa: E402


def build_demo() -> dict:
    rng = np.random.default_rng(42)
    t = np.arange(60)
    series = 50 + 0.8 * t + rng.normal(scale=1.5, size=60)
    return {"series": series, "steps": 6}


def holt(series, alpha, beta, steps):
    level, trend = series[0], series[1] - series[0]
    fitted = [level]
    for value in series[1:]:
        last_level = level
        level = alpha * value + (1 - alpha) * (level + trend)
        trend = beta * (level - last_level) + (1 - beta) * trend
        fitted.append(level + trend)
    forecast = [level + (h + 1) * trend for h in range(steps)]
    return np.array(fitted), np.array(forecast)


def solve(series, steps: int):
    series = np.asarray(series, float)
    best = (np.inf, None, None, None)
    for alpha in np.arange(0.05, 0.96, 0.05):
        for beta in np.arange(0.05, 0.96, 0.05):
            fitted, forecast = holt(series, alpha, beta, steps)
            rmse = float(np.sqrt(np.mean((fitted - series) ** 2)))
            if rmse < best[0]:
                best = (rmse, alpha, beta, (fitted, forecast))
    rmse, alpha, beta, (fitted, forecast) = best
    return forecast, (round(float(alpha), 3), round(float(beta), 3)), rmse, fitted


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    forecast, params, rmse, fitted = solve(data["series"], int(data["steps"]))
    report("指数平滑", alpha=params[0], beta=params[1], 拟合RMSE=round(rmse, 4),
           预测值=np.round(forecast, 4).tolist())
    save_table(__file__, "预测结果", {"期数": np.arange(1, int(data["steps"]) + 1), "预测值": np.round(forecast, 4)})
    save_table(__file__, "拟合对照", {"序号": np.arange(len(fitted)), "实际值": np.round(data["series"], 4),
                                      "拟合值": np.round(fitted, 4)})
