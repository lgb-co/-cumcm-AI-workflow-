"""整数规划 · 小规模整数资源分配（Python 最小可运行模板）

模型：max 5 x1 + 4 x2
      s.t. 6 x1 + 4 x2 <= 24，x1 + 2 x2 <= 6，x1, x2 为非负整数
接口：solve(c, A_ub, b_ub) -> (x, 最优值)；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_table  # noqa: E402


def build_demo() -> dict:
    return {"c": [5.0, 4.0], "A_ub": [[6.0, 4.0], [1.0, 2.0]], "b_ub": [24.0, 6.0]}


def solve(c, A_ub, b_ub):
    """milp 求最小：目标取负，integrality=1 表示全整数变量。"""
    constraints = LinearConstraint(np.asarray(A_ub, float), -np.inf, np.asarray(b_ub, float))
    res = milp(c=-np.asarray(c, float), constraints=constraints,
               integrality=np.ones(len(c)), bounds=Bounds(np.zeros(len(c)), np.full(len(c), np.inf)))
    if not res.success:
        raise RuntimeError(f"整数规划未收敛：{res.message}")
    return res.x, -res.fun


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    x, best = solve(data["c"], data["A_ub"], data["b_ub"])
    report("整数规划", x1=int(round(x[0])), x2=int(round(x[1])), 最优值=round(best, 4))
    save_table(__file__, "最优解", {"变量": ["x1", "x2"], "取值": np.round(x, 4)})
