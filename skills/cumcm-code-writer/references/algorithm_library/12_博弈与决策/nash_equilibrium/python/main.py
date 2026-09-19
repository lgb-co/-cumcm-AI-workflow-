"""纳什均衡求解 · 双人矩阵博弈（Python 最小可运行模板）

内容：① 枚举纯策略纳什均衡（互为最优反应）；② 对 2×2 博弈解析求混合策略均衡
（使对手两策略收益无差异）。输出均衡集合与期望收益。
接口：solve(A, B) -> (纯策略均衡, 混合均衡)；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_fig, save_table, set_style  # noqa: E402


def build_demo() -> dict:
    # 经典"囚徒困境"收益矩阵（行玩家收益 A，列玩家收益 B）
    A = np.array([[3.0, 0.0], [5.0, 1.0]])
    B = np.array([[3.0, 5.0], [0.0, 1.0]])
    return {"A": A, "B": B, "row_names": ["合作", "背叛"], "col_names": ["合作", "背叛"]}


def pure_nash(A, B):
    equilibria = []
    for i in range(A.shape[0]):
        for j in range(A.shape[1]):
            best_row = A[i, j] >= A[:, j].max() - 1e-12
            best_col = B[i, j] >= B[i, :].max() - 1e-12
            if best_row and best_col:
                equilibria.append((i, j, float(A[i, j]), float(B[i, j])))
    return equilibria


def mixed_nash_2x2(A, B):
    """行玩家以概率 p 选策略 1，列玩家以概率 q 选策略 1，使对手无差异。"""
    denom_q = (A[0, 0] - A[0, 1] - A[1, 0] + A[1, 1])
    denom_p = (B[0, 0] - B[1, 0] - B[0, 1] + B[1, 1])
    if abs(denom_q) < 1e-12 or abs(denom_p) < 1e-12:
        return None
    p = (A[1, 1] - A[0, 1]) / denom_q
    q = (B[1, 1] - B[1, 0]) / denom_p
    if not (0 <= p <= 1 and 0 <= q <= 1):
        return None
    payoff_row = p * (q * A[0, 0] + (1 - q) * A[0, 1]) + (1 - p) * (q * A[1, 0] + (1 - q) * A[1, 1])
    payoff_col = q * (p * B[0, 0] + (1 - p) * B[1, 0]) + (1 - q) * (p * B[0, 1] + (1 - p) * B[1, 1])
    return (p, q, float(payoff_row), float(payoff_col))


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    A, B = np.asarray(data["A"], float), np.asarray(data["B"], float)
    pure = pure_nash(A, B)
    mixed = mixed_nash_2x2(A, B)
    row_names = data["row_names"]
    col_names = data["col_names"]
    report("纳什均衡", 纯策略均衡=[f"({row_names[i]}, {col_names[j]})" for i, j, _, _ in pure] or "无",
           混合均衡=("无" if mixed is None else f"行玩家 p={mixed[0]:.3f}，列玩家 q={mixed[1]:.3f}"))
    save_table(__file__, "纯策略均衡",
               [{"行策略": row_names[i], "列策略": col_names[j], "行收益": round(r, 4), "列收益": round(c, 4)}
                for i, j, r, c in pure])
    if mixed:
        save_table(__file__, "混合策略均衡",
                   {"策略": [f"行玩家选{row_names[0]}", f"列玩家选{col_names[0]}"],
                    "概率": [round(mixed[0], 6), round(mixed[1], 6)],
                    "期望收益": [round(mixed[2], 6), round(mixed[3], 6)]})
    plt = set_style()
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.2))
    grid = np.linspace(0, 1, 200)
    row_payoff = [p * (q * A[0, 0] + (1 - q) * A[0, 1]) + (1 - p) * (q * A[1, 0] + (1 - q) * A[1, 1])
                  for p, q in zip(grid, grid)]
    col_payoff = [q * (p * B[0, 0] + (1 - p) * B[1, 0]) + (1 - q) * (p * B[0, 1] + (1 - p) * B[1, 1])
                  for p, q in zip(grid, grid)]
    axes[0].plot(grid, row_payoff, color="#0072B2", label="行玩家期望收益")
    axes[0].plot(grid, col_payoff, color="#D55E00", label="列玩家期望收益")
    axes[0].set_xlabel("偏离概率（对称示意）")
    axes[0].set_ylabel("期望收益")
    axes[0].legend(fontsize=8)
    for i in range(2):
        for j in range(2):
            axes[1].text(j, 1 - i, f"({A[i, j]:g}, {B[i, j]:g})", ha="center", va="center", fontsize=11)
    axes[1].set_xticks([0, 1], col_names)
    axes[1].set_yticks([1, 0], row_names)
    axes[1].set_xlabel("列玩家")
    axes[1].set_ylabel("行玩家")
    axes[1].set_title("收益矩阵（行收益, 列收益）")
    axes[1].set_xlim(-0.6, 1.6)
    axes[1].set_ylim(-0.6, 1.6)
    axes[1].grid(False)
    save_fig(__file__, fig, "nash_equilibrium")
