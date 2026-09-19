"""多项式拟合 · 趋势外推（Python 最小可运行模板）

步骤：最小二乘拟合 1–5 阶多项式 → 用留出法比较 RMSE 选择阶数 → 输出拟合系数与外推值。
接口：solve(x, y, degrees) -> (最优阶数, 系数, RMSE)；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_table  # noqa: E402


def build_demo() -> dict:
    rng = np.random.default_rng(42)
    x = np.linspace(0, 10, 40)
    y = 1.2 * x - 0.08 * x ** 2 + 0.003 * x ** 3 + rng.normal(scale=0.2, size=40)
    return {"x": x, "y": y, "degrees": [1, 2, 3, 4, 5]}


def solve(x, y, degrees, holdout: int = 8):
    x, y = np.asarray(x, float), np.asarray(y, float)
    x_train, y_train = x[:-holdout], y[:-holdout]
    x_test, y_test = x[-holdout:], y[-holdout:]
    results = {}
    for d in degrees:
        coef = np.polyfit(x_train, y_train, d)
        rmse = float(np.sqrt(np.mean((np.polyval(coef, x_test) - y_test) ** 2)))
        results[d] = (rmse, coef)
    best_d = min(results, key=lambda d: results[d][0])
    return best_d, results[best_d][1], results


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    best_d, coef, results = solve(data["x"], data["y"], data["degrees"])
    report("多项式拟合", 最优阶数=best_d, 测试RMSE=round(results[best_d][0], 4),
           系数=np.round(coef, 6).tolist())
    save_table(__file__, "阶数选择", {"阶数": list(results), "测试RMSE": [round(v[0], 6) for v in results.values()]})
    save_table(__file__, "拟合对照", {"x": np.round(data["x"], 4), "实际值": np.round(data["y"], 4),
                                      "拟合值": np.round(np.polyval(coef, data["x"]), 4)})
