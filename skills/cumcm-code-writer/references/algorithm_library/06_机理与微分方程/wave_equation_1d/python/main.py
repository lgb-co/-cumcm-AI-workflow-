"""一维波动方程 · 显式有限差分（Python 最小可运行模板）

模型：∂²u/∂t² = c² ∂²u/∂x²，两端固定；显式格式要求 CFL 条件 c·Δt/Δx ≤ 1。
初值取高斯调制的正弦波包，输出各时刻波形快照与离散能量（检验守恒性）。
接口：solve(length, nx, c, t_end) -> (坐标, 波形快照, CFL 平方, 能量序列, 快照时刻)；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_fig, save_table, set_style  # noqa: E402


def build_demo() -> dict:
    return {"length": 1.0, "nx": 101, "c": 1.0, "t_end": 1.0}


def solve(length, nx, c, t_end, n_snapshots: int = 5):
    dx = length / (nx - 1)
    dt = 0.8 * dx / c                      # 取 CFL = 0.8，留出安全余量
    steps = int(np.ceil(t_end / dt))
    dt = t_end / steps
    r2 = (c * dt / dx) ** 2
    if r2 > 1:
        raise ValueError(f"CFL 条件不满足：r²={r2:.3f} > 1，需减小时间步长")

    x = np.linspace(0, length, nx)
    u = np.sin(3 * np.pi * x) * np.exp(-40 * (x - 0.5) ** 2)
    u[0] = u[-1] = 0.0
    u_prev = u.copy()

    snapshots = [u.copy()]
    marks = [0.0]
    energy = [float(np.sum(u[1:-1] ** 2) * dx)]
    interval = max(1, steps // (n_snapshots - 1))
    for step in range(1, steps + 1):
        u_next = np.zeros_like(u)
        u_next[1:-1] = 2 * u[1:-1] - u_prev[1:-1] + r2 * (u[2:] - 2 * u[1:-1] + u[:-2])
        u_prev, u = u, u_next
        energy.append(float(np.sum(u[1:-1] ** 2) * dx))
        if step % interval == 0 and len(snapshots) < n_snapshots:
            snapshots.append(u.copy())
            marks.append(step * dt)
    return x, snapshots, float(r2), energy, marks


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    x, snapshots, r2, energy, marks = solve(**data)
    report("波动方程", 网格数=data["nx"], CFL平方=round(r2, 4),
           能量漂移=round(abs(energy[-1] - energy[0]) / energy[0], 6),
           快照数=len(snapshots))
    save_table(__file__, "能量守恒", {"时间步": np.arange(len(energy)), "离散能量": np.round(energy, 8)})
    table = {"x": np.round(x, 4)}
    for index, snap in enumerate(snapshots):
        table[f"t={marks[index]:.3f}"] = np.round(snap, 6)
    save_table(__file__, "波形快照", table)
    plt = set_style()
    fig, axes = plt.subplots(1, 2, figsize=(7.6, 3.2))
    for index, snap in enumerate(snapshots):
        axes[0].plot(x, snap, label=f"t={marks[index]:.2f}")
    axes[0].set_xlabel("位置 x")
    axes[0].set_ylabel("位移 u")
    axes[0].legend(fontsize=7)
    axes[1].plot(energy, color="#D55E00")
    axes[1].set_xlabel("时间步")
    axes[1].set_ylabel("离散能量")
    axes[1].set_title("能量守恒检验")
    save_fig(__file__, fig, "wave_equation_1d")
