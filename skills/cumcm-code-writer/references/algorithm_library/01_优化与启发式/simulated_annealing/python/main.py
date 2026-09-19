"""模拟退火 SA · 十城市 TSP（Python 最小可运行模板）

模型：min 巡回路径总长度；邻域用 2-opt 逆序交换；Metropolis 准则接受劣解。
参数：初温 100，降温系数 0.99，每温度迭代 200 次，终温 0.5。
接口：solve(coords, seed) -> (最优路径, 路径长度, 收敛序列)；运行：python main.py
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


def tour_length(tour, dist):
    return float(dist[tour, np.roll(tour, -1)].sum())


def solve(coords, t0: float = 100.0, alpha: float = 0.99, inner: int = 200,
          t_min: float = 0.5, seed: int = 42):
    diff = coords[:, None, :] - coords[None, :, :]
    dist = np.sqrt((diff ** 2).sum(-1))
    rng = np.random.default_rng(seed)
    n = len(coords)
    tour = np.arange(n)
    current = tour_length(tour, dist)
    best_tour, best = tour.copy(), current
    history = []
    temperature = t0
    iterations = 0
    while temperature > t_min and iterations < 20000:
        for _ in range(inner):
            i, j = sorted(rng.integers(0, n, 2))
            if i == j:
                continue
            candidate = tour.copy()
            candidate[i:j + 1] = candidate[i:j + 1][::-1]
            length = tour_length(candidate, dist)
            delta = length - current
            if delta < 0 or rng.random() < np.exp(-delta / temperature):
                tour, current = candidate, length
                if current < best:
                    best_tour, best = tour.copy(), current
            iterations += 1
        temperature *= alpha
        history.append(best)
    return best_tour, best, history, dist


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    tour, best, history, dist = solve(np.asarray(data["coords"], float))
    report("模拟退火", 最优路径长度=round(best, 3), 巡回顺序=tour.tolist(), 温度步数=len(history))
    save_table(__file__, "最优路径", {"顺序": np.arange(1, len(tour) + 1), "城市": tour})
    save_table(__file__, "收敛过程", {"温度步": np.arange(1, len(history) + 1), "当前最优": np.round(history, 4)})
    plt = set_style()
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.2))
    path = np.append(tour, tour[0])
    axes[0].plot(np.asarray(data["coords"])[path, 0], np.asarray(data["coords"])[path, 1],
                 "-o", color="#0072B2", markersize=4)
    axes[0].set_title(f"最优路径（长度 {best:.2f}）")
    axes[0].set_xlabel("x 坐标")
    axes[0].set_ylabel("y 坐标")
    axes[1].plot(history, color="#D55E00")
    axes[1].set_title("退火收敛过程")
    axes[1].set_xlabel("温度步")
    axes[1].set_ylabel("当前最优长度")
    save_fig(__file__, fig, "simulated_annealing")
