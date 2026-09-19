"""三次样条插值（Python 最小可运行模板）

模型：分段三次多项式，二阶连续可导；默认自然边界条件；与拉格朗日插值对比高阶插值的稳定性。
接口：solve(x_nodes, y_nodes, x_query) -> (样条值, 拉格朗日值, 误差对照)；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from scipy.interpolate import CubicSpline

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_fig, save_table, set_style  # noqa: E402


def build_demo() -> dict:
    x_nodes = np.linspace(0, 10, 11)
    y_nodes = np.sin(x_nodes) + 0.1 * x_nodes
    return {"x_nodes": x_nodes, "y_nodes": y_nodes, "x_query": np.linspace(0, 10, 201)}


def lagrange(x_nodes, y_nodes, x_query):
    result = np.zeros_like(x_query)
    for i in range(len(x_nodes)):
        basis = np.ones_like(x_query)
        for j in range(len(x_nodes)):
            if i != j:
                basis *= (x_query - x_nodes[j]) / (x_nodes[i] - x_nodes[j])
        result += basis * y_nodes[i]
    return result


def solve(x_nodes, y_nodes, x_query):
    x_nodes, y_nodes, x_query = map(lambda a: np.asarray(a, float), (x_nodes, y_nodes, x_query))
    spline = CubicSpline(x_nodes, y_nodes, bc_type="natural")
    spline_values = spline(x_query)
    lagrange_values = lagrange(x_nodes, y_nodes, x_query)
    true = np.sin(x_query) + 0.1 * x_query
    return spline_values, lagrange_values, true, float(np.abs(spline_values - true).max()), \
        float(np.abs(lagrange_values - true).max())


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    spline_values, lagrange_values, true, spline_error, lagrange_error = solve(
        data["x_nodes"], data["y_nodes"], data["x_query"])
    report("三次样条插值", 节点数=len(data["x_nodes"]), 样条最大误差=f"{spline_error:.3e}",
           拉格朗日最大误差=f"{lagrange_error:.3e}")
    save_table(__file__, "插值对照", {"x": np.round(data["x_query"], 4),
                                      "真值": np.round(true, 6),
                                      "三次样条": np.round(spline_values, 6),
                                      "拉格朗日": np.round(lagrange_values, 6)})
    plt = set_style()
    fig, axes = plt.subplots(1, 2, figsize=(7.6, 3.2))
    axes[0].plot(data["x_query"], true, color="#999999", label="真值")
    axes[0].plot(data["x_query"], spline_values, "--", color="#0072B2", label="三次样条")
    axes[0].plot(data["x_query"], lagrange_values, ":", color="#D55E00", label="拉格朗日")
    axes[0].scatter(data["x_nodes"], data["y_nodes"], s=20, color="#009E73", zorder=3)
    axes[0].set_xlabel("x")
    axes[0].set_ylabel("y")
    axes[0].legend()
    axes[1].semilogy(data["x_query"], np.abs(spline_values - true) + 1e-16, color="#0072B2", label="三次样条")
    axes[1].semilogy(data["x_query"], np.abs(lagrange_values - true) + 1e-16, color="#D55E00", label="拉格朗日")
    axes[1].set_xlabel("x")
    axes[1].set_ylabel("绝对误差（对数轴）")
    axes[1].legend()
    save_fig(__file__, fig, "cubic_spline_interpolation")
