"""TOPSIS · 逼近理想解排序（Python 最小可运行模板）

步骤：向量归一化 → 加权 → 正/负理想解 → 欧氏距离 → 相对贴近度排序。
接口：solve(X, weight, positive) -> (贴近度, 排名)；运行：python main.py
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
    return {"X": X, "weight": [0.25, 0.35, 0.20, 0.20], "positive": [True, True, False, True]}


def solve(X, weight, positive):
    X = np.asarray(X, float)
    weight = np.asarray(weight, float)
    Z = X / np.sqrt((X ** 2).sum(axis=0, keepdims=True))
    V = Z * weight
    best = np.array([V[:, j].max() if positive[j] else V[:, j].min() for j in range(X.shape[1])])
    worst = np.array([V[:, j].min() if positive[j] else V[:, j].max() for j in range(X.shape[1])])
    d_best = np.sqrt(((V - best) ** 2).sum(axis=1))
    d_worst = np.sqrt(((V - worst) ** 2).sum(axis=1))
    closeness = d_worst / (d_best + d_worst)
    rank = (-closeness).argsort().argsort() + 1
    return closeness, rank


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    closeness, rank = solve(data["X"], data["weight"], data["positive"])
    report("TOPSIS", 贴近度=np.round(closeness, 4).tolist(), 排名=rank.tolist())
    save_table(__file__, "评价排序", {"方案": [f"A{i + 1}" for i in range(len(closeness))],
                                      "贴近度": np.round(closeness, 6), "排名": rank})
