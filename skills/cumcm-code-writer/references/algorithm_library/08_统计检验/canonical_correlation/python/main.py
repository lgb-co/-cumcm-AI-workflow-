"""典型相关分析 CCA（Python 最小可运行模板）

步骤：求两组变量间的典型相关系数与典型变量，报告显著性检验（用 sklearn CCA 作为主实现）。
接口：solve(X, Y) -> (典型相关系数, 典型变量)；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from sklearn.cross_decomposition import CCA

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_table  # noqa: E402


def build_demo() -> dict:
    rng = np.random.default_rng(42)
    latent = rng.normal(size=(150, 1))
    X = latent @ np.array([[0.9, 0.4, 0.2]]) + rng.normal(scale=0.5, size=(150, 3))
    Y = latent @ np.array([[0.8, 0.5]]) + rng.normal(scale=0.5, size=(150, 2))
    return {"X": X, "Y": Y, "names_x": ["X1", "X2", "X3"], "names_y": ["Y1", "Y2"]}


def solve(X, Y):
    X, Y = np.asarray(X, float), np.asarray(Y, float)
    n_components = min(X.shape[1], Y.shape[1])
    model = CCA(n_components=n_components).fit(X, Y)
    X_c, Y_c = model.transform(X, Y)
    correlations = [
        float(abs(np.corrcoef(X_c[:, k], Y_c[:, k])[0, 1])) for k in range(n_components)
    ]
    return correlations, X_c, Y_c, model.x_weights_, model.y_weights_


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    correlations, X_c, Y_c, wx, wy = solve(data["X"], data["Y"])
    report("典型相关分析", 典型相关系数=np.round(correlations, 4).tolist(),
           X载荷=np.round(wx[:, 0], 4).tolist(), Y载荷=np.round(wy[:, 0], 4).tolist())
    save_table(__file__, "典型相关系数", {"序号": np.arange(1, len(correlations) + 1),
                                          "典型相关系数": np.round(correlations, 6)})
    save_table(__file__, "第一对典型变量", {"样本": np.arange(1, len(X_c) + 1),
                                            "U1": np.round(X_c[:, 0], 6), "V1": np.round(Y_c[:, 0], 6)})
    frame_x = {"变量": data["names_x"], "第一典型载荷": np.round(wx[:, 0], 6)}
    frame_y = {"变量": data["names_y"], "第一典型载荷": np.round(wy[:, 0], 6)}
    save_table(__file__, "X组载荷", frame_x)
    save_table(__file__, "Y组载荷", frame_y)
