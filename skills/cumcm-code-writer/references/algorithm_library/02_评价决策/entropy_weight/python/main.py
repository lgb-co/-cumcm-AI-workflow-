"""熵权法 · 客观赋权（Python 最小可运行模板）

步骤：正/负向指标极差标准化（补 0.002 避免零值）→ 计算比重 → 熵值 → 差异系数归一化得权重。
接口：solve(X, positive) -> 权重；运行：python main.py
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
    return {"X": X, "positive": [True, True, False, True]}


def normalize(X, positive):
    X = np.asarray(X, float)
    Z = np.empty_like(X)
    for j in range(X.shape[1]):
        col = X[:, j]
        span = col.max() - col.min()
        Z[:, j] = (col - col.min()) / span if positive[j] else (col.max() - col) / span
    return Z + 0.002


def solve(X, positive):
    Z = normalize(X, positive)
    P = Z / Z.sum(axis=0, keepdims=True)
    n = Z.shape[0]
    E = -(P * np.log(P)).sum(axis=0) / np.log(n)
    d = 1 - E
    return d / d.sum(), E


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    weight, entropy = solve(data["X"], data["positive"])
    report("熵权法", 权重=np.round(weight, 4).tolist(), 熵值=np.round(entropy, 4).tolist())
    save_table(__file__, "指标权重", {"指标": [f"X{i + 1}" for i in range(len(weight))],
                                      "熵值": np.round(entropy, 6), "权重": np.round(weight, 6)})
