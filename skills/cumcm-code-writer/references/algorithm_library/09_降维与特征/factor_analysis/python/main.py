"""因子分析（Python 最小可运行模板）

步骤：相关矩阵 Bartlett 球形检验与 KMO 取样适当性 → 主成分法提取因子 → Varimax 旋转 →
输出旋转后载荷、共同度与因子得分（不依赖第三方因子分析库，避免额外安装）。
接口：solve(X, n_factors) -> (载荷, 得分, 共同度, Bartlett p, KMO)；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from scipy import stats
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_table  # noqa: E402


def build_demo() -> dict:
    rng = np.random.default_rng(42)
    f1, f2 = rng.normal(size=300), rng.normal(size=300)
    X = np.column_stack([
        0.9 * f1 + rng.normal(scale=0.4, size=300),
        0.8 * f1 + rng.normal(scale=0.4, size=300),
        0.85 * f2 + rng.normal(scale=0.4, size=300),
        0.7 * f2 + rng.normal(scale=0.4, size=300),
        rng.normal(size=300),
    ])
    return {"X": X, "names": [f"指标{i + 1}" for i in range(5)], "n_factors": 2}


def varimax(loadings, gamma: float = 1.0, max_iter: int = 100, tol: float = 1e-6):
    p, k = loadings.shape
    rotation = np.eye(k)
    objective = 0.0
    for _ in range(max_iter):
        previous = objective
        rotated = loadings @ rotation
        u, s, vt = np.linalg.svd(
            loadings.T @ (rotated ** 3 - (gamma / p) * rotated @ np.diag(np.diag(rotated.T @ rotated)))
        )
        rotation = u @ vt
        objective = float(s.sum())
        if previous != 0 and objective / previous < 1 + tol:
            break
    return loadings @ rotation


def solve(X, names, n_factors: int = 2):
    X = np.asarray(X, float)
    Xs = StandardScaler().fit_transform(X)
    n, p = Xs.shape
    corr = np.corrcoef(Xs, rowvar=False)
    chi2 = -(n - 1 - (2 * p + 5) / 6) * np.log(np.linalg.det(corr))
    bartlett_p = float(1 - stats.chi2.cdf(chi2, p * (p - 1) / 2))
    inv_corr = np.linalg.pinv(corr)
    d = np.sqrt(np.outer(np.diag(inv_corr), np.diag(inv_corr)))
    partial = -inv_corr / d
    np.fill_diagonal(partial, 0.0)
    off = corr - np.eye(p)
    kmo = float((off ** 2).sum() / ((off ** 2).sum() + (partial ** 2).sum()))

    pca = PCA(n_components=n_factors).fit(Xs)
    loadings = pca.components_.T * np.sqrt(pca.explained_variance_)
    rotated = varimax(loadings)
    communality = (rotated ** 2).sum(axis=1)
    scores = pca.transform(Xs)
    return rotated, scores, communality, bartlett_p, kmo


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    loadings, scores, communality, bartlett_p, kmo = solve(data["X"], data["names"], int(data["n_factors"]))
    report("因子分析", KMO=round(kmo, 4), Bartlett_p=f"{bartlett_p:.3e}", 因子数=int(data["n_factors"]),
           共同度=np.round(communality, 4).tolist())
    save_table(__file__, "因子载荷", {"指标": data["names"],
                                      **{f"因子{i + 1}": np.round(loadings[:, i], 6)
                                         for i in range(loadings.shape[1])},
                                      "共同度": np.round(communality, 6)})
    save_table(__file__, "因子得分", {"样本": np.arange(1, 101),
                                      **{f"因子{i + 1}": np.round(scores[:100, i], 6)
                                         for i in range(scores.shape[1])}})
