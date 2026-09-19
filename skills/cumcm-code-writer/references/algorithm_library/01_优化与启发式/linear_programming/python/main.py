"""线性规划 · 生产资源分配（Python 最小可运行模板）

模型：max 50 x1 + 30 x2
      s.t. 4 x1 + 3 x2 <= 120（工时），2 x1 + x2 <= 50（原料），x1, x2 >= 0
接口：solve(c, A_ub, b_ub) -> (x, 最优值)；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from scipy.optimize import linprog

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_table  # noqa: E402


def build_demo() -> dict:
    return {
        "c": [50.0, 30.0],
        "A_ub": [[4.0, 3.0], [2.0, 1.0]],
        "b_ub": [120.0, 50.0],
    }


def solve(c, A_ub, b_ub):
    """标准化形式：linprog 求最小，故对目标取负。"""
    res = linprog(-np.asarray(c, float), A_ub=np.asarray(A_ub, float), b_ub=np.asarray(b_ub, float),
                  bounds=[(0, None)] * len(c), method="highs")
    if not res.success:
        raise RuntimeError(f"线性规划未收敛：{res.message}")
    return res.x, -res.fun


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    x, best = solve(data["c"], data["A_ub"], data["b_ub"])
    report("线性规划", x1=round(x[0], 4), x2=round(x[1], 4), 最优值=round(best, 4))
    save_table(__file__, "最优解", {"变量": ["x1", "x2"], "取值": np.round(x, 4)})
