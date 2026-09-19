"""CRITIC 客观赋权法（Python 最小可运行模板）

思路：权重 = 对比强度（标准差）× 冲突性（1 - 与其他指标的相关性），再归一化。
适合指标间存在相关性的客观赋权，比熵权法更能反映指标冲突。
接口：solve(X, positive) -> (权重, 信息量)；运行：python main.py
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


def solve(X, positive):
    X = np.asarray(X, float)
    Z = np.empty_like(X)
    for j in range(X.shape[1]):
        col = X[:, j]
        span = col.max() - col.min()
        Z[:, j] = (col - col.min()) / span if positive[j] else (col.max() - col) / span
    std = Z.std(axis=0, ddof=1)
    corr = np.corrcoef(Z, rowvar=False)
    conflict = (1 - corr).sum(axis=1)
    information = std * conflict
    return information / information.sum(), information, std, conflict


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    weight, information, std, conflict = solve(data["X"], data["positive"])
    report("CRITIC 赋权", 权重=np.round(weight, 4).tolist(),
           标准差=np.round(std, 4).tolist(), 冲突性=np.round(conflict, 4).tolist())
    save_table(__file__, "指标权重", {"指标": [f"X{i + 1}" for i in range(len(weight))],
                                      "标准差": np.round(std, 6), "冲突性": np.round(conflict, 6),
                                      "信息量": np.round(information, 6), "权重": np.round(weight, 6)})
