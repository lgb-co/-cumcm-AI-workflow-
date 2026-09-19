"""二阶微分方程 · 阻尼振动（Python 最小可运行模板）

模型：x'' + 2ζω x' + ω² x = 0；降阶为一阶方程组后用 RK45 求解，输出峰值衰减与周期。
接口：solve(zeta, omega, x0, v0, t_end) -> (轨迹, 周期)；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from scipy.integrate import solve_ivp

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_fig, save_table, set_style  # noqa: E402


def build_demo() -> dict:
    return {"zeta": 0.08, "omega": 2.0, "x0": 1.0, "v0": 0.0, "t_end": 20.0}


def solve(zeta, omega, x0, v0, t_end):
    def rhs(t, y):
        x, v = y
        return [v, -2 * zeta * omega * v - omega ** 2 * x]

    t_eval = np.linspace(0, t_end, 2001)
    result = solve_ivp(rhs, [0, t_end], [x0, v0], t_eval=t_eval, rtol=1e-9, atol=1e-12)
    x = result.y[0]
    peaks = [i for i in range(1, len(x) - 1) if x[i] > x[i - 1] and x[i] > x[i + 1]]
    period = float(np.mean(np.diff(t_eval[peaks]))) if len(peaks) >= 2 else float("nan")
    return result.t, result.y, period, peaks


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    t, y, period, peaks = solve(**data)
    report("阻尼振动", 阻尼比=data["zeta"], 固有频率=data["omega"], 周期=round(period, 4),
           末态位移=round(float(y[0][-1]), 5))
    save_table(__file__, "振动轨迹", {"时间": np.round(t, 4), "位移x": np.round(y[0], 6),
                                      "速度v": np.round(y[1], 6)})
    plt = set_style()
    fig, axes = plt.subplots(1, 2, figsize=(7.6, 3.0))
    axes[0].plot(t, y[0], color="#0072B2")
    axes[0].set_xlabel("时间")
    axes[0].set_ylabel("位移 x")
    axes[0].set_title("阻尼振动时程")
    axes[1].plot(y[0], y[1], color="#D55E00")
    axes[1].set_xlabel("位移 x")
    axes[1].set_ylabel("速度 v")
    axes[1].set_title("相轨迹")
    save_fig(__file__, fig, "second_order_ode")
