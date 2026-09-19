"""Z-Score 异常值检测（Python 最小可运行模板）

判定：|z| > 阈值记为异常；适合近似正态数据，长尾分布应改用 IQR 或稳健 Z 值。
接口：solve(series, threshold) -> (异常掩码, z 值, 统计对照)；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_fig, save_table, set_style  # noqa: E402


def build_demo() -> dict:
    rng = np.random.default_rng(42)
    series = rng.normal(loc=100, scale=8, size=150)
    series[[5, 77, 140]] = [150.0, 40.0, 155.0]
    return {"series": series, "threshold": 3.0}


def solve(series, threshold: float = 3.0, robust: bool = False):
    series = np.asarray(series, float)
    if robust:
        center = np.median(series)
        scale = 1.4826 * np.median(np.abs(series - center))
    else:
        center, scale = series.mean(), series.std(ddof=1)
    z = (series - center) / scale
    mask = np.abs(z) > threshold
    stats = {
        "异常点数": int(mask.sum()),
        "异常比例": float(mask.mean()),
        "中心值": float(center),
        "尺度": float(scale),
        "最大|z|": float(np.abs(z).max()),
    }
    return mask, z, stats


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    mask, z, stats = solve(data["series"], float(data["threshold"]))
    report("Z-Score 异常检测", 样本量=len(data["series"]), 阈值=data["threshold"],
           异常点数=stats["异常点数"], 最大z=round(stats["最大|z|"], 3))
    save_table(__file__, "异常标记", {"序号": np.arange(1, len(mask) + 1),
                                      "数值": np.round(data["series"], 4),
                                      "Z值": np.round(z, 4),
                                      "是否异常": ["是" if m else "否" for m in mask]})
    plt = set_style()
    fig, ax = plt.subplots()
    ax.plot(z, "o-", ms=3.5, color="#0072B2")
    ax.scatter(np.where(mask)[0], z[mask], color="#D55E00", s=30, zorder=3)
    ax.axhline(float(data["threshold"]), color="#666666", ls="--", lw=0.9)
    ax.axhline(-float(data["threshold"]), color="#666666", ls="--", lw=0.9)
    ax.set_xlabel("样本序号")
    ax.set_ylabel("Z 值")
    save_fig(__file__, fig, "zscore_outlier")
