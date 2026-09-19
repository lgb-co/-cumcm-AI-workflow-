"""层次聚类（Python 最小可运行模板）

步骤：Ward 连接法自底向上合并 → 输出聚类树合并距离与指定簇数下的标签。
接口：solve(X, n_clusters) -> (标签, 合并距离矩阵, 轮廓系数)；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from scipy.cluster.hierarchy import fcluster, linkage
from sklearn.metrics import silhouette_score

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_table  # noqa: E402


def build_demo() -> dict:
    rng = np.random.default_rng(42)
    centers = np.array([[0, 0], [6, 6], [-5, 5]])
    X = np.vstack([c + rng.normal(scale=0.7, size=(40, 2)) for c in centers])
    return {"X": X, "n_clusters": 3}


def solve(X, n_clusters: int, method: str = "ward"):
    X = np.asarray(X, float)
    Z = linkage(X, method=method)
    labels = fcluster(Z, t=n_clusters, criterion="maxclust")
    score = float(silhouette_score(X, labels)) if len(set(labels)) > 1 else float("nan")
    return labels, Z, score


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    labels, Z, score = solve(data["X"], int(data["n_clusters"]))
    report("层次聚类", 簇数=int(data["n_clusters"]), 轮廓系数=round(score, 4), 样本数=len(labels))
    save_table(__file__, "聚类结果", {"样本": np.arange(1, len(labels) + 1), "簇标签": labels,
                                      "X1": np.round(data["X"][:, 0], 4), "X2": np.round(data["X"][:, 1], 4)})
    save_table(__file__, "合并过程", {"步骤": np.arange(1, len(Z) + 1), "合并距离": np.round(Z[:, 2], 6)})
