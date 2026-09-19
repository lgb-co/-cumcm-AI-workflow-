"""动态规划 · 0-1 背包（Python 最小可运行模板）

模型：max Σ v_i z_i，s.t. Σ w_i z_i <= W，z_i ∈ {0,1}
状态：dp[j] = 容量 j 时的最大价值；用一维滚动数组，容量倒序保证每件物品只取一次。
接口：solve(weights, values, capacity) -> (最大价值, 选中下标)；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_table  # noqa: E402


def build_demo() -> dict:
    return {
        "weights": [2, 3, 4, 5, 9],
        "values": [3, 4, 5, 8, 10],
        "capacity": 20,
    }


def solve(weights, values, capacity: int) -> tuple[float, list[int]]:
    weights = [int(w) for w in weights]
    values = [int(v) for v in values]
    dp = [0] * (capacity + 1)
    choice = [[False] * (capacity + 1) for _ in range(len(weights))]
    for i, (w, v) in enumerate(zip(weights, values)):
        for j in range(capacity, w - 1, -1):
            if dp[j - w] + v > dp[j]:
                dp[j] = dp[j - w] + v
                choice[i][j] = True
    picked, j = [], capacity
    for i in range(len(weights) - 1, -1, -1):
        if choice[i][j]:
            picked.append(i)
            j -= weights[i]
    return float(dp[capacity]), sorted(picked)


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    best, picked = solve(data["weights"], data["values"], int(data["capacity"]))
    total_w = sum(np.asarray(data["weights"])[picked])
    report("0-1 背包", 最大价值=best, 选中物品=picked, 总重量=int(total_w),
           容量=int(data["capacity"]))
    save_table(__file__, "背包方案",
               {"物品": np.arange(1, len(data["weights"]) + 1),
                "重量": data["weights"], "价值": data["values"],
                "是否选中": [1 if i in picked else 0 for i in range(len(data["weights"]))]})
