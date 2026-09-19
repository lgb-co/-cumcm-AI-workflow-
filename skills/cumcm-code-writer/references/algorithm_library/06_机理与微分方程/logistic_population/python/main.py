"""Logistic 人口增长模型（Python 最小可运行模板）

模型：dN/dt = r N (1 - N/K)；参数用最小二乘在数据上标定，再做趋势预测。
接口：solve(t, N, t_pred) -> (参数 r/K, 拟合值, 预测值)；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import curve_fit

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_fig, save_table, set_style  # noqa: E402


def build_demo() -> dict:
    t = np.arange(0, 31, dtype=float)
    true_r, true_k = 0.45, 120.0
    N = true_k / (1 + (true_k / 8 - 1) * np.exp(-true_r * t))
    return {"t": t, "N": N, "t_pred": np.arange(31, 41, dtype=float)}


def logistic(t, r, K, N0):
    return K / (1 + (K / N0 - 1) * np.exp(-r * t))


def solve(t, N, t_pred):
    n0 = float(N[0])
    (r, K), _ = curve_fit(lambda tt, rr, KK: logistic(tt, rr, KK, n0), t, N,
                         p0=[0.3, float(N.max())], maxfev=20000)
    fitted = logistic(t, r, K, float(N[0]))
    forecast = logistic(t_pred, r, K, float(N[0]))
    residual = float(np.sqrt(np.mean((fitted - N) ** 2)))
    return float(r), float(K), fitted, forecast, residual


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    r, K, fitted, forecast, rmse = solve(data["t"], data["N"], data["t_pred"])
    report("Logistic 模型", 增长率r=round(r, 4), 环境容量K=round(K, 3), 拟合RMSE=round(rmse, 4),
           预测末期=round(float(forecast[-1]), 3))
    save_table(__file__, "拟合与预测", {"时间": np.concatenate([data["t"], data["t_pred"]]),
                                        "数值": np.round(np.concatenate([fitted, forecast]), 4),
                                        "类型": ["拟合"] * len(data["t"]) + ["预测"] * len(data["t_pred"])})
    plt = set_style()
    fig, ax = plt.subplots()
    ax.scatter(data["t"], data["N"], s=18, color="#0072B2", label="观测值")
    ax.plot(data["t"], fitted, color="#D55E00", label="Logistic 拟合")
    ax.plot(data["t_pred"], forecast, "--", color="#009E73", label="预测")
    ax.axhline(K, color="#666666", lw=0.8, ls=":")
    ax.set_xlabel("时间")
    ax.set_ylabel("人口/规模 N")
    ax.legend()
    save_fig(__file__, fig, "logistic_population")
