"""普通克里金插值（Python 最小可运行模板）

思路：由样本点估计指数变异函数 γ(h) = c0 + c(1 - e^{-h/a})，求解普通克里金方程组
（含拉格朗日乘子，保证无偏），对网格点给出预测值与克里金方差。
适用：气象/水文/污染等空间插值与制图；样本点较少时优于反距离加权。
接口：solve(points, values, grid) -> (预测面, 克里金方差)；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_fig, save_table, set_style  # noqa: E402


def build_demo() -> dict:
    rng = np.random.default_rng(42)
    points = rng.uniform(0, 10, size=(24, 2))
    values = np.sin(points[:, 0] / 2) + np.cos(points[:, 1] / 3) + rng.normal(scale=0.1, size=24)
    axis = np.linspace(0, 10, 40)
    grid = np.array(np.meshgrid(axis, axis)).reshape(2, -1).T
    return {"points": points, "values": values, "grid": grid, "axis": axis}


def variogram_model(h, nugget: float, sill: float, rang: float):
    return nugget + sill * (1 - np.exp(-h / rang))


def fit_variogram(points, values):
    """经验变异函数 + 简易最小二乘拟合（固定块宽）。"""
    n = len(points)
    pairs = []
    for i in range(n):
        for j in range(i + 1, n):
            h = float(np.linalg.norm(points[i] - points[j]))
            pairs.append((h, 0.5 * (values[i] - values[j]) ** 2))
    pairs = np.array(sorted(pairs))
    bins = np.linspace(0, pairs[:, 0].max(), 9)
    empirical = []
    for k in range(len(bins) - 1):
        mask = (pairs[:, 0] >= bins[k]) & (pairs[:, 0] < bins[k + 1])
        if mask.sum() >= 2:
            empirical.append((pairs[mask, 0].mean(), pairs[mask, 1].mean()))
    empirical = np.array(empirical)
    grid = np.linspace(0.01, 3, 25)
    best = None
    for nugget in [0.0, 0.01, 0.05]:
        for sill in grid:
            for rang in np.linspace(0.5, 5, 20):
                residual = np.sum((variogram_model(empirical[:, 0], nugget, sill, rang) - empirical[:, 1]) ** 2)
                if best is None or residual < best[0]:
                    best = (residual, nugget, sill, rang)
    _, nugget, sill, rang = best
    return (nugget, sill, rang), empirical


def solve(points, values, grid):
    points, values = np.asarray(points, float), np.asarray(values, float)
    params, empirical = fit_variogram(points, values)
    nugget, sill, rang = params
    n = len(points)
    D = np.linalg.norm(points[:, None, :] - points[None, :, :], axis=-1)
    Gamma = variogram_model(D, nugget, sill, rang)
    A = np.zeros((n + 1, n + 1))
    A[:n, :n] = Gamma
    A[:n, n] = 1
    A[n, :n] = 1
    predictions, variances = [], []
    for target in np.asarray(grid, float):
        d = np.linalg.norm(points - target, axis=1)
        b = np.concatenate([variogram_model(d, nugget, sill, rang), [1.0]])
        solution = np.linalg.solve(A, b)
        weights = solution[:n]
        predictions.append(float(weights @ values))
        variances.append(float(weights @ b[:n] + solution[n]))
    return np.array(predictions), np.array(variances), params, empirical


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    predictions, variances, params, empirical = solve(data["points"], data["values"], data["grid"])
    report("普通克里金", 变差参数=f"c0={params[0]:.3f}, c={params[1]:.3f}, a={params[2]:.3f}",
           预测范围=f"{predictions.min():.3f}~{predictions.max():.3f}",
           平均克里金方差=round(float(variances.mean()), 5))
    save_table(__file__, "变异函数拟合", {"距离": np.round(empirical[:, 0], 4),
                                          "经验变异值": np.round(empirical[:, 1], 6)})
    axis = np.asarray(data["axis"])
    plt = set_style()
    fig, axes = plt.subplots(1, 3, figsize=(9.6, 3.2))
    left, right = axis[0], axis[-1]
    image = axes[0].imshow(predictions.reshape(len(axis), len(axis)), origin="lower",
                           extent=[left, right, left, right], cmap="viridis")
    axes[0].scatter(data["points"][:, 0], data["points"][:, 1], c="white", s=12, edgecolor="black")
    axes[0].set_title("克里金预测面")
    fig.colorbar(image, ax=axes[0], fraction=0.046)
    image2 = axes[1].imshow(variances.reshape(len(axis), len(axis)), origin="lower",
                            extent=[left, right, left, right], cmap="magma")
    axes[1].scatter(data["points"][:, 0], data["points"][:, 1], c="white", s=12, edgecolor="black")
    axes[1].set_title("克里金方差")
    fig.colorbar(image2, ax=axes[1], fraction=0.046)
    axes[2].scatter(empirical[:, 0], empirical[:, 1], color="#0072B2", label="经验变异函数")
    hs = np.linspace(0.01, empirical[:, 0].max(), 100)
    axes[2].plot(hs, variogram_model(hs, *params), color="#D55E00", label="拟合模型")
    axes[2].set_xlabel("距离 h")
    axes[2].set_ylabel("γ(h)")
    axes[2].legend(fontsize=8)
    save_fig(__file__, fig, "kriging")
