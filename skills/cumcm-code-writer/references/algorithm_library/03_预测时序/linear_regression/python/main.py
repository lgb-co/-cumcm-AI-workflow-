"""多元线性回归 · 影响因素建模（Python 最小可运行模板）

模型：y = Xβ + ε，最小二乘估计；输出系数、R²、RMSE 与预测对照。
接口：solve(X, y) -> (系数, R², RMSE)；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_table  # noqa: E402


def build_demo() -> dict:
    rng = np.random.default_rng(42)
    X = rng.normal(size=(60, 3))
    y = 2.5 + X @ np.array([1.2, -0.8, 0.5]) + rng.normal(scale=0.3, size=60)
    return {"X": X, "y": y}


def solve(X, y):
    X = np.asarray(X, float)
    y = np.asarray(y, float)
    design = np.column_stack([np.ones(len(X)), X])
    beta, *_ = np.linalg.lstsq(design, y, rcond=None)
    pred = design @ beta
    ss_res = float(((y - pred) ** 2).sum())
    ss_tot = float(((y - y.mean()) ** 2).sum())
    r2 = 1 - ss_res / ss_tot
    rmse = float(np.sqrt(ss_res / len(y)))
    return beta, r2, rmse, pred


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    beta, r2, rmse, pred = solve(data["X"], data["y"])
    report("多元线性回归", 系数=np.round(beta, 4).tolist(), R2=round(r2, 4), RMSE=round(rmse, 4))
    save_table(__file__, "回归结果", {"样本": np.arange(1, len(pred) + 1),
                                      "实际值": np.round(data["y"], 4), "预测值": np.round(pred, 4)})
