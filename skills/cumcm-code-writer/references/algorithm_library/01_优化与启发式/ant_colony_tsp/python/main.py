"""蚁群算法 ACO · 十城市 TSP（Python 最小可运行模板）

模型：min 巡回路径总长度；转移概率由信息素 τ^α 与启发式 1/d^β 决定；轮盘赌选择下一城市。
参数：蚂蚁 10 只，迭代 120 次，α=1，β=2，挥发率 0.5，信息素增量 Q/L。
接口：solve(coords, iterations, seed) -> (最优路径, 长度, 收敛序列)；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_fig, save_table, set_style  # noqa: E402

COORDS = np.array([[0, 0], [10, 0], [20, 5], [22, 18], [12, 26],
                   [0, 22], [-8, 14], [-6, 4], [8, 12], [16, 10]], dtype=float)


def build_demo() -> dict:
    return {"coords": COORDS}


def solve(coords, ants: int = 10, iterations: int = 120, alpha: float = 1.0,
          beta: float = 2.0, rho: float = 0.5, q: float = 1.0, seed: int = 42):
    rng = np.random.default_rng(seed)
    diff = coords[:, None, :] - coords[None, :, :]
    dist = np.sqrt((diff ** 2).sum(-1))
    n = len(coords)
    tau = np.ones((n, n))
    eta = 1.0 / np.where(dist == 0, np.inf, dist)
    best_tour, best_length = None, np.inf
    history = []
    for _ in range(iterations):
        tours, lengths = [], []
        for _ in range(ants):
            start = int(rng.integers(0, n))
            tour = [start]
            visited = {start}
            while len(tour) < n:
                current = tour[-1]
                prob = np.zeros(n)
                for city in range(n):
                    if city not in visited:
                        prob[city] = tau[current, city] ** alpha * eta[current, city] ** beta
                prob = prob / prob.sum()
                nxt = int(rng.choice(n, p=prob))
                tour.append(nxt)
                visited.add(nxt)
            tour = np.array(tour)
            length = float(dist[tour, np.roll(tour, -1)].sum())
            tours.append(tour)
            lengths.append(length)
        tau *= (1 - rho)
        for tour, length in zip(tours, lengths):
            for a, b in zip(tour, np.roll(tour, -1)):
                tau[a, b] += q / length
        index = int(np.argmin(lengths))
        if lengths[index] < best_length:
            best_length, best_tour = lengths[index], tours[index].copy()
        history.append(best_length)
    return best_tour, best_length, history, dist


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    tour, best, history, dist = solve(np.asarray(data["coords"], float))
    tour = np.roll(tour, -int(np.argmin(tour)))
    report("蚁群算法", 最优路径长度=round(best, 3), 巡回顺序=tour.tolist(), 迭代=len(history))
    save_table(__file__, "最优路径", {"顺序": np.arange(1, len(tour) + 1), "城市": tour})
    save_table(__file__, "收敛过程", {"迭代": np.arange(1, len(history) + 1), "当前最优": np.round(history, 4)})
    plt = set_style()
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.2))
    path = np.append(tour, tour[0])
    axes[0].plot(np.asarray(data["coords"])[path, 0], np.asarray(data["coords"])[path, 1],
                 "-o", color="#009E73", markersize=4)
    axes[0].set_title(f"最优路径（长度 {best:.2f}）")
    axes[0].set_xlabel("x 坐标")
    axes[0].set_ylabel("y 坐标")
    axes[1].plot(history, color="#D55E00")
    axes[1].set_title("蚁群收敛过程")
    axes[1].set_xlabel("迭代次数")
    axes[1].set_ylabel("当前最优长度")
    save_fig(__file__, fig, "ant_colony_tsp")
