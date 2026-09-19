"""Lorenz 混沌系统（Python 最小可运行模板）

模型：dx/dt = σ(y-x)，dy/dt = x(ρ-z)-y，dz/dt = xy-βz；用两组初值展示初值敏感性。
接口：solve(params, t_end) -> (轨迹, 初值间距离)；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from scipy.integrate import solve_ivp

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_fig, save_table, set_style  # noqa: E402


def build_demo() -> dict:
    return {"sigma": 10.0, "rho": 28.0, "beta": 8 / 3, "t_end": 30.0, "perturb": 1e-8}


def solve(sigma, rho, beta, t_end, perturb):
    def rhs(t, y):
        x, yy, z = y
        return [sigma * (yy - x), x * (rho - z) - yy, x * yy - beta * z]

    t_eval = np.linspace(0, t_end, 6001)
    base = solve_ivp(rhs, [0, t_end], [1.0, 1.0, 1.0], t_eval=t_eval, rtol=1e-10, atol=1e-12).y
    shifted = solve_ivp(rhs, [0, t_end], [1.0 + perturb, 1.0, 1.0], t_eval=t_eval, rtol=1e-10, atol=1e-12).y
    distance = np.linalg.norm(base - shifted, axis=0)
    return t_eval, base, shifted, distance


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    t, base, shifted, distance = solve(**data)
    report("Lorenz 系统", 初值扰动=data["perturb"], 末态距离=f"{distance[-1]:.4g}",
           分离时刻=round(float(t[int(np.argmax(distance > 1.0))]) if (distance > 1.0).any() else float("nan"), 2))
    save_table(__file__, "轨迹", {"时间": np.round(t, 3), "x": np.round(base[0], 5),
                                  "y": np.round(base[1], 5), "z": np.round(base[2], 5),
                                  "初值间距离": np.round(distance, 8)})
    plt = set_style()
    fig = plt.figure(figsize=(7.6, 3.4))
    ax1 = fig.add_subplot(1, 2, 1, projection="3d")
    ax1.plot(base[0], base[1], base[2], lw=0.6, color="#0072B2")
    ax1.set_xlabel("x")
    ax1.set_ylabel("y")
    ax1.set_zlabel("z")
    ax1.set_title("Lorenz 吸引子")
    ax2 = fig.add_subplot(1, 2, 2)
    ax2.semilogy(t, np.maximum(distance, 1e-16), color="#D55E00")
    ax2.set_xlabel("时间")
    ax2.set_ylabel("两组初值的距离（对数轴）")
    ax2.set_title("初值敏感性")
    save_fig(__file__, fig, "lorenz_system")
