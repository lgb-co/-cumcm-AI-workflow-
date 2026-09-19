"""Moran's I 空间自相关分析（Python 最小可运行模板）

公式：I = (n / S0) · [Σ_i Σ_j w_ij (x_i - x̄)(x_j - x̄)] / Σ_i (x_i - x̄)²
空间权重用行标准化的邻接矩阵（演示为网格 rook 邻接）；输出 I、期望值 E(I) 与 z 检验。
接口：solve(values, weights) -> (I, E(I), z, p)；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_fig, save_table, set_style  # noqa: E402


def build_demo() -> dict:
    rng = np.random.default_rng(42)
    side = 8
    base = rng.normal(size=(side, side))
    # 制造空间聚集：用邻域平均平滑一次
    smooth = (base + np.roll(base, 1, 0) + np.roll(base, -1, 0)
              + np.roll(base, 1, 1) + np.roll(base, -1, 1)) / 5
    n = side * side
    weights = np.zeros((n, n))
    for r in range(side):
        for c in range(side):
            index = r * side + c
            for dr, dc in ((0, 1), (1, 0)):
                rr, cc = r + dr, c + dc
                if rr < side and cc < side:
                    other = rr * side + cc
                    weights[index, other] = weights[other, index] = 1
    return {"values": smooth.ravel(), "weights": weights, "side": side}


def solve(values, weights):
    x = np.asarray(values, float)
    W = np.asarray(weights, float)
    n = len(x)
    row_sum = W.sum(axis=1, keepdims=True)
    W = np.divide(W, row_sum, out=np.zeros_like(W), where=row_sum > 0)
    z = x - x.mean()
    S0 = W.sum()
    numerator = float(z @ W @ z)
    denominator = float((z ** 2).sum())
    I = n / S0 * numerator / denominator
    EI = -1 / (n - 1)
    # 随机化假设下的方差（行标准化权重）
    weights_sum_sq = float((W ** 2).sum())
    VI = (n ** 2 * weights_sum_sq - n * S0) / ((n ** 2 - 1) * S0 ** 2) - EI ** 2
    z_score = (I - EI) / np.sqrt(VI)
    p_value = float(2 * (1 - stats.norm.cdf(abs(z_score))))
    return float(I), float(EI), float(z_score), p_value, W


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    I, EI, z_score, p_value, W = solve(data["values"], data["weights"])
    conclusion = "显著空间正相关（聚集）" if p_value < 0.05 and I > EI else \
        "显著空间负相关（离散）" if p_value < 0.05 else "无显著空间自相关"
    report("Moran's I", I=round(I, 4), 期望值=round(EI, 4), z=round(z_score, 4),
           p值=f"{p_value:.4f}", 结论=conclusion)
    save_table(__file__, "全局自相关", {"指标": ["Moran's I", "E(I)", "z", "p"],
                                        "数值": [round(I, 6), round(EI, 6), round(z_score, 6), round(p_value, 6)]})
    side = int(data["side"])
    plt = set_style()
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.4))
    image = axes[0].imshow(np.asarray(data["values"]).reshape(side, side), cmap="RdBu_r")
    axes[0].set_title("区域取值分布")
    axes[0].grid(False)
    fig.colorbar(image, ax=axes[0], fraction=0.046)
    lag = W @ (np.asarray(data["values"]) - np.mean(data["values"]))
    axes[1].scatter(np.asarray(data["values"]) - np.mean(data["values"]), lag, s=18, color="#0072B2")
    axes[1].axhline(0, color="#666666", lw=0.8)
    axes[1].axvline(0, color="#666666", lw=0.8)
    slope = np.polyfit(np.asarray(data["values"]) - np.mean(data["values"]), lag, 1)
    xs = np.linspace(lag.min(), lag.max(), 10)
    axes[1].plot(xs, np.polyval(slope, xs), color="#D55E00", lw=1.2)
    axes[1].set_xlabel("中心化取值")
    axes[1].set_ylabel("空间滞后")
    axes[1].set_title(f"Moran 散点图（I={I:.3f}）")
    save_fig(__file__, fig, "moran_i")
