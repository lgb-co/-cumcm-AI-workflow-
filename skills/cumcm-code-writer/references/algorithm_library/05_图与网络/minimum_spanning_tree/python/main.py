"""最小生成树 Kruskal（Python 最小可运行模板）

步骤：边按权升序 → 并查集判断是否成环 → 依次选边直到 n-1 条。
接口：solve(edges, n) -> (选中边, 总权重)；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_table  # noqa: E402


def build_demo() -> dict:
    edges = [(0, 1, 4), (0, 2, 3), (1, 2, 1), (1, 3, 2), (2, 3, 4), (2, 4, 6), (3, 4, 5), (3, 5, 7), (4, 5, 2)]
    return {"edges": edges, "n": 6}


def solve(edges, n: int):
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    chosen, total = [], 0.0
    for u, v, w in sorted(edges, key=lambda e: e[2]):
        ru, rv = find(u), find(v)
        if ru != rv:
            parent[ru] = rv
            chosen.append((u, v, w))
            total += w
    return chosen, total


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    chosen, total = solve(data["edges"], int(data["n"]))
    report("最小生成树", 边数=len(chosen), 总权重=round(total, 3))
    save_table(__file__, "生成树", {"起点": [e[0] for e in chosen], "终点": [e[1] for e in chosen],
                                    "权重": [e[2] for e in chosen]})
