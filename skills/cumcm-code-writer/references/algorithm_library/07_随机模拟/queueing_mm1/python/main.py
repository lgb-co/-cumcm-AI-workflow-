"""M/M/1 排队论解析公式（Python 最小可运行模板）

模型：到达率 λ、服务率 μ、ρ=λ/μ<1 时稳态指标：L、Lq、W、Wq、P0。
接口：solve(lam, mu) -> 指标字典；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_fig, save_table, set_style  # noqa: E402


def build_demo() -> dict:
    return {"lam": 2.4, "mu": 3.0}


def solve(lam: float, mu: float) -> dict:
    rho = lam / mu
    if rho >= 1:
        raise ValueError(f"系统不稳定：ρ={rho:.3f} ≥ 1，需提高服务率或降低到达率")
    metrics = {
        "ρ": rho,
        "平均队长L": rho / (1 - rho),
        "平均等待队长Lq": rho ** 2 / (1 - rho),
        "平均逗留W": 1 / (mu - lam),
        "平均等待Wq": rho / (mu - lam),
        "空闲概率P0": 1 - rho,
    }
    return metrics


if __name__ == "__main__":
    import numpy as np

    data = demo(__file__, build_demo)
    metrics = solve(data["lam"], data["mu"])
    report("M/M/1", 利用率=round(metrics["ρ"], 4), 平均队长=round(metrics["平均队长L"], 4),
           平均等待=round(metrics["平均等待Wq"], 4), 空闲概率=round(metrics["空闲概率P0"], 4))
    save_table(__file__, "稳态指标", {"指标": list(metrics), "数值": [round(v, 6) for v in metrics.values()]})
    lam_grid = np.linspace(0.1, data["mu"] * 0.98, 50)
    wait = [1 / (data["mu"] - l) for l in lam_grid]
    plt = set_style()
    fig, ax = plt.subplots()
    ax.plot(lam_grid, wait, color="#0072B2")
    ax.axvline(data["lam"], color="#D55E00", ls="--", lw=0.9)
    ax.annotate(f"当前 λ={data['lam']}", xy=(data["lam"], 1 / (data["mu"] - data["lam"])),
                xytext=(data["lam"] - 1.6, 4), fontsize=8,
                arrowprops=dict(arrowstyle="->", color="#444444"))
    ax.set_xlabel("到达率 λ")
    ax.set_ylabel("平均逗留时间 W")
    ax.set_yscale("log")
    save_fig(__file__, fig, "queueing_mm1")
