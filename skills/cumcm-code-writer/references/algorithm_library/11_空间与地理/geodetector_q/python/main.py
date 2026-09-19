"""地理探测器 · 因子探测 q 统计量（Python 最小可运行模板）

公式：q = 1 - Σ_h (N_h σ_h²) / (N σ²)，q ∈ [0,1]，越大表示该因子对空间分异的解释力越强。
同时给出分层均值与样本数，便于判断分层是否均衡。
接口：solve(y, strata) -> (q, 分层统计)；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_fig, save_table, set_style  # noqa: E402


def build_demo() -> dict:
    rng = np.random.default_rng(42)
    n = 300
    factor = rng.integers(0, 5, size=n)          # 5 个分层
    y = 10 + 2.5 * factor + rng.normal(scale=1.5, size=n)   # 该因子解释力较强
    noise = rng.integers(0, 3, size=n)                       # 噪声因子
    return {"y": y, "strata": factor, "compare": noise}


def solve(y, strata):
    y = np.asarray(y, float)
    strata = np.asarray(strata)
    total_var = y.var(ddof=0)
    rows = []
    weighted = 0.0
    for level in np.unique(strata):
        subset = y[strata == level]
        weighted += len(subset) * subset.var(ddof=0)
        rows.append({"分层": level, "样本数": int(len(subset)),
                     "均值": round(float(subset.mean()), 4),
                     "层内方差": round(float(subset.var(ddof=0)), 4)})
    q = 1 - weighted / (len(y) * total_var)
    return float(q), rows


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    q_main, rows_main = solve(data["y"], data["strata"])
    q_noise, _ = solve(data["y"], data["compare"])
    report("地理探测器", 主因子q=round(q_main, 4), 噪声因子q=round(q_noise, 4),
           解释力比较="主因子明显更强" if q_main > q_noise * 2 else "两者接近，需检查分层")
    save_table(__file__, "分层统计", rows_main)
    save_table(__file__, "因子对比", {"因子": ["主因子", "噪声因子"], "q值": [round(q_main, 6), round(q_noise, 6)]})
    plt = set_style()
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.2))
    levels = [row["分层"] for row in rows_main]
    counts = [row["样本数"] for row in rows_main]
    axes[0].bar([str(level) for level in levels], counts, color="#56B4E9")
    axes[0].set_xlabel("分层")
    axes[0].set_ylabel("样本数")
    axes[0].set_title("分层样本量")
    positions = np.arange(len(levels))
    for index, row in enumerate(rows_main):
        axes[1].scatter(np.full(row["样本数"], index) + np.random.default_rng(index).normal(scale=0.03, size=row["样本数"]),
                        data["y"][np.asarray(data["strata"]) == row["分层"]], s=6, alpha=0.4, color="#0072B2")
        axes[1].plot([index - 0.3, index + 0.3], [row["均值"]] * 2, color="#D55E00", lw=2)
    axes[1].set_xticks(positions, [str(level) for level in levels])
    axes[1].set_xlabel("分层")
    axes[1].set_ylabel("y")
    axes[1].set_title(f"分层均值对比（q={q_main:.3f}）")
    save_fig(__file__, fig, "geodetector_q")
