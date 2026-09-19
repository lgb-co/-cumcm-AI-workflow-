"""归一化与标准化（Python 最小可运行模板）

内容：Min-Max 归一化、Z-Score 标准化、正向/负向指标同向化；输出变换后数据与参数（用于反变换）。
接口：solve(X, positive) -> (标准化矩阵, 参数)；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_table  # noqa: E402


def build_demo() -> dict:
    rng = np.random.default_rng(42)
    X = np.column_stack([
        rng.normal(loc=100, scale=15, size=50),
        rng.normal(loc=0.6, scale=0.1, size=50),
        rng.uniform(1, 10, size=50),
    ])
    return {"X": X, "positive": [True, True, False]}


def solve(X, positive):
    X = np.asarray(X, float)
    direction = np.asarray([1.0 if p else -1.0 for p in positive])
    oriented = X * direction
    minmax = (oriented - oriented.min(axis=0)) / (oriented.max(axis=0) - oriented.min(axis=0))
    zscore = (oriented - oriented.mean(axis=0)) / oriented.std(axis=0, ddof=1)
    params = {
        "min": oriented.min(axis=0).tolist(),
        "max": oriented.max(axis=0).tolist(),
        "mean": oriented.mean(axis=0).tolist(),
        "std": oriented.std(axis=0, ddof=1).tolist(),
        "direction": direction.tolist(),
    }
    return minmax, zscore, params, oriented


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    minmax, zscore, params, oriented = solve(data["X"], data["positive"])
    report("归一化与标准化", 样本数=len(data["X"]), 指标数=data["X"].shape[1],
           同向化后均值=np.round(oriented.mean(axis=0), 4).tolist())
    save_table(__file__, "MinMax归一化", {f"X{i + 1}": np.round(minmax[:, i], 6)
                                          for i in range(minmax.shape[1])})
    save_table(__file__, "ZScore标准化", {f"X{i + 1}": np.round(zscore[:, i], 6)
                                          for i in range(zscore.shape[1])})
    save_table(__file__, "变换参数", {"指标": [f"X{i + 1}" for i in range(len(params["min"]))],
                                      "方向": params["direction"], "最小值": params["min"],
                                      "最大值": params["max"], "均值": params["mean"], "标准差": params["std"]})
