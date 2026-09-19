"""遗传算法 · 连续函数寻优（Python 最小可运行模板）

模型：max f(x, y) = 21.5 + x sin(4πx) + y sin(20πy)，x ∈ [-3, 12.1]，y ∈ [4.1, 5.8]
步骤：实数编码 → 锦标赛选择 → 算术交叉 → 高斯变异 → 精英保留。
接口：solve(generations, pop_size, seed) -> (最优个体, 最优值, 收敛序列)；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_fig, save_table, set_style  # noqa: E402

BOUNDS = np.array([[-3.0, 12.1], [4.1, 5.8]])


def build_demo() -> dict:
    return {"bounds": BOUNDS}


def fitness(pop):
    x, y = pop[:, 0], pop[:, 1]
    return 21.5 + x * np.sin(4 * np.pi * x) + y * np.sin(20 * np.pi * y)


def solve(generations: int = 100, pop_size: int = 60, seed: int = 42):
    rng = np.random.default_rng(seed)
    low, high = BOUNDS[:, 0], BOUNDS[:, 1]
    pop = rng.uniform(low, high, size=(pop_size, 2))
    values = fitness(pop)
    history = []
    for _ in range(generations):
        best = np.argmax(values)
        elite, elite_value = pop[best].copy(), values[best]
        children = [elite]
        while len(children) < pop_size - 1:
            i, j = rng.integers(0, pop_size, 2)
            p1, p2 = pop[i], pop[j]
            alpha = rng.random()
            child = alpha * p1 + (1 - alpha) * p2
            if rng.random() < 0.3:
                child = child + rng.normal(0, 0.1 * (high - low), size=2)
            children.append(np.clip(child, low, high))
        pop = np.array([elite] + children)
        values = fitness(pop)
        history.append(float(values.max()))
    best = np.argmax(values)
    return pop[best], float(values[best]), history, pop, values


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    x, best, history, pop, values = solve()
    report("遗传算法", 迭代=len(history), 最优x=round(x[0], 4), 最优y=round(x[1], 4), 最优值=round(best, 4))
    save_table(__file__, "收敛过程", {"代数": np.arange(1, len(history) + 1), "最优值": np.round(history, 6)})
    plt = set_style()
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.0))
    axes[0].plot(history, color="#0072B2")
    axes[0].set_xlabel("代数")
    axes[0].set_ylabel("种群最优值")
    axes[0].set_title("收敛过程")
    axes[1].scatter(pop[:, 0], pop[:, 1], c=values, cmap="viridis", s=18)
    axes[1].scatter(*x, marker="*", s=140, color="#D55E00", label="最优个体")
    axes[1].set_xlabel("x")
    axes[1].set_ylabel("y")
    axes[1].set_title("末代种群分布")
    axes[1].legend()
    save_fig(__file__, fig, "genetic_algorithm")
