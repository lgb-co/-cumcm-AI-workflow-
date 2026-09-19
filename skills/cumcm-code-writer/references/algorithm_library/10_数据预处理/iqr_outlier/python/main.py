"""IQR 四分位距异常值检测（Python 最小可运行模板）

判定：值落在 [Q1-1.5IQR, Q3+1.5IQR] 之外记为异常；输出异常点位置、边界与剔除前后统计。
接口：solve(series, factor) -> (异常掩码, 边界, 统计对照)；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_fig, save_table, set_style  # noqa: E402


def build_demo() -> dict:
    rng = np.random.default_rng(42)
    series = rng.normal(loc=50, scale=5, size=120)
    series[[10, 45, 90]] = [85.0, -12.0, 96.0]
    return {"series": series, "factor": 1.5}


def solve(series, factor: float = 1.5):
    series = np.asarray(series, float)
    q1, q3 = np.quantile(series, [0.25, 0.75])
    iqr = q3 - q1
    low, high = q1 - factor * iqr, q3 + factor * iqr
    mask = (series < low) | (series > high)
    stats = {
        "异常点数": int(mask.sum()),
        "异常比例": float(mask.mean()),
        "剔除前均值": float(series.mean()),
        "剔除后均值": float(series[~mask].mean()),
        "剔除前标准差": float(series.std(ddof=1)),
        "剔除后标准差": float(series[~mask].std(ddof=1)),
    }
    return mask, (float(low), float(high)), stats


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    mask, bounds, stats = solve(data["series"], float(data["factor"]))
    report("IQR 异常检测", 样本量=len(data["series"]), 下界=round(bounds[0], 3), 上界=round(bounds[1], 3),
           异常点数=stats["异常点数"], 异常比例=f"{stats['异常比例']:.1%}")
    save_table(__file__, "异常标记", {"序号": np.arange(1, len(mask) + 1),
                                      "数值": np.round(data["series"], 4),
                                      "是否异常": ["是" if m else "否" for m in mask]})
    save_table(__file__, "统计对照", {"指标": list(stats), "数值": [round(v, 6) for v in stats.values()]})
    plt = set_style()
    fig, ax = plt.subplots()
    ax.scatter(np.arange(1, len(mask) + 1), data["series"], s=16,
               c=["#D55E00" if m else "#0072B2" for m in mask])
    ax.axhline(bounds[0], color="#666666", ls="--", lw=0.9)
    ax.axhline(bounds[1], color="#666666", ls="--", lw=0.9)
    ax.set_xlabel("样本序号")
    ax.set_ylabel("数值")
    ax.set_title(f"IQR 检测：异常 {stats['异常点数']} 个")
    save_fig(__file__, fig, "iqr_outlier")
