"""马尔可夫链预测（Python 最小可运行模板）

步骤：由状态转移频数估计转移矩阵 → 校验行和为 1 → 逐期递推状态分布 → 求平稳分布。
接口：solve(sequence, states, steps) -> (转移矩阵, 各期分布, 平稳分布)；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_table  # noqa: E402


def build_demo() -> dict:
    return {"sequence": [0, 1, 0, 1, 1, 2, 1, 0, 0, 1, 2, 2, 1, 0, 1, 1, 0, 2, 1, 0], "steps": 6}


def solve(sequence, steps: int):
    sequence = list(sequence)
    states = sorted(set(sequence))
    index = {s: i for i, s in enumerate(states)}
    counts = np.zeros((len(states), len(states)))
    for a, b in zip(sequence[:-1], sequence[1:]):
        counts[index[a], index[b]] += 1
    row_sums = counts.sum(axis=1, keepdims=True)
    transition = np.divide(counts, row_sums, out=np.zeros_like(counts), where=row_sums > 0)
    current = np.zeros(len(states))
    current[index[sequence[-1]]] = 1.0
    distributions = [current]
    for _ in range(steps):
        current = current @ transition
        distributions.append(current)
    # 平稳分布：幂迭代到收敛
    stationary = np.ones(len(states)) / len(states)
    for _ in range(500):
        stationary = stationary @ transition
    return transition, np.array(distributions), stationary, states


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    transition, distributions, stationary, states = solve(data["sequence"], int(data["steps"]))
    report("马尔可夫链", 状态数=len(states), 行和校验=np.round(transition.sum(axis=1), 6).tolist(),
           平稳分布=np.round(stationary, 4).tolist())
    save_table(__file__, "转移矩阵", pd.DataFrame(np.round(transition, 6),
                                                  index=[f"状态{s}" for s in states],
                                                  columns=[f"状态{s}" for s in states]).reset_index())
    rows = []
    for step, dist in enumerate(distributions):
        for state, value in zip(states, dist):
            rows.append({"期数": step, "状态": state, "概率": round(float(value), 6)})
    save_table(__file__, "状态分布", rows)
