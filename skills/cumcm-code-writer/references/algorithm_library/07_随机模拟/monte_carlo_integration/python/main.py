"""蒙特卡洛积分与收敛性分析（Python 最小可运行模板）

模型：计算 ∫_0^1 e^x dx，用均匀抽样估计均值与标准误，并按 1/√n 收敛。
接口：solve(n_list, seed) -> (各样本量估计值, 标准误)；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_fig, save_table, set_style  # noqa: E402


def build_demo() -> dict:
    return {"n_list": [100, 1000, 10000, 100000, 1000000]}


def solve(n_list, seed: int = 42):
    rng = np.random.default_rng(seed)
    estimates, errors = [], []
    for n in n_list:
        samples = np.exp(rng.random(n))
        estimates.append(float(samples.mean()))
        errors.append(float(samples.std(ddof=1) / np.sqrt(n)))
    return np.array(estimates), np.array(errors)


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    estimates, errors = solve(data["n_list"])
    true_value = float(np.e - 1)
    report("蒙特卡洛积分", 真值=round(true_value, 6), 最大样本量估计=round(float(estimates[-1]), 6),
           标准误=f"{errors[-1]:.2e}", 相对误差=f"{abs(estimates[-1] - true_value) / true_value:.2e}")
    save_table(__file__, "收敛过程", {"样本量": data["n_list"], "估计值": np.round(estimates, 6),
                                      "标准误": errors})
    plt = set_style()
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.0))
    axes[0].semilogx(data["n_list"], estimates, "o-", color="#0072B2", label="估计值")
    axes[0].axhline(true_value, color="#D55E00", ls="--", label="真值")
    axes[0].set_xlabel("样本量")
    axes[0].set_ylabel("积分估计")
    axes[0].legend()
    axes[1].loglog(data["n_list"], errors, "o-", color="#009E73")
    axes[1].set_xlabel("样本量")
    axes[1].set_ylabel("标准误")
    axes[1].set_title("1/√n 收敛")
    save_fig(__file__, fig, "monte_carlo_integration")
