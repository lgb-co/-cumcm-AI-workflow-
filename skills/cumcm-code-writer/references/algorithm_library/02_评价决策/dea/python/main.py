"""DEA · CCR 模型效率评价（Python 最小可运行模板）

对每个决策单元解一个线性规划：max Σ u_r y_rj / Σ v_i x_ij = 1 的分式规划，转成线性形式后用
linprog 求解；效率值=1 表示 DEA 有效。
接口：solve(X, Y) -> 效率值；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from scipy.optimize import linprog

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_table  # noqa: E402


def build_demo() -> dict:
    X = np.array([[20, 30], [25, 28], [30, 35], [22, 26], [28, 32]], dtype=float)  # 投入
    Y = np.array([[60, 40], [55, 45], [70, 42], [58, 38], [65, 48]], dtype=float)   # 产出
    return {"X": X, "Y": Y}


def solve(X, Y):
    X, Y = np.asarray(X, float), np.asarray(Y, float)
    n, m = X.shape
    s = Y.shape[1]
    efficiencies = []
    for j in range(n):
        # 变量 [v(投入权重 m), u(产出权重 s)]；min -Σu y_j，约束 Σv x_j = 1 且 uY - vX <= 0
        c = np.concatenate([np.zeros(m), -Y[j]])
        A_ub = np.hstack([-X, Y])
        b_ub = np.zeros(n)
        A_eq = np.concatenate([X[j], np.zeros(s)]).reshape(1, -1)
        b_eq = [1.0]
        res = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq,
                      bounds=[(0, None)] * (m + s), method="highs")
        efficiencies.append(float(-res.fun) if res.success else np.nan)
    return np.array(efficiencies)


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    efficiency = solve(data["X"], data["Y"])
    report("DEA-CCR", 效率值=np.round(efficiency, 4).tolist(),
           有效单元=int((efficiency > 0.999).sum()))
    save_table(__file__, "效率评价", {"决策单元": [f"DMU{i + 1}" for i in range(len(efficiency))],
                                      "综合效率": np.round(efficiency, 6)})
