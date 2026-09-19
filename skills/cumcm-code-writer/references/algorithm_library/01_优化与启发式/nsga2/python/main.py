"""NSGA-II · 双目标优化（Python 最小可运行模板）

模型：min f1 = Σ x_i^2，min f2 = Σ (x_i - 2)^2，x_i ∈ [0, 2]，n = 10
步骤：快速非支配排序 → 拥挤度距离 → 锦标赛选择 → SBX 交叉 → 多项式变异。
接口：solve(pop_size, generations, seed) -> (Pareto 前沿, 目标值)；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_fig, save_table, set_style  # noqa: E402

DIMS, LOW, HIGH = 10, 0.0, 2.0


def build_demo() -> dict:
    return {"dims": DIMS, "low": LOW, "high": HIGH}


def objectives(pop):
    return np.column_stack([(pop ** 2).sum(1), ((pop - 2.0) ** 2).sum(1)])


def dominates(a, b) -> bool:
    return bool(np.all(a <= b) and np.any(a < b))


def fast_nondominated_sort(objs) -> list[list[int]]:
    n = len(objs)
    dominated_by = [[] for _ in range(n)]
    count = np.zeros(n, int)
    fronts = [[]]
    for p in range(n):
        for q in range(n):
            if p == q:
                continue
            if dominates(objs[p], objs[q]):
                dominated_by[p].append(q)
            elif dominates(objs[q], objs[p]):
                count[p] += 1
        if count[p] == 0:
            fronts[0].append(p)
    i = 0
    while fronts[i]:
        nxt: list[int] = []
        for p in fronts[i]:
            for q in dominated_by[p]:
                count[q] -= 1
                if count[q] == 0:
                    nxt.append(q)
        i += 1
        fronts.append(nxt)
    return [front for front in fronts if front]


def crowding_distance(objs, front: list[int]) -> np.ndarray:
    distance = np.zeros(len(front))
    if len(front) <= 2:
        return np.full(len(front), np.inf)
    values = objs[front]
    for k in range(values.shape[1]):
        order = np.argsort(values[:, k])
        distance[order[0]] = distance[order[-1]] = np.inf
        span = values[order[-1], k] - values[order[0], k]
        if span > 0:
            for i in range(1, len(front) - 1):
                distance[order[i]] += (values[order[i + 1], k] - values[order[i - 1], k]) / span
    return distance


def solve(pop_size: int = 40, generations: int = 30, seed: int = 42):
    rng = np.random.default_rng(seed)
    pop = rng.uniform(LOW, HIGH, size=(pop_size, DIMS))
    objs = objectives(pop)
    for _ in range(generations):
        fronts = fast_nondominated_sort(objs)
        rank = np.zeros(pop_size, int)
        crowd = np.zeros(pop_size)
        for level, front in enumerate(fronts):
            rank[front] = level
            crowd[front] = crowding_distance(objs, front)

        def tournament() -> int:
            i, j = rng.integers(0, pop_size, 2)
            if rank[i] != rank[j]:
                return int(i if rank[i] < rank[j] else j)
            return int(i if crowd[i] >= crowd[j] else j)

        children = np.empty_like(pop)
        for k in range(0, pop_size, 2):
            p1, p2 = pop[tournament()].copy(), pop[tournament()].copy()
            u = rng.random(DIMS)
            beta = np.where(u <= 0.5, (2 * u) ** (1 / 3), (1 / (2 * (1 - u))) ** (1 / 3))
            c1 = 0.5 * ((1 + beta) * p1 + (1 - beta) * p2)
            c2 = 0.5 * ((1 - beta) * p1 + (1 + beta) * p2)
            for child in (c1, c2):
                mask = rng.random(DIMS) < 0.1
                child[mask] += rng.normal(0, 0.1, mask.sum())
            children[k] = np.clip(c1, LOW, HIGH)
            if k + 1 < pop_size:
                children[k + 1] = np.clip(c2, LOW, HIGH)

        merged = np.vstack([pop, children])
        merged_objs = objectives(merged)
        new_pop, new_objs = [], []
        for front in fast_nondominated_sort(merged_objs):
            if len(new_pop) + len(front) <= pop_size:
                new_pop += [merged[i] for i in front]
                new_objs += [merged_objs[i] for i in front]
            else:
                distance = crowding_distance(merged_objs, front)
                order = np.argsort(-distance)
                for i in order[: pop_size - len(new_pop)]:
                    new_pop.append(merged[front[i]])
                    new_objs.append(merged_objs[front[i]])
                break
        pop, objs = np.array(new_pop), np.array(new_objs)

    front = fast_nondominated_sort(objs)[0]
    return pop[front], objs[front]


if __name__ == "__main__":
    demo(__file__, build_demo)
    pop, objs = solve()
    order = np.argsort(objs[:, 0])
    report("NSGA-II", Pareto解个数=len(pop), f1范围=f"{objs[:, 0].min():.3f}~{objs[:, 0].max():.3f}",
           f2范围=f"{objs[:, 1].min():.3f}~{objs[:, 1].max():.3f}")
    save_table(__file__, "pareto前沿", {"f1": np.round(objs[order, 0], 6), "f2": np.round(objs[order, 1], 6)})
    save_table(__file__, "pareto解", {f"x{i + 1}": np.round(pop[order, i], 6) for i in range(DIMS)})
    plt = set_style()
    fig, ax = plt.subplots()
    ax.scatter(objs[:, 0], objs[:, 1], color="#0072B2", s=22)
    ax.set_xlabel("$f_1$：Σ x²")
    ax.set_ylabel("$f_2$：Σ (x-2)²")
    ax.set_title("NSGA-II Pareto 前沿")
    save_fig(__file__, fig, "nsga2")
