"""灰色关联分析 · 因素影响排序（Python 最小可运行模板）

步骤：确定参考序列 → 初值化（这里用极差标准化）→ 计算绝对差序列 → 关联系数（ρ=0.5）→ 关联度排序。
接口：solve(X, reference) -> 关联度；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_table  # noqa: E402

RHO = 0.5


def build_demo() -> dict:
    X = np.array([[2.1, 3.4, 5.2, 7.8, 9.1, 11.3],
                  [1.2, 2.0, 3.1, 4.4, 5.0, 6.2],
                  [4.5, 4.9, 5.6, 6.8, 7.1, 7.9],
                  [3.0, 3.8, 4.9, 6.5, 7.4, 8.8]], dtype=float).T
    reference = np.array([10.5, 12.0, 13.4, 15.9, 17.2, 19.6], dtype=float)
    return {"X": X, "reference": reference}


def solve(X, reference, rho: float = RHO):
    X = np.asarray(X, float)
    reference = np.asarray(reference, float)
    def scaled(col):
        return (col - col.min()) / (col.max() - col.min())
    target = scaled(reference)
    factors = np.column_stack([scaled(X[:, j]) for j in range(X.shape[1])])
    diff = np.abs(target[:, None] - factors)
    delta_min, delta_max = diff.min(), diff.max()
    coef = (delta_min + rho * delta_max) / (diff + rho * delta_max)
    return coef.mean(axis=0), coef


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    degree, coef = solve(data["X"], data["reference"])
    order = np.argsort(-degree) + 1
    report("灰色关联", 关联度=np.round(degree, 4).tolist(), 排序=order.tolist())
    save_table(__file__, "关联度", {"因素": [f"X{i + 1}" for i in range(len(degree))],
                                    "关联度": np.round(degree, 6)})
