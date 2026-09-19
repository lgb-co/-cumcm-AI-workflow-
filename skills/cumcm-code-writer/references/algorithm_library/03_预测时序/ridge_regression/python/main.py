"""岭回归 · 共线性下的正则化回归（Python 最小可运行模板）

模型：min ||y - Xβ||² + λ||β||²；用 K 折交叉验证选 λ，报告系数与验证误差。
接口：solve(X, y, alphas) -> (最优 λ, 系数, 交叉验证曲线)；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from sklearn.linear_model import Ridge
from sklearn.model_selection import KFold, cross_val_score

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_table  # noqa: E402


def build_demo() -> dict:
    rng = np.random.default_rng(42)
    X = rng.normal(size=(80, 4))
    X[:, 3] = X[:, 0] * 0.95 + rng.normal(scale=0.1, size=80)  # 制造共线性
    y = 1.5 + X @ np.array([1.0, -0.6, 0.4, 0.8]) + rng.normal(scale=0.4, size=80)
    return {"X": X, "y": y, "alphas": np.logspace(-3, 2, 30).tolist()}


def solve(X, y, alphas, seed: int = 42):
    X = np.asarray(X, float)
    y = np.asarray(y, float)
    cv = KFold(n_splits=5, shuffle=True, random_state=seed)
    scores = [cross_val_score(Ridge(alpha=a), X, y, cv=cv, scoring="neg_root_mean_squared_error").mean()
              for a in alphas]
    scores = -np.asarray(scores)
    best_alpha = float(alphas[int(np.argmin(scores))])
    model = Ridge(alpha=best_alpha).fit(X, y)
    return best_alpha, model.coef_, model.intercept_, scores


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    best_alpha, coef, intercept, scores = solve(data["X"], data["y"], data["alphas"])
    report("岭回归", 最优lambda=best_alpha, 截距=round(float(intercept), 4),
           系数=np.round(coef, 4).tolist(), 交叉验证RMSE=f"{scores.min():.4f}")
    save_table(__file__, "正则化路径", {"lambda": data["alphas"], "交叉验证RMSE": np.round(scores, 6)})
