"""粒子群优化 PSO · Rosenbrock 函数寻优（Python 最小可运行模板）

模型：min f(x, y) = 100 (y - x^2)^2 + (1 - x)^2，最优解 (1, 1)，最优值 0
步骤：初始化粒子与速度 → 更新个体/全局最优 → 惯性权重线性递减。
接口：solve(particles, iterations, seed) -> (最优位置, 最优值, 收敛序列)；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_fig, save_table, set_style  # noqa: E402

BOUND = 2.5


def build_demo() -> dict:
    return {"bound": BOUND}


def objective(x):
    x = np.atleast_2d(x)
    return 100 * (x[:, 1] - x[:, 0] ** 2) ** 2 + (1 - x[:, 0]) ** 2


def solve(particles: int = 30, iterations: int = 200, seed: int = 42):
    rng = np.random.default_rng(seed)
    position = rng.uniform(-BOUND, BOUND, size=(particles, 2))
    velocity = rng.uniform(-0.1, 0.1, size=(particles, 2))
    pbest = position.copy()
    pbest_value = objective(position)
    best_index = int(np.argmin(pbest_value))
    gbest, gbest_value = pbest[best_index].copy(), float(pbest_value[best_index])
    history = []
    for step in range(iterations):
        w = 0.9 - 0.5 * step / iterations
        r1, r2 = rng.random((particles, 2)), rng.random((particles, 2))
        velocity = (w * velocity + 1.5 * r1 * (pbest - position) + 1.5 * r2 * (gbest - position))
        position = np.clip(position + velocity, -BOUND, BOUND)
        value = objective(position)
        better = value < pbest_value
        pbest[better], pbest_value[better] = position[better], value[better]
        best_index = int(np.argmin(pbest_value))
        if pbest_value[best_index] < gbest_value:
            gbest, gbest_value = pbest[best_index].copy(), float(pbest_value[best_index])
        history.append(gbest_value)
    return gbest, gbest_value, history


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    gbest, value, history = solve()
    report("粒子群", 最优x=round(gbest[0], 4), 最优y=round(gbest[1], 4), 最优值=f"{value:.3e}")
    save_table(__file__, "收敛过程", {"迭代": np.arange(1, len(history) + 1), "全局最优": history})
    plt = set_style()
    fig, ax = plt.subplots()
    ax.semilogy(np.maximum(history, 1e-12), color="#0072B2")
    ax.set_xlabel("迭代次数")
    ax.set_ylabel("全局最优值（对数轴）")
    ax.set_title("PSO 收敛曲线")
    save_fig(__file__, fig, "particle_swarm")
