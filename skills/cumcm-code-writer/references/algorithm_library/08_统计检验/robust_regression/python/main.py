"""稳健回归 · Huber M 估计（Python 最小可运行模板）

思路：用 Huber 损失替代最小二乘，降低异常点对系数的影响；与 OLS 对比看系数变化。
适用：数据含离群点或厚尾误差时；输出两种方法的系数与残差尺度对照。
接口：solve(X, y) -> (Huber 系数, OLS 系数, 对照表)；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import statsmodels.api as sm
from sklearn.linear_model import HuberRegressor

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_fig, save_table, set_style  # noqa: E402


def build_demo() -> dict:
    rng = np.random.default_rng(42)
    X = rng.normal(size=(200, 3))
    y = 1.0 + X @ np.array([2.0, -1.5, 0.8]) + rng.normal(scale=0.5, size=200)
    outliers = rng.choice(200, 12, replace=False)
    y[outliers] += rng.normal(loc=12, scale=3, size=12)   # 人为制造离群点
    return {"X": X, "y": y, "names": ["X1", "X2", "X3"]}


def solve(X, y):
    X, y = np.asarray(X, float), np.asarray(y, float)
    ols = sm.OLS(y, sm.add_constant(X)).fit()
    huber = HuberRegressor(epsilon=1.35, alpha=0.0, max_iter=500).fit(X, y)
    huber_coef = np.concatenate([[huber.intercept_], huber.coef_])
    residuals = y - (huber.intercept_ + X @ huber.coef_)
    return huber_coef, ols.params, residuals, ols


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    huber_coef, ols_coef, residuals, ols = solve(data["X"], data["y"])
    report("稳健回归", Huber系数=np.round(huber_coef, 4).tolist(), OLS系数=np.round(ols_coef, 4).tolist(),
           系数最大差异=round(float(np.abs(huber_coef - ols_coef).max()), 4))
    save_table(__file__, "系数对照", {"变量": ["常数"] + data["names"],
                                      "Huber": np.round(huber_coef, 6), "OLS": np.round(ols_coef, 6),
                                      "差异": np.round(huber_coef - ols_coef, 6)})
    plt = set_style()
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.0))
    axes[0].scatter(ols.fittedvalues, ols.resid, s=16, color="#0072B2", label="OLS 残差")
    axes[0].axhline(0, color="#666666", lw=0.9)
    axes[0].set_xlabel("拟合值")
    axes[0].set_ylabel("残差")
    axes[1].hist(ols.resid, bins=30, color="#56B4E9", edgecolor="white")
    axes[1].axvline(np.percentile(ols.resid, 2.5), color="#D55E00", ls="--", lw=0.9)
    axes[1].axvline(np.percentile(ols.resid, 97.5), color="#D55E00", ls="--", lw=0.9)
    axes[1].set_xlabel("残差")
    axes[1].set_ylabel("频数")
    save_fig(__file__, fig, "robust_regression")
