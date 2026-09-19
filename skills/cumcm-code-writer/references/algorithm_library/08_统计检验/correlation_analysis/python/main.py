"""相关分析 · Pearson / Spearman / Kendall（Python 最小可运行模板）

步骤：按数据类型与单调性选择相关系数 → 显著性检验 → 输出相关系数矩阵与 p 值矩阵。
接口：solve(data, names) -> (Pearson 矩阵, Spearman 矩阵, p 值矩阵)；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_fig, save_table, set_style  # noqa: E402


def build_demo() -> dict:
    rng = np.random.default_rng(42)
    x1 = rng.normal(size=120)
    x2 = 0.7 * x1 + rng.normal(scale=0.7, size=120)
    x3 = np.exp(x1 / 2) + rng.normal(scale=0.3, size=120)
    x4 = rng.normal(size=120)
    return {"data": np.column_stack([x1, x2, x3, x4]), "names": ["X1", "X2", "X3", "X4"]}


def solve(data, names):
    data = np.asarray(data, float)
    n = data.shape[1]
    pearson = np.eye(n)
    spearman = np.eye(n)
    p_values = np.eye(n)
    for i in range(n):
        for j in range(i + 1, n):
            r, p = stats.pearsonr(data[:, i], data[:, j])
            rs, _ = stats.spearmanr(data[:, i], data[:, j])
            pearson[i, j] = pearson[j, i] = r
            spearman[i, j] = spearman[j, i] = rs
            p_values[i, j] = p_values[j, i] = p
    return pearson, spearman, p_values


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    pearson, spearman, p_values = solve(data["data"], data["names"])
    report("相关分析", 样本量=len(data["data"]),
           最强Pearson=round(float(pearson[np.triu_indices(len(data["names"]), 1)][
               np.argmax(np.abs(pearson[np.triu_indices(len(data["names"]), 1)]))]), 4))
    for label, matrix in [("Pearson", pearson), ("Spearman", spearman), ("p值", p_values)]:
        frame = pd.DataFrame(np.round(matrix, 6), index=data["names"], columns=data["names"])
        frame.insert(0, "变量", data["names"])
        save_table(__file__, f"相关系数_{label}", frame)
    plt = set_style()
    fig, axes = plt.subplots(1, 2, figsize=(7.6, 3.4))
    for ax, matrix, title in zip(axes, [pearson, spearman], ["Pearson 相关", "Spearman 相关"]):
        image = ax.imshow(matrix, cmap="RdBu_r", vmin=-1, vmax=1)
        ax.set_xticks(range(len(data["names"])), data["names"])
        ax.set_yticks(range(len(data["names"])), data["names"])
        ax.set_title(title)
        ax.grid(False)
        for i in range(len(data["names"])):
            for j in range(len(data["names"])):
                ax.text(j, i, f"{matrix[i, j]:.2f}", ha="center", va="center", fontsize=7)
    fig.colorbar(image, ax=axes, fraction=0.03)
    save_fig(__file__, fig, "correlation_analysis")
