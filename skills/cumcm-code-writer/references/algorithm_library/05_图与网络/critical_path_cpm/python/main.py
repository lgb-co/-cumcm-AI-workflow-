"""关键路径 CPM（Python 最小可运行模板）

步骤：拓扑排序 → 正推最早开始/最早完成 → 逆推最迟完成 → 总时差为 0 的节点构成关键路径。
接口：solve(activities, n) -> (总工期, 关键节点, 时间参数)；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_table  # noqa: E402


def build_demo() -> dict:
    activities = [(0, 1, 3), (0, 2, 4), (1, 3, 5), (2, 3, 2), (1, 4, 6),
                  (3, 5, 4), (4, 5, 3), (4, 6, 5), (5, 6, 2)]
    return {"activities": activities, "n": 7}


def solve(activities, n: int):
    adj = [[] for _ in range(n)]
    indeg = [0] * n
    for u, v, d in activities:
        adj[u].append((v, d))
        indeg[v] += 1
    order, queue = [], [i for i in range(n) if indeg[i] == 0]
    while queue:
        u = queue.pop(0)
        order.append(u)
        for v, _ in adj[u]:
            indeg[v] -= 1
            if indeg[v] == 0:
                queue.append(v)
    if len(order) != n:
        raise ValueError("活动网络存在环，无法计算关键路径")

    ES = [0.0] * n
    for u in order:
        for v, d in adj[u]:
            ES[v] = max(ES[v], ES[u] + d)
    project_time = max(ES)
    LF = [project_time] * n
    for u in reversed(order):
        for v, d in adj[u]:
            LF[u] = min(LF[u], LF[v] - d)
    slack = [LF[i] - ES[i] for i in range(n)]
    critical = [i for i in range(n) if abs(slack[i]) < 1e-9]
    return project_time, critical, ES, LF, slack


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    n = int(data["n"])
    project_time, critical, ES, LF, slack = solve(data["activities"], n)
    report("关键路径", 总工期=round(project_time, 3), 关键节点=critical, 节点数=n)
    save_table(__file__, "节点时间参数", {"节点": list(range(n)), "最早开始": ES, "最迟完成": LF, "总时差": slack})
