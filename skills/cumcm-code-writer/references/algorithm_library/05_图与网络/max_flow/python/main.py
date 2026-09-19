"""最大流 · Edmonds-Karp（Python 最小可运行模板）

模型：网络最大流，反复 BFS 寻找增广路直到不存在，复杂度 O(V E²)。
接口：solve(capacity, source, sink) -> (最大流值, 各边流量)；运行：python main.py
"""
from __future__ import annotations

import sys
from collections import deque
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_table  # noqa: E402


def build_demo() -> dict:
    capacity = np.array([
        [0, 16, 13, 0, 0, 0],
        [0, 0, 10, 12, 0, 0],
        [0, 4, 0, 0, 14, 0],
        [0, 0, 9, 0, 0, 20],
        [0, 0, 0, 7, 0, 4],
        [0, 0, 0, 0, 0, 0]], dtype=float)
    return {"capacity": capacity, "source": 0, "sink": 5}


def solve(capacity, source: int, sink: int):
    capacity = np.asarray(capacity, float)
    n = capacity.shape[0]
    flow = np.zeros_like(capacity)
    residual = capacity.copy()
    total = 0.0
    while True:
        parent = [-1] * n
        parent[source] = source
        queue = deque([source])
        while queue and parent[sink] == -1:
            u = queue.popleft()
            for v in range(n):
                if parent[v] == -1 and residual[u, v] > 1e-12:
                    parent[v] = u
                    queue.append(v)
        if parent[sink] == -1:
            break
        path_flow, v = np.inf, sink
        while v != source:
            u = parent[v]
            path_flow = min(path_flow, residual[u, v])
            v = u
        v = sink
        while v != source:
            u = parent[v]
            flow[u, v] += path_flow
            flow[v, u] -= path_flow
            residual[u, v] -= path_flow
            residual[v, u] += path_flow
            v = u
        total += path_flow
    return total, flow


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    total, flow = solve(data["capacity"], int(data["source"]), int(data["sink"]))
    report("最大流", 源点=data["source"], 汇点=data["sink"], 最大流=round(float(total), 3))
    capacity = np.asarray(data["capacity"])
    idx = np.argwhere(capacity > 0)
    save_table(__file__, "边流量", {"起点": idx[:, 0], "终点": idx[:, 1],
                                    "容量": capacity[idx[:, 0], idx[:, 1]],
                                    "流量": flow[idx[:, 0], idx[:, 1]]})
