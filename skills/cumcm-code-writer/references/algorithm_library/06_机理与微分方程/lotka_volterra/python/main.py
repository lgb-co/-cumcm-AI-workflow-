"""Lotka-Volterra 捕食者-被捕食者模型（Python 最小可运行模板）

模型：dx/dt = αx - βxy，dy/dt = δxy - γy；输出周期、极值与相图。
接口：solve(params, t_end) -> (轨迹, 周期估计)；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from scipy.integrate import solve_ivp

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_fig, save_table, set_style  # noqa: E402


def build_demo() -> dict:
    return {"alpha": 1.1, "beta": 0.4, "delta": 0.1, "gamma": 0.4, "x0": 10.0, "y0": 5.0, "t_end": 60.0}


def solve(alpha, beta, delta, gamma, x0, y0, t_end):
    def rhs(t, y):
        x, yy = y
        return [alpha * x - beta * x * yy, delta * x * yy - gamma * yy]

    t_eval = np.linspace(0, t_end, int(t_end * 20) + 1)
    result = solve_ivp(rhs, [0, t_end], [x0, y0], t_eval=t_eval, rtol=1e-9, atol=1e-9)
    x, y = result.y
    # 用被捕食者序列的峰值间隔估计周期
    peaks = [i for i in range(1, len(x) - 1) if x[i] > x[i - 1] and x[i] > x[i + 1]]
    period = float(np.mean(np.diff(t_eval[peaks]))) if len(peaks) >= 2 else float("nan")
    return result.t, np.vstack([x, y]), period, (float(x.max()), float(y.max()))


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    t, y, period, extremes = solve(**data)
    report("Lotka-Volterra", 周期=round(period, 3), 被捕食者峰值=round(extremes[0], 2),
           捕食者峰值=round(extremes[1], 2))
    save_table(__file__, "种群轨迹", {"时间": np.round(t, 3), "被捕食者x": np.round(y[0], 4),
                                      "捕食者y": np.round(y[1], 4)})
    plt = set_style()
    fig, axes = plt.subplots(1, 2, figsize=(7.6, 3.2))
    axes[0].plot(t, y[0], color="#0072B2", label="被捕食者 x")
    axes[0].plot(t, y[1], color="#D55E00", label="捕食者 y")
    axes[0].set_xlabel("时间")
    axes[0].set_ylabel("种群数量")
    axes[0].legend()
    axes[1].plot(y[0], y[1], color="#009E73")
    axes[1].set_xlabel("被捕食者 x")
    axes[1].set_ylabel("捕食者 y")
    axes[1].set_title("相平面轨迹")
    save_fig(__file__, fig, "lotka_volterra")
