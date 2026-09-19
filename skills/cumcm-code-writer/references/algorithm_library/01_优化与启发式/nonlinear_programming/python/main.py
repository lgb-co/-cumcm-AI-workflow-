"""非线性规划 · 带不等式约束的连续优化（Python 最小可运行模板）

模型：min (x1-1)^2 + (x2-2.5)^2
      s.t. x1 - 2x2 + 2 >= 0，-x1 - 2x2 + 6 >= 0，-x1 + 2x2 + 2 >= 0，x >= 0
接口：solve(x0) -> (x, 最优值)；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from scipy.optimize import minimize

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_table  # noqa: E402


def build_demo() -> dict:
    return {"x0": [0.5, 0.5]}


def objective(x):
    return (x[0] - 1.0) ** 2 + (x[1] - 2.5) ** 2


def constraints(x):
    return np.array([
        x[0] - 2 * x[1] + 2.0,
        -x[0] - 2 * x[1] + 6.0,
        -x[0] + 2 * x[1] + 2.0,
    ])


def solve(x0, multi_start: int = 12, seed: int = 42):
    """多起点避免局部最优：约束以 SLSQP 的 dict 形式给出。"""
    rng = np.random.default_rng(seed)
    cons = [{"type": "ineq", "fun": constraints}]
    bounds = [(0, None), (0, None)]
    best_x, best_f = None, np.inf
    starts = [np.asarray(x0, float)] + [rng.uniform(0, 4, size=2) for _ in range(multi_start - 1)]
    for start in starts:
        res = minimize(objective, start, method="SLSQP", bounds=bounds, constraints=cons,
                       options={"ftol": 1e-10, "maxiter": 300})
        if res.success and res.fun < best_f:
            best_x, best_f = res.x, float(res.fun)
    if best_x is None:
        raise RuntimeError("非线性规划未找到可行解")
    return best_x, best_f


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    x, best = solve(data["x0"])
    report("非线性规划", x1=round(x[0], 4), x2=round(x[1], 4), 最优值=round(best, 6),
           约束余量=round(float(constraints(x).min()), 6))
    save_table(__file__, "最优解", {"变量": ["x1", "x2"], "取值": np.round(x, 6)})
