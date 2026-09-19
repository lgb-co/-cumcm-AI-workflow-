"""演化博弈 · 复制动态（Python 最小可运行模板）

模型：dx_i/dt = x_i [(Ax)_i - x' A x]，x 为策略占比；求解并画单纯形轨迹，判断演化稳定策略（ESS）。
适用：策略扩散、群体行为演化、监管博弈等。
接口：solve(A, x0_list, t_end) -> (轨迹, 末态占比)；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from scipy.integrate import solve_ivp

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_fig, save_table, set_style  # noqa: E402


def build_demo() -> dict:
    # 三策略收益矩阵：合作 / 搭便车 / 惩罚
    A = np.array([[3.0, 1.0, 2.5],
                  [4.0, 2.0, 1.0],
                  [3.2, 1.5, 2.2]])
    starts = [[0.8, 0.1, 0.1], [0.1, 0.8, 0.1], [0.1, 0.1, 0.8], [0.34, 0.33, 0.33]]
    return {"A": A, "starts": starts, "t_end": 60.0, "names": ["合作", "搭便车", "惩罚"]}


def replicator(A, t_end: float, x0):
    def rhs(t, x):
        x = np.clip(x, 0, None)
        fitness = A @ x
        return x * (fitness - float(x @ fitness))

    return solve_ivp(rhs, [0, t_end], np.asarray(x0, float) / np.sum(x0),
                     t_eval=np.linspace(0, t_end, 301), rtol=1e-8, atol=1e-10)


def solve(A, starts, t_end: float):
    trajectories = []
    for x0 in starts:
        result = replicator(A, t_end, x0)
        trajectories.append((np.asarray(x0), result.t, result.y))
    return trajectories


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    A = np.asarray(data["A"], float)
    trajectories = solve(A, data["starts"], float(data["t_end"]))
    finals = [traj[2][:, -1] for traj in trajectories]
    dominant = data["names"][int(np.argmax(np.mean(finals, axis=0)))]
    report("演化博弈", 轨迹数=len(trajectories), 平均末态占比=np.round(np.mean(finals, axis=0), 4).tolist(),
           占优策略=dominant)
    save_table(__file__, "末态占比", {"初始状态": [str(np.round(t[0], 3)) for t in trajectories],
                                      **{f"{name}占比": [round(float(t[2][i, -1]), 6) for t in trajectories]
                                         for i, name in enumerate(data["names"])}})
    plt = set_style()
    fig, axes = plt.subplots(1, 2, figsize=(7.6, 3.4))
    colors = ["#0072B2", "#D55E00", "#009E73"]
    for index, (x0, t, y) in enumerate(trajectories):
        for strategy in range(len(data["names"])):
            axes[0].plot(t, y[strategy], color=colors[strategy], alpha=0.35 + 0.15 * index,
                         label=data["names"][strategy] if index == 0 else None)
    axes[0].set_xlabel("时间")
    axes[0].set_ylabel("策略占比")
    axes[0].legend()
    axes[0].set_title("复制动态轨迹")
    for x0, t, y in trajectories:
        axes[1].plot(y[0], y[1], color="#666666", alpha=0.6, lw=1.0)
        axes[1].scatter(y[0, 0], y[1, 0], s=18, color="#0072B2")
        axes[1].scatter(y[0, -1], y[1, -1], s=26, marker="*", color="#D55E00")
    axes[1].set_xlabel(f"{data['names'][0]} 占比")
    axes[1].set_ylabel(f"{data['names'][1]} 占比")
    axes[1].set_title("相平面（○ 起点，★ 终点）")
    save_fig(__file__, fig, "evolutionary_game")
