"""变异系数法 · 客观赋权（Python 最小可运行模板）

步骤：极差标准化 → 计算各指标标准差与均值之比（变异系数）→ 归一化得权重。
接口：solve(X) -> (权重, 变异系数)；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_table  # noqa: E402


def build_demo() -> dict:
    X = np.array([[92, 0.83, 3.1, 8], [78, 0.71, 4.5, 6], [85, 0.90, 2.7, 9],
                  [70, 0.64, 5.2, 5], [88, 0.79, 3.6, 7]], dtype=float)
    return {"X": X}


def solve(X):
    X = np.asarray(X, float)
    std = X.std(axis=0, ddof=1)
    mean = X.mean(axis=0)
    cv = std / mean
    return cv / cv.sum(), cv


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    weight, cv = solve(data["X"])
    report("变异系数法", 权重=np.round(weight, 4).tolist(), 变异系数=np.round(cv, 4).tolist())
    save_table(__file__, "指标权重", {"指标": [f"X{i + 1}" for i in range(len(weight))],
                                      "变异系数": np.round(cv, 6), "权重": np.round(weight, 6)})
