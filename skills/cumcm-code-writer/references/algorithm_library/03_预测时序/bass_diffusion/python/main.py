"""Bass 扩散模型（Python 最小可运行模板）

模型：dN/dt = (p + q N/m)(m - N)，N(t) = m [1 - e^{-(p+q)t}] / [1 + (q/p) e^{-(p+q)t}]
用途：新产品/新技术市场扩散预测；用网格搜索或最小二乘标定 p、q、m。
接口：solve(series, steps) -> (参数, 拟合值, 预测值)；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from scipy.optimize import curve_fit

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_fig, save_table, set_style  # noqa: E402


def build_demo() -> dict:
    p, q, m = 0.02, 0.35, 500.0
    t = np.arange(0, 20, dtype=float)
    cumulative = m * (1 - np.exp(-(p + q) * t)) / (1 + (q / p) * np.exp(-(p + q) * t))
    return {"series": cumulative, "steps": 8, "t": t}


def bass(t, p, q, m):
    return m * (1 - np.exp(-(p + q) * t)) / (1 + (q / p) * np.exp(-(p + q) * t))


def solve(t, series, steps: int = 8):
    t = np.asarray(t, float)
    series = np.asarray(series, float)
    (p, q, m), _ = curve_fit(bass, t, series, p0=[0.01, 0.3, series.max() * 1.2],
                             bounds=([1e-6, 1e-6, series.max()], [1, 5, series.max() * 50]),
                             maxfev=40000)
    fitted = bass(t, p, q, m)
    t_future = np.arange(t[-1] + 1, t[-1] + 1 + steps)
    forecast = bass(t_future, p, q, m)
    peak_time = float(np.log(q / p) / (p + q)) if q > p else float("nan")
    return (float(p), float(q), float(m)), fitted, t_future, forecast, peak_time


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    (p, q, m), fitted, t_future, forecast, peak_time = solve(data["t"], data["series"], int(data["steps"]))
    report("Bass 扩散", p=round(p, 4), q=round(q, 4), 市场潜力m=round(m, 1),
           拐点时刻=round(peak_time, 2), 预测末期=round(float(forecast[-1]), 1))
    save_table(__file__, "拟合与预测",
               {"时间": np.concatenate([data["t"], t_future]),
                "累计采纳": np.round(np.concatenate([fitted, forecast]), 3),
                "类型": ["拟合"] * len(fitted) + ["预测"] * len(forecast)})
    plt = set_style()
    fig, ax = plt.subplots()
    ax.scatter(data["t"], data["series"], s=22, color="#0072B2", label="观测")
    ax.plot(data["t"], fitted, color="#56B4E9", label="Bass 拟合")
    ax.plot(t_future, forecast, "--", color="#D55E00", label="预测")
    ax.axvline(peak_time, color="#666666", ls=":", lw=0.9)
    ax.annotate(f"拐点 t≈{peak_time:.1f}", xy=(peak_time, bass(peak_time, p, q, m) / 2),
                xytext=(peak_time + 1, m * 0.35), fontsize=8,
                arrowprops=dict(arrowstyle="->", color="#444444"))
    ax.set_xlabel("时间")
    ax.set_ylabel("累计采纳量")
    ax.legend()
    save_fig(__file__, fig, "bass_diffusion")
