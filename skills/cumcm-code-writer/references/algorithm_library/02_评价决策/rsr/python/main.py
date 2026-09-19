"""秩和比 RSR · 综合评价与分档（Python 最小可运行模板）

步骤：指标同向化 → 编秩（高优指标从小到大编秩）→ 加权秩和比 RSR → 按分位数分档。
接口：solve(X, positive, weight) -> (RSR, 排序, 档位)；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_table  # noqa: E402


def build_demo() -> dict:
    X = np.array([[92, 0.83, 3.1, 8], [78, 0.71, 4.5, 6], [85, 0.90, 2.7, 9],
                  [70, 0.64, 5.2, 5], [88, 0.79, 3.6, 7]], dtype=float)
    return {"X": X, "positive": [True, True, False, True], "weight": [0.3, 0.3, 0.2, 0.2]}


def solve(X, positive, weight):
    X = np.asarray(X, float)
    weight = np.asarray(weight, float)
    n, m = X.shape
    ranks = np.zeros((n, m))
    for j in range(m):
        col = X[:, j] if positive[j] else -X[:, j]
        ranks[:, j] = pd.Series(col).rank(method="average").to_numpy()
    rsr = (ranks * weight).sum(axis=1) / n
    order = (-rsr).argsort().argsort() + 1
    # 按 RSR 排序后按 30%/40%/30% 数量比例分档
    sorted_index = np.argsort(rsr)
    grades = np.empty(n, dtype=object)
    cuts = np.cumsum([0.3, 0.4, 0.3]) * n
    labels = ["三档（差）", "二档（中）", "一档（优）"]
    for index, position in enumerate(sorted_index):
        grades[position] = labels[int(np.searchsorted(cuts, index + 0.5, side="right"))]
    return rsr, order, grades


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    rsr, order, grades = solve(data["X"], data["positive"], data["weight"])
    report("秩和比", RSR=np.round(rsr, 4).tolist(), 排序=order.tolist())
    save_table(__file__, "RSR评价", {"方案": [f"A{i + 1}" for i in range(len(rsr))],
                                     "RSR": np.round(rsr, 6), "排序": order, "档位": grades})
