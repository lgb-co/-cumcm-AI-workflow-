"""高斯混合模型 GMM 软聚类（Python 最小可运行模板）

步骤：按 BIC 选择簇数 → EM 估计均值/协方差/权重 → 输出后验概率与硬标签。
接口：solve(X, k_range) -> (最优 K, BIC, 标签, 后验概率, 均值)；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_table  # noqa: E402


def build_demo() -> dict:
    rng = np.random.default_rng(42)
    X = np.vstack([rng.normal(loc=[0, 0], scale=[0.6, 1.2], size=(80, 2)),
                   rng.normal(loc=[4, 3], scale=[1.0, 0.5], size=(70, 2))])
    return {"X": X, "k_range": [2, 3, 4]}


def solve(X, k_range, seed: int = 42):
    Xs = StandardScaler().fit_transform(np.asarray(X, float))
    records, best = [], None
    for k in k_range:
        model = GaussianMixture(n_components=k, covariance_type="full", random_state=seed, n_init=5).fit(Xs)
        records.append((k, float(model.bic(Xs)), float(model.aic(Xs))))
        if best is None or records[-1][1] < best[1]:
            best = (k, records[-1][1], model.predict(Xs), model.predict_proba(Xs), model.means_)
    return best, records


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    (best_k, bic, labels, proba, means), records = solve(data["X"], data["k_range"])
    report("高斯混合", 最优K=best_k, BIC=round(bic, 3),
           最大后验概率均值=round(float(proba.max(1).mean()), 4))
    save_table(__file__, "模型选择", {"K": [r[0] for r in records], "BIC": np.round([r[1] for r in records], 4),
                                      "AIC": np.round([r[2] for r in records], 4)})
    table = {"样本": np.arange(1, len(labels) + 1), "硬标签": labels}
    for j in range(best_k):
        table[f"后验P{j + 1}"] = np.round(proba[:, j], 4)
    save_table(__file__, "聚类结果", table)
