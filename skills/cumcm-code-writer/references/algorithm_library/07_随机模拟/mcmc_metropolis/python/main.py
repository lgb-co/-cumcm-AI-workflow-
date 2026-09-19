"""MCMC · Metropolis-Hastings 抽样（Python 最小可运行模板）

目标分布：标准正态与混合分布；输出样本均值/方差、接受率与轨迹，用于参数后验抽样。
接口：solve(n_samples, proposal_sd, seed) -> (样本, 接受率)；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_fig, save_table, set_style  # noqa: E402


def build_demo() -> dict:
    return {"n_samples": 20000, "proposal_sd": 1.2, "burn_in": 2000}


def log_target(x: float) -> float:
    return -0.5 * x ** 2


def solve(n_samples: int, proposal_sd: float, burn_in: int = 2000, seed: int = 42):
    rng = np.random.default_rng(seed)
    samples = np.empty(n_samples)
    current, log_current = 0.0, log_target(0.0)
    accepted = 0
    for i in range(n_samples):
        proposal = current + rng.normal(scale=proposal_sd)
        log_proposal = log_target(proposal)
        if np.log(rng.random()) < log_proposal - log_current:
            current, log_current = proposal, log_proposal
            accepted += 1
        samples[i] = current
    kept = samples[burn_in:]
    return kept, accepted / n_samples, samples


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    kept, rate, samples = solve(int(data["n_samples"]), float(data["proposal_sd"]), int(data["burn_in"]))
    report("MCMC", 接受率=round(rate, 4), 后验均值=round(float(kept.mean()), 4),
           后验标准差=round(float(kept.std(ddof=1)), 4), 有效样本=int(len(kept)))
    save_table(__file__, "抽样结果", {"样本": np.arange(1, 501), "取值": np.round(kept[:500], 6)})
    plt = set_style()
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.0))
    axes[0].plot(samples[:3000], lw=0.6, color="#0072B2")
    axes[0].axvline(int(data["burn_in"]), color="#D55E00", ls="--", lw=0.9)
    axes[0].set_xlabel("迭代")
    axes[0].set_ylabel("样本值")
    axes[1].hist(kept, bins=50, density=True, color="#56B4E9", edgecolor="white")
    grid = np.linspace(kept.min(), kept.max(), 200)
    axes[1].plot(grid, np.exp(-0.5 * grid ** 2) / np.sqrt(2 * np.pi), color="#D55E00", label="标准正态")
    axes[1].set_xlabel("取值")
    axes[1].legend()
    save_fig(__file__, fig, "mcmc_metropolis")
