"""元胞自动机 · 森林火灾传播（Python 最小可运行模板）

规则：空地(0) 按 p_grow 长树(1)；树按邻域着火概率 p_fire 被引燃(2)；着火元胞下一轮变空地。
接口：solve(grid_size, steps, p_grow, p_fire, seed) -> (各期状态, 统计序列)；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_fig, save_table, set_style  # noqa: E402

EMPTY, TREE, FIRE = 0, 1, 2


def build_demo() -> dict:
    return {"grid_size": 60, "steps": 60, "p_grow": 0.05, "p_fire": 0.25}


def solve(grid_size: int, steps: int, p_grow: float, p_fire: float, seed: int = 42):
    rng = np.random.default_rng(seed)
    grid = (rng.random((grid_size, grid_size)) < 0.6).astype(int)
    grid[grid_size // 2, grid_size // 2] = FIRE
    frames = [grid.copy()]
    stats = []
    for _ in range(steps):
        new = grid.copy()
        burning = grid == FIRE
        for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            neighbour_fire = np.roll(np.roll(burning, di, axis=0), dj, axis=1)
            new[(grid == TREE) & neighbour_fire & (rng.random(grid.shape) < p_fire)] = FIRE
        new[burning] = EMPTY
        new[(grid == EMPTY) & (rng.random(grid.shape) < p_grow)] = TREE
        grid = new
        frames.append(grid.copy())
        stats.append({"步": len(stats) + 1, "树木比例": float((grid == TREE).mean()),
                      "着火比例": float((grid == FIRE).mean()), "空地比例": float((grid == EMPTY).mean())})
    return np.array(frames), stats


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    frames, stats = solve(int(data["grid_size"]), int(data["steps"]),
                          float(data["p_grow"]), float(data["p_fire"]))
    final = stats[-1]
    report("元胞自动机", 网格=len(frames[0]), 步数=len(stats), 末步树木比例=round(final["树木比例"], 4),
           末步着火比例=round(final["着火比例"], 4))
    save_table(__file__, "演化统计", stats)
    plt = set_style()
    fig, axes = plt.subplots(1, 3, figsize=(8.4, 3.0))
    for ax, index, title in zip(axes, [0, len(frames) // 2, -1], ["初始", "中期", "终态"]):
        ax.imshow(frames[index], cmap="YlGn_r", vmin=0, vmax=2)
        ax.set_title(title)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.grid(False)
    save_fig(__file__, fig, "cellular_automata")
