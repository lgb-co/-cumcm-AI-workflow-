"""Mann-Kendall 趋势检验（Python 最小可运行模板）

步骤：计算 S 统计量与方差（含并列值校正）→ 标准化 Z → 双侧 p 值 → 结合 Sen's slope 量化趋势。
接口：solve(series) -> (Z, p, Sen 斜率, 趋势结论)；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_table  # noqa: E402


def build_demo() -> dict:
    rng = np.random.default_rng(42)
    return {"series": 0.35 * np.arange(40) + rng.normal(scale=1.2, size=40) + 10}


def solve(series, alpha: float = 0.05):
    x = np.asarray(series, float)
    n = len(x)
    s = sum(np.sign(x[j] - x[i]) for i in range(n - 1) for j in range(i + 1, n))
    _, counts = np.unique(x, return_counts=True)
    tie = sum(c * (c - 1) * (2 * c + 5) for c in counts)
    var_s = (n * (n - 1) * (2 * n + 5) - tie) / 18
    if s > 0:
        z = (s - 1) / np.sqrt(var_s)
    elif s < 0:
        z = (s + 1) / np.sqrt(var_s)
    else:
        z = 0.0
    p = 2 * (1 - stats.norm.cdf(abs(z)))
    slopes = [(x[j] - x[i]) / (j - i) for i in range(n - 1) for j in range(i + 1, n)]
    sen = float(np.median(slopes))
    trend = "显著上升" if (p < alpha and sen > 0) else "显著下降" if (p < alpha and sen < 0) else "无显著趋势"
    return float(z), float(p), sen, trend


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    z, p, sen, trend = solve(data["series"])
    report("Mann-Kendall", Z=round(z, 4), p值=f"{p:.4f}", Sen斜率=round(sen, 4), 结论=trend)
    save_table(__file__, "趋势检验", {"统计量": ["Z", "p", "Sen斜率"], "数值": [z, p, sen]})
