"""系统动力学（存量-流量）简化模型（Python 最小可运行模板）

模型：经典"人口-资源"存量流量系统
    存量：人口 P、资源存量 R；辅助变量：资源人均占有 R/P、拥挤度
    流量：出生率 = b·P·(1 - 拥挤度)、死亡率 = d·P·(1 + 资源紧缺度)
    方程：dP/dt = 出生 - 死亡，dR/dt = 再生 - 消耗
用欧拉法逐步积分（步长 Δt 可调），输出轨迹、峰值与稳态判断。
接口：solve(params, t_end, dt) -> (时间序列, 各存量轨迹, 指标)；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_fig, save_table, set_style  # noqa: E402


def build_demo() -> dict:
    return {"params": {"P0": 100.0, "R0": 1000.0, "b": 0.08, "d": 0.03,
                       "regen": 60.0, "consume": 0.6, "capacity": 400.0},
            "t_end": 120.0, "dt": 0.1}


def solve(params, t_end: float, dt: float):
    P, R = float(params["P0"]), float(params["R0"])
    b, d = float(params["b"]), float(params["d"])
    regen, consume, capacity = float(params["regen"]), float(params["consume"]), float(params["capacity"])
    steps = int(round(t_end / dt))
    t = np.arange(steps + 1) * dt
    population = np.zeros(steps + 1)
    resource = np.zeros(steps + 1)
    population[0], resource[0] = P, R
    for k in range(steps):
        crowding = min(1.0, P / capacity)                 # 拥挤度（0~1）
        scarcity = max(0.0, 1 - (R / max(P, 1e-9)) / 10)  # 资源紧缺度
        births = b * P * (1 - crowding)
        deaths = d * P * (1 + scarcity)
        regeneration = regen * (1 - R / (capacity * 10))
        consumption = consume * P
        P = max(0.0, P + (births - deaths) * dt)
        R = max(0.0, R + (regeneration - consumption) * dt)
        population[k + 1], resource[k + 1] = P, R
    peak_index = int(np.argmax(population))
    metrics = {
        "人口峰值": float(population.max()),
        "达峰时间": float(t[peak_index]),
        "末期人口": float(population[-1]),
        "末期资源": float(resource[-1]),
        "末20%人口变化率": float((population[-1] - population[int(steps * 0.8)]) / max(population[int(steps * 0.8)], 1e-9)),
    }
    return t, population, resource, metrics


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    t, population, resource, metrics = solve(data["params"], float(data["t_end"]), float(data["dt"]))
    steady = "趋于稳态" if abs(metrics["末20%人口变化率"]) < 0.05 else "仍在演化"
    report("系统动力学", 人口峰值=round(metrics["人口峰值"], 2), 达峰时间=round(metrics["达峰时间"], 2),
           末期人口=round(metrics["末期人口"], 2), 末期资源=round(metrics["末期资源"], 2), 状态=steady)
    save_table(__file__, "存量轨迹", {"时间": np.round(t, 3), "人口P": np.round(population, 4),
                                      "资源R": np.round(resource, 4),
                                      "人均资源": np.round(resource / np.maximum(population, 1e-9), 4)})
    save_table(__file__, "关键指标", {"指标": list(metrics), "数值": [round(v, 6) for v in metrics.values()]})
    plt = set_style()
    fig, axes = plt.subplots(1, 2, figsize=(7.6, 3.2))
    axes[0].plot(t, population, color="#0072B2", label="人口 P")
    axes[0].axvline(metrics["达峰时间"], color="#D55E00", ls=":", lw=0.9)
    axes[0].set_xlabel("时间")
    axes[0].set_ylabel("人口")
    axes[0].legend()
    axes[1].plot(t, resource, color="#009E73", label="资源存量 R")
    axes[1].plot(t, resource / np.maximum(population, 1e-9), color="#E69F00", label="人均资源")
    axes[1].set_xlabel("时间")
    axes[1].set_ylabel("资源")
    axes[1].legend()
    save_fig(__file__, fig, "system_dynamics")
