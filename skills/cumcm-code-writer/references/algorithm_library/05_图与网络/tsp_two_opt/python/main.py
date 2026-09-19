"""TSP 两阶段启发式 · 最近邻 + 2-opt（Python 最小可运行模板）

步骤：最近邻构造初始巡回 → 反复尝试 2-opt 逆序改进，直到无改进。
接口：solve(coords) -> (巡回, 优化后长度, 改进次数, 初始长度)；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_table  # noqa: E402

COORDS = np.array([[0, 0], [10, 0], [20, 5], [22, 18], [12, 26],
                   [0, 22], [-8, 14], [-6, 4], [8, 12], [16, 10]], dtype=float)


def build_demo() -> dict:
    return {"coords": COORDS}


def tour_length(tour, dist):
    return float(dist[tour, np.roll(tour, -1)].sum())


def nearest_neighbor(dist, start: int = 0):
    n = dist.shape[0]
    tour, visited = [start], {start}
    while len(tour) < n:
        last = tour[-1]
        nxt = min((j for j in range(n) if j not in visited), key=lambda j: dist[last, j])
        tour.append(nxt)
        visited.add(nxt)
    return np.array(tour)


def two_opt(tour, dist):
    best = tour.copy()
    best_length = tour_length(best, dist)
    improvements, improved = 0, True
    while improved:
        improved = False
        n = len(best)
        for i in range(1, n - 1):
            for j in range(i + 1, n):
                candidate = best.copy()
                candidate[i:j + 1] = candidate[i:j + 1][::-1]
                length = tour_length(candidate, dist)
                if length < best_length - 1e-9:
                    best, best_length = candidate, length
                    improvements += 1
                    improved = True
    return best, best_length, improvements


def solve(coords):
    coords = np.asarray(coords, float)
    diff = coords[:, None, :] - coords[None, :, :]
    dist = np.sqrt((diff ** 2).sum(-1))
    initial = nearest_neighbor(dist)
    tour, length, improvements = two_opt(initial, dist)
    return tour, length, improvements, tour_length(initial, dist)


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    tour, length, improvements, initial_length = solve(data["coords"])
    report("TSP 两阶段", 初始长度=round(initial_length, 3), 优化后长度=round(length, 3),
           改进次数=improvements, 巡回顺序=tour.tolist())
    save_table(__file__, "最优路径", {"顺序": np.arange(1, len(tour) + 1), "城市": tour})
