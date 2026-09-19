"""排队系统蒙特卡洛仿真（Python 最小可运行模板）

模型：M/M/1 单服务台，到达间隔~Exp(1/λ)、服务时间~Exp(1/μ)；统计平均等待、队长与利用率。
接口：solve(lam, mu, n_customers, seed) -> (指标)；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_fig, save_table, set_style  # noqa: E402


def build_demo() -> dict:
    return {"lam": 2.4, "mu": 3.0, "n_customers": 5000, "warmup": 500}


def solve(lam, mu, n_customers: int, warmup: int = 500, seed: int = 42):
    rng = np.random.default_rng(seed)
    arrivals = np.cumsum(rng.exponential(1 / lam, n_customers))
    service = rng.exponential(1 / mu, n_customers)
    start = np.zeros(n_customers)
    finish = np.zeros(n_customers)
    for i in range(n_customers):
        start[i] = max(arrivals[i], finish[i - 1] if i else 0.0)
        finish[i] = start[i] + service[i]
    wait = start - arrivals
    busy = service.sum()
    horizon = finish[-1]
    metrics = {
        "平均等待时间": float(wait[warmup:].mean()),
        "最大等待时间": float(wait[warmup:].max()),
        "平均逗留时间": float((wait + service)[warmup:].mean()),
        "系统利用率": float(busy / horizon),
        "到达率": lam,
        "服务率": mu,
    }
    return metrics, wait, service, arrivals


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    metrics, wait, service, arrivals = solve(data["lam"], data["mu"], int(data["n_customers"]))
    theory = 1 / (data["mu"] - data["lam"])
    report("排队仿真", 平均等待=round(metrics["平均等待时间"], 4), 理论等待=round(theory, 4),
           利用率=round(metrics["系统利用率"], 4), 顾客数=int(data["n_customers"]))
    save_table(__file__, "仿真指标", {"指标": list(metrics), "数值": [round(v, 6) for v in metrics.values()]})
    save_table(__file__, "等待时间样本", {"顾客": np.arange(1, 201), "等待时间": np.round(wait[:200], 6)})
    plt = set_style()
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.0))
    axes[0].hist(wait[500:], bins=40, color="#56B4E9", edgecolor="white")
    axes[0].set_xlabel("等待时间")
    axes[0].set_ylabel("频数")
    axes[1].plot(np.arange(1, len(wait) + 1), np.cumsum(wait) / np.arange(1, len(wait) + 1),
                 color="#0072B2")
    axes[1].axhline(theory, color="#D55E00", ls="--", label="理论均值")
    axes[1].set_xlabel("顾客序号（累计）")
    axes[1].set_ylabel("累计平均等待")
    axes[1].legend()
    save_fig(__file__, fig, "queue_simulation")
