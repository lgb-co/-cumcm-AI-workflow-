"""SEIR 传染病模型（Python 最小可运行模板）

模型：dS/dt = -βSI/N，dE/dt = βSI/N - σE，dI/dt = σE - γI，dR/dt = γI
相比 SIR 多了潜伏期 E；输出峰值、达峰时间与基本再生数 R0 = β/γ。
接口：solve(N, E0, I0, beta, sigma, gamma, days) -> (轨迹, 峰值, 达峰时间)；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from scipy.integrate import solve_ivp

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_fig, save_table, set_style  # noqa: E402


def build_demo() -> dict:
    return {"N": 10000.0, "E0": 20.0, "I0": 5.0, "beta": 0.45, "sigma": 0.2, "gamma": 0.15, "days": 180.0}


def solve(N, E0, I0, beta, sigma, gamma, days):
    def rhs(t, y):
        S, E, I, R = y
        infection = beta * S * I / N
        return [-infection, infection - sigma * E, sigma * E - gamma * I, gamma * I]

    t_eval = np.linspace(0, days, int(days) + 1)
    result = solve_ivp(rhs, [0, days], [N - E0 - I0, E0, I0, 0.0], t_eval=t_eval, rtol=1e-9)
    peak_index = int(np.argmax(result.y[2]))
    return result.t, result.y, float(result.y[2][peak_index]), float(result.t[peak_index]), float(beta / gamma)


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    t, y, peak, peak_time, r0 = solve(**data)
    report("SEIR 模型", R0=round(r0, 3), 感染峰值=round(peak, 1), 达峰时间=round(peak_time, 1),
           最终累计感染=round(float(y[3][-1]), 1))
    save_table(__file__, "传播轨迹", {"天": np.round(t, 2), "S": np.round(y[0], 2), "E": np.round(y[1], 2),
                                      "I": np.round(y[2], 2), "R": np.round(y[3], 2)})
    plt = set_style()
    fig, ax = plt.subplots()
    for index, (label, color) in enumerate([("易感 S", "#0072B2"), ("潜伏 E", "#E69F00"),
                                            ("感染 I", "#D55E00"), ("移除 R", "#009E73")]):
        ax.plot(t, y[index], color=color, label=label)
    ax.axvline(peak_time, color="#666666", ls=":", lw=0.9)
    ax.annotate(f"峰值 {peak:.0f}（第 {peak_time:.0f} 天）", xy=(peak_time, peak),
                xytext=(peak_time + 10, peak), fontsize=8,
                arrowprops=dict(arrowstyle="->", color="#444444"))
    ax.set_xlabel("时间（天）")
    ax.set_ylabel("人数")
    ax.legend()
    save_fig(__file__, fig, "seir_model")
