"""Dijkstra 最短路（Python 最小可运行模板）

模型：非负权网络单源最短路；用优先队列实现，复杂度 O(E log V)。
接口：solve(edges, n, source) -> (最短距离数组, 前驱数组)；运行：python main.py
"""
from __future__ import annotations

import heapq
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_table  # noqa: E402


def build_demo() -> dict:
    edges = [(0, 1, 4), (0, 2, 2), (1, 2, 1), (1, 3, 5), (2, 3, 8), (2, 4, 10), (3, 4, 2), (3, 5, 6), (4, 5, 3)]
    return {"edges": edges, "n": 6, "source": 0}


def solve(edges, n: int, source: int):
    graph = [[] for _ in range(n)]
    for u, v, w in edges:
        graph[u].append((v, w))
        graph[v].append((u, w))
    dist = [np.inf] * n
    prev = [-1] * n
    dist[source] = 0.0
    queue = [(0.0, source)]
    while queue:
        d, u = heapq.heappop(queue)
        if d > dist[u]:
            continue
        for v, w in graph[u]:
            if d + w < dist[v]:
                dist[v] = d + w
                prev[v] = u
                heapq.heappush(queue, (dist[v], v))
    return np.array(dist), prev


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    dist, prev = solve(data["edges"], int(data["n"]), int(data["source"]))
    report("Dijkstra", 源点=data["source"], 最短路=np.round(dist, 3).tolist())
    save_table(__file__, "最短距离", {"节点": np.arange(int(data["n"])), "距离": np.round(dist, 6), "前驱": prev})
