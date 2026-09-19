"""拉格朗日插值（Python 最小可运行模板）

模型：对给定节点构造拉格朗日基函数；节点不宜过多（高阶会出现龙格现象），输出插值对照与最大误差。
接口：solve(x_nodes, y_nodes, x_query) -> (插值值, 基函数矩阵)；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_fig, save_table, set_style  # noqa: E402


def build_demo() -> dict:
    x_nodes = np.linspace(0, 10, 7)
    y_nodes = np.sin(x_nodes) + 0.1 * x_nodes
    return {"x_nodes": x_nodes, "y_nodes": y_nodes, "x_query": np.linspace(0, 10, 101)}


def lagrange_basis(x_nodes, x_query):
    basis = np.ones((len(x_query), len(x_nodes)))
    for i, xi in enumerate(x_nodes):
        for j, xj in enumerate(x_nodes):
            if i != j:
                basis[:, i] *= (x_query - xj) / (xi - xj)
    return basis


def solve(x_nodes, y_nodes, x_query):
    x_nodes, y_nodes, x_query = map(lambda a: np.asarray(a, float), (x_nodes, y_nodes, x_query))
    basis = lagrange_basis(x_nodes, x_query)
    values = basis @ y_nodes
    dense = np.sin(x_query) + 0.1 * x_query
    error = float(np.abs(values - dense).max())
    return values, basis, error, dense


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    values, basis, error, dense = solve(data["x_nodes"], data["y_nodes"], data["x_query"])
    report("拉格朗日插值", 节点数=len(data["x_nodes"]), 最大误差=f"{error:.3e}",
           插值区间=f"{data['x_query'][0]:.1f}~{data['x_query'][-1]:.1f}")
    save_table(__file__, "插值结果", {"x": np.round(data["x_query"], 4), "插值值": np.round(values, 6),
                                      "真值": np.round(dense, 6),
                                      "绝对误差": np.round(np.abs(values - dense), 8)})
    plt = set_style()
    fig, ax = plt.subplots()
    ax.plot(data["x_query"], dense, color="#999999", label="真值")
    ax.plot(data["x_query"], values, "--", color="#0072B2", label="拉格朗日插值")
    ax.scatter(data["x_nodes"], data["y_nodes"], color="#D55E00", s=24, zorder=3, label="插值节点")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.legend()
    save_fig(__file__, fig, "lagrange_interpolation")
