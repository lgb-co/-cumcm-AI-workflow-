"""一维热传导方程 · 显式有限差分（Python 最小可运行模板）

模型：∂u/∂t = a ∂²u/∂x²，两端固定温度；显式格式要求 r = aΔt/Δx² ≤ 1/2，否则数值不稳定。
接口：solve(length, nx, a, t_end, u_left, u_right) -> (温度场, r, 稳定性)；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_fig, save_table, set_style  # noqa: E402


def build_demo() -> dict:
    return {"length": 1.0, "nx": 51, "a": 0.01, "t_end": 5.0, "u_left": 100.0, "u_right": 0.0}


def solve(length, nx, a, t_end, u_left, u_right):
    dx = length / (nx - 1)
    r_target = 0.4
    dt = r_target * dx ** 2 / a
    steps = int(np.ceil(t_end / dt))
    dt = t_end / steps
    r = a * dt / dx ** 2
    if r > 0.5:
        raise ValueError(f"显式格式不稳定：r={r:.3f} > 0.5，需减小时间步长")
    u = np.zeros(nx)
    u[0], u[-1] = u_left, u_right
    history = [u.copy()]
    for _ in range(steps):
        u_next = u.copy()
        u_next[1:-1] = u[1:-1] + r * (u[2:] - 2 * u[1:-1] + u[:-2])
        u_next[0], u_next[-1] = u_left, u_right
        u = u_next
        history.append(u.copy())
    x = np.linspace(0, length, nx)
    return x, np.array(history), r, steps


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    x, history, r, steps = solve(**data)
    report("热传导方程", 网格数=data["nx"], r=round(r, 4), 时间步数=steps,
           稳定性="满足 r<=0.5" if r <= 0.5 else "不满足")
    save_table(__file__, "温度分布", {"x": np.round(x, 5),
                                      "初始": np.round(history[0], 4),
                                      "中期": np.round(history[len(history) // 4], 4),
                                      "终态": np.round(history[-1], 4)})
    plt = set_style()
    fig, ax = plt.subplots()
    for index, color, label in [(0, "#999999", "初始"), (len(history) // 10, "#56B4E9", "t=10%"),
                                (len(history) // 4, "#0072B2", "t=25%"), (-1, "#D55E00", "稳态")]:
        ax.plot(x, history[index], color=color, label=label)
    ax.set_xlabel("位置 x")
    ax.set_ylabel("温度 u")
    ax.legend()
    save_fig(__file__, fig, "heat_equation_1d")
