"""主成分分析 PCA（Python 最小可运行模板）

步骤：标准化 → 特征分解 → 方差贡献率与累计贡献率 → 取累计 ≥85% 的主成分 → 输出得分与载荷。
接口：solve(X, threshold) -> (得分, 载荷, 贡献率, 累计贡献率, 保留个数)；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_fig, save_table, set_style  # noqa: E402


def build_demo() -> dict:
    rng = np.random.default_rng(42)
    latent = rng.normal(size=(200, 2))
    X = latent @ np.array([[0.9, 0.4, 0.2, 0.1, 0.0], [0.1, 0.5, 0.8, 0.3, 0.2]])
    X = X + rng.normal(scale=0.4, size=X.shape)
    return {"X": X, "names": [f"指标{i + 1}" for i in range(X.shape[1])], "threshold": 0.85}


def solve(X, threshold: float = 0.85):
    X = np.asarray(X, float)
    Xs = StandardScaler().fit_transform(X)
    model = PCA().fit(Xs)
    ratio = model.explained_variance_ratio_
    cumulative = np.cumsum(ratio)
    kept = int(np.searchsorted(cumulative, threshold) + 1)
    return model.transform(Xs)[:, :kept], model.components_[:kept], ratio, cumulative, kept


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    scores, loadings, ratio, cumulative, kept = solve(data["X"], float(data["threshold"]))
    report("主成分分析", 保留主成分数=kept, 累计贡献率=round(float(cumulative[kept - 1]), 4),
           各主成分贡献率=np.round(ratio[:kept], 4).tolist())
    save_table(__file__, "方差贡献率", {"主成分": [f"PC{i + 1}" for i in range(len(ratio))],
                                        "贡献率": np.round(ratio, 6), "累计贡献率": np.round(cumulative, 6)})
    save_table(__file__, "载荷矩阵", {"指标": data["names"],
                                      **{f"PC{i + 1}": np.round(loadings[i], 6) for i in range(kept)}})
    save_table(__file__, "主成分得分", {f"PC{i + 1}": np.round(scores[:100, i], 6) for i in range(kept)})
    plt = set_style()
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.0))
    axes[0].bar(np.arange(1, len(ratio) + 1), ratio, color="#56B4E9", label="贡献率")
    axes[0].plot(np.arange(1, len(ratio) + 1), cumulative, "o-", color="#D55E00", label="累计贡献率")
    axes[0].axhline(float(data["threshold"]), ls=":", color="#666666")
    axes[0].set_xlabel("主成分")
    axes[0].set_ylabel("方差贡献率")
    axes[0].legend()
    axes[1].scatter(scores[:, 0], scores[:, 1] if kept > 1 else np.zeros(len(scores)), s=14, color="#0072B2")
    axes[1].set_xlabel("PC1 得分")
    axes[1].set_ylabel("PC2 得分")
    save_fig(__file__, fig, "pca")
