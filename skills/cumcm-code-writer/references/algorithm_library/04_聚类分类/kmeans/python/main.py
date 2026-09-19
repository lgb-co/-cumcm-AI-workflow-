"""K-means 聚类（Python 最小可运行模板）

步骤：先用肘部法（SSE）与轮廓系数选 K，再输出簇标签、簇中心与轮廓系数。
接口：solve(X, k_range) -> (最优 K, 标签, 中心, 轮廓系数)；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_table  # noqa: E402


def build_demo() -> dict:
    rng = np.random.default_rng(42)
    centers = np.array([[0, 0], [5, 5], [-4, 4]])
    X = np.vstack([c + rng.normal(scale=0.8, size=(60, 2)) for c in centers])
    return {"X": X, "k_range": [2, 3, 4, 5, 6]}


def solve(X, k_range, seed: int = 42):
    X = np.asarray(X, float)
    Xs = StandardScaler().fit_transform(X)
    records, best = [], None
    for k in k_range:
        model = KMeans(n_clusters=k, n_init=20, random_state=seed).fit(Xs)
        score = float(silhouette_score(Xs, model.labels_))
        records.append((k, float(model.inertia_), score))
        if best is None or score > best[3]:
            best = (k, model.labels_, model.cluster_centers_, score)
    return best, records


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    (best_k, labels, centers, score), records = solve(data["X"], data["k_range"])
    report("K-means", 最优K=best_k, 轮廓系数=round(score, 4), 样本数=len(labels))
    save_table(__file__, "K值选择", {"K": [r[0] for r in records], "SSE": np.round([r[1] for r in records], 4),
                                     "轮廓系数": np.round([r[2] for r in records], 6)})
    save_table(__file__, "聚类结果", {"样本": np.arange(1, len(labels) + 1), "簇标签": labels,
                                      "X1": np.round(data["X"][:, 0], 4), "X2": np.round(data["X"][:, 1], 4)})
    save_table(__file__, "簇中心", {"簇": np.arange(1, best_k + 1),
                                    "中心1": np.round(centers[:, 0], 6), "中心2": np.round(centers[:, 1], 6)})
