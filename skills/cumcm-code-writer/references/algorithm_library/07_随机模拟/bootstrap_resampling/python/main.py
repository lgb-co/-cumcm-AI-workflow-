"""Bootstrap 重采样（Python 最小可运行模板）

用途：小样本统计量的置信区间与稳健性评估；输出均值/中位数的 Bootstrap 分布与 95% 区间。
接口：solve(data, n_boot, seed) -> (置信区间字典, 重采样矩阵)；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_fig, save_table, set_style  # noqa: E402


def build_demo() -> dict:
    rng = np.random.default_rng(42)
    # 右偏分布：Bootstrap 比正态近似更合适
    return {"data": rng.lognormal(mean=1.0, sigma=0.6, size=60), "n_boot": 5000}


def solve(data, n_boot: int = 5000, seed: int = 42, alpha: float = 0.05):
    rng = np.random.default_rng(seed)
    data = np.asarray(data, float)
    n = len(data)
    indices = rng.integers(0, n, size=(n_boot, n))
    resamples = data[indices]
    means = resamples.mean(axis=1)
    medians = np.median(resamples, axis=1)
    interval = {
        "均值": (float(np.quantile(means, alpha / 2)), float(np.quantile(means, 1 - alpha / 2))),
        "中位数": (float(np.quantile(medians, alpha / 2)), float(np.quantile(medians, 1 - alpha / 2))),
    }
    return interval, means, medians


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    interval, means, medians = solve(data["data"], int(data["n_boot"]))
    report("Bootstrap", 样本量=len(data["data"]), 重采样次数=int(data["n_boot"]),
           均值区间=np.round(interval["均值"], 4).tolist(),
           中位数区间=np.round(interval["中位数"], 4).tolist())
    save_table(__file__, "置信区间", {"统计量": ["均值", "中位数"],
                                      "下界": [interval["均值"][0], interval["中位数"][0]],
                                      "上界": [interval["均值"][1], interval["中位数"][1]]})
    save_table(__file__, "Bootstrap分布", {"重采样序号": np.arange(1, 501),
                                           "均值": np.round(means[:500], 6),
                                           "中位数": np.round(medians[:500], 6)})
    plt = set_style()
    fig, ax = plt.subplots()
    ax.hist(means, bins=50, color="#56B4E9", edgecolor="white", label="Bootstrap 均值")
    ax.axvline(np.mean(data["data"]), color="#D55E00", label="样本均值")
    ax.axvline(interval["均值"][0], color="#666666", ls="--", lw=0.9)
    ax.axvline(interval["均值"][1], color="#666666", ls="--", lw=0.9)
    ax.set_xlabel("均值")
    ax.set_ylabel("频数")
    ax.legend()
    save_fig(__file__, fig, "bootstrap_resampling")
