"""M/M/c 多服务台排队模型（Python 最小可运行模板）

模型：到达率 λ、服务率 μ、服务台 c 个；先算 Erlang-C 排队概率，再给 Lq、Wq、L、W、ρ。
适用：窗口/充电桩/客服坐席等服务能力评估；λ/(cμ) ≥ 1 时系统不稳定。
接口：solve(lam, mu, c) -> 指标字典；运行：python main.py
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_fig, save_table, set_style  # noqa: E402


def build_demo() -> dict:
    return {"lam": 8.0, "mu": 3.0, "c": 4}


def solve(lam: float, mu: float, c: int) -> dict:
    rho = lam / (c * mu)
    if rho >= 1:
        raise ValueError(f"系统不稳定：ρ={rho:.3f} ≥ 1，需增加服务台或提高服务率")
    a = lam / mu
    sum_terms = sum(a ** k / math.factorial(k) for k in range(c))
    p0 = 1 / (sum_terms + a ** c / (math.factorial(c) * (1 - rho)))
    erlang_c = a ** c / (math.factorial(c) * (1 - rho)) * p0
    lq = erlang_c * rho / (1 - rho)
    wq = lq / lam
    w = wq + 1 / mu
    return {
        "服务台利用率ρ": rho,
        "排队概率C(c,a)": erlang_c,
        "空闲概率P0": p0,
        "平均队长L": lq + a,
        "平均等待队长Lq": lq,
        "平均逗留W": w,
        "平均等待Wq": wq,
    }


def main() -> None:
    import numpy as np

    data = demo(__file__, build_demo)
    metrics = solve(data["lam"], data["mu"], int(data["c"]))
    report("M/M/c", 到达率=data["lam"], 服务率=data["mu"], 服务台=data["c"],
           利用率=round(metrics["服务台利用率ρ"], 4), 平均等待=round(metrics["平均等待Wq"], 4))
    save_table(__file__, "稳态指标", {"指标": list(metrics), "数值": [round(v, 6) for v in metrics.values()]})
    servers = list(range(1, 13))
    waits = []
    for c in servers:
        try:
            waits.append(solve(data["lam"], data["mu"], c)["平均等待Wq"])
        except ValueError:
            waits.append(float("nan"))
    plt = set_style()
    fig, ax = plt.subplots()
    ax.plot(servers, waits, "o-", color="#0072B2")
    ax.axvline(int(data["c"]), color="#D55E00", ls="--", lw=0.9)
    ax.annotate(f"当前配置 c={data['c']}", xy=(data["c"], metrics["平均等待Wq"]),
                xytext=(data["c"] + 1.5, max(w * 0.6 for w in waits if w == w)),
                fontsize=8, arrowprops=dict(arrowstyle="->", color="#444444"))
    ax.set_xlabel("服务台数量 c")
    ax.set_ylabel("平均等待时间 Wq")
    ax.set_yscale("log")
    save_fig(__file__, fig, "queueing_mmc")


if __name__ == "__main__":
    main()
