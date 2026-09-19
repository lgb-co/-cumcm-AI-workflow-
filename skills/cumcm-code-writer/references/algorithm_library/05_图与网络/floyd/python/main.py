"""Floyd 全源最短路（Python 最小可运行模板）

模型：动态规划递推 D[i][j] = min(D[i][j], D[i][k] + D[k][j])，复杂度 O(V³)。
接口：solve(edges, n) -> 距离矩阵；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_table  # noqa: E402


def build_demo() -> dict:
    edges = [(0, 1, 4), (0, 2, 2), (1, 2, 1), (1, 3, 5), (2, 3, 8), (2, 4, 10), (3, 4, 2), (3, 5, 6), (4, 5, 3)]
    return {"edges": edges, "n": 6}


def solve(edges, n: int):
    D = np.full((n, n), np.inf)
    np.fill_diagonal(D, 0.0)
    for u, v, w in edges:
        D[u, v] = D[v, u] = min(D[u, v], w)
    for k in range(n):
        D = np.minimum(D, D[:, k, None] + D[None, k, :])
    return D


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    D = solve(data["edges"], int(data["n"]))
    report("Floyd", 节点数=int(data["n"]), 网络直径=round(float(np.nanmax(D[np.isfinite(D)])), 3))
    size = int(data["n"])
    save_table(__file__, "距离矩阵", {"起点": np.repeat(np.arange(size), size),
                                      "终点": np.tile(np.arange(size), size),
                                      "距离": np.round(D.ravel(), 6)})
