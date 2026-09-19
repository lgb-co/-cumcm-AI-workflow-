"""DBSCAN 密度聚类（Python 最小可运行模板）

步骤：用 k-距离图的拐点估计 eps，再按 eps 与 min_samples 识别核心点、边界点与噪声点。
接口：solve(X, min_samples, eps) -> (标签, 簇数, 噪声数, eps)；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.metrics import silhouette_score
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_table  # noqa: E402


def build_demo() -> dict:
    rng = np.random.default_rng(42)
    X = np.vstack([
        rng.normal(loc=[0, 0], scale=0.5, size=(70, 2)),
        rng.normal(loc=[4, 4], scale=0.6, size=(60, 2)),
        rng.uniform(-6, 6, size=(10, 2)),
    ])
    return {"X": X, "min_samples": 5}


def suggest_eps(X, k: int = 5) -> float:
    """按第 k 近邻距离的拐点估计 eps（k-距离图法）。"""
    distances, _ = NearestNeighbors(n_neighbors=k).fit(X).kneighbors(X)
    kth = np.sort(distances[:, -1])
    gradient = np.gradient(kth)
    return float(kth[int(np.argmax(gradient))])


def solve(X, min_samples: int, eps: float | None = None):
    X = StandardScaler().fit_transform(np.asarray(X, float))
    eps = suggest_eps(X) if eps is None else eps
    labels = DBSCAN(eps=eps, min_samples=min_samples).fit(X).labels_
    clusters = len(set(labels)) - (1 if -1 in labels else 0)
    noise = int((labels == -1).sum())
    score = float(silhouette_score(X, labels)) if clusters > 1 else float("nan")
    return labels, clusters, noise, float(eps), score


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    labels, clusters, noise, eps, score = solve(data["X"], int(data["min_samples"]))
    report("DBSCAN", eps=round(eps, 4), 簇数=clusters, 噪声点=noise, 轮廓系数=round(score, 4))
    save_table(__file__, "聚类结果", {"样本": np.arange(1, len(labels) + 1), "标签": labels,
                                      "X1": np.round(data["X"][:, 0], 4), "X2": np.round(data["X"][:, 1], 4)})
