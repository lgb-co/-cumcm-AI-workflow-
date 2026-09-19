"""贝叶斯参数估计 · 共轭先验（Python 最小可运行模板）

场景：成功率参数 θ 的 Beta-二项模型；先验 Beta(α0, β0)，观测 n 次成功 k 次，
后验解析解 Beta(α0+k, β0+n-k)，输出后验均值、可信区间与先验-后验对照。
接口：solve(k, n, prior) -> (后验参数, 后验统计量)；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_fig, save_table, set_style  # noqa: E402


def build_demo() -> dict:
    return {"k": 57, "n": 100, "alpha0": 2.0, "beta0": 2.0}


def solve(k: int, n: int, alpha0: float, beta0: float, credible: float = 0.95):
    alpha_post = alpha0 + k
    beta_post = beta0 + n - k
    posterior = stats.beta(alpha_post, beta_post)
    prior = stats.beta(alpha0, beta0)
    lower, upper = posterior.ppf([(1 - credible) / 2, 1 - (1 - credible) / 2])
    metrics = {
        "后验均值": float(posterior.mean()),
        "后验众数": float((alpha_post - 1) / (alpha_post + beta_post - 2)) if alpha_post > 1 and beta_post > 1 else float("nan"),
        "后验标准差": float(posterior.std()),
        "可信区间下界": float(lower),
        "可信区间上界": float(upper),
        "先验均值": float(prior.mean()),
        "频率估计": k / n,
    }
    return (alpha_post, beta_post), metrics


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    (alpha_post, beta_post), metrics = solve(int(data["k"]), int(data["n"]),
                                             float(data["alpha0"]), float(data["beta0"]))
    report("贝叶斯估计", 后验参数=f"Beta({alpha_post:g}, {beta_post:g})",
           后验均值=round(metrics["后验均值"], 4), 可信区间=[round(metrics["可信区间下界"], 4),
                                                       round(metrics["可信区间上界"], 4)],
           频率估计=round(metrics["频率估计"], 4))
    save_table(__file__, "后验统计量", {"指标": list(metrics), "数值": [round(v, 6) for v in metrics.values()]})
    grid = np.linspace(0, 1, 400)
    plt = set_style()
    fig, ax = plt.subplots()
    ax.plot(grid, stats.beta(data["alpha0"], data["beta0"]).pdf(grid), color="#999999", label="先验")
    ax.plot(grid, stats.beta(alpha_post, beta_post).pdf(grid), color="#0072B2", label="后验")
    ax.axvline(metrics["频率估计"], color="#D55E00", ls="--", lw=0.9, label="频率估计")
    ax.fill_between(grid, 0, stats.beta(alpha_post, beta_post).pdf(grid),
                    where=(grid >= metrics["可信区间下界"]) & (grid <= metrics["可信区间上界"]),
                    color="#0072B2", alpha=0.15, label="95% 可信区间")
    ax.set_xlabel("成功率 θ")
    ax.set_ylabel("概率密度")
    ax.legend(fontsize=8)
    save_fig(__file__, fig, "bayesian_inference")
