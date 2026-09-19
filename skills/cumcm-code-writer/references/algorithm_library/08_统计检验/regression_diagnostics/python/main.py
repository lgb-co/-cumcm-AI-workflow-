"""回归诊断（Python 最小可运行模板）

检查：残差正态性（Shapiro）、异方差（Breusch-Pagan）、多重共线性（VIF）、异常点（Cook 距离）。
接口：solve(X, y) -> (诊断指标字典)；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import statsmodels.api as sm
from scipy import stats
from statsmodels.stats.diagnostic import het_breuschpagan
from statsmodels.stats.outliers_influence import variance_inflation_factor

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_fig, save_table, set_style  # noqa: E402


def build_demo() -> dict:
    rng = np.random.default_rng(42)
    X = rng.normal(size=(120, 3))
    X[:, 2] = 0.85 * X[:, 0] + rng.normal(scale=0.3, size=120)  # 制造共线性
    y = 1.0 + X @ np.array([1.5, -0.9, 0.6]) + rng.normal(scale=1.0, size=120)
    return {"X": X, "y": y, "names": ["X1", "X2", "X3"]}


def solve(X, y, names):
    X, y = np.asarray(X, float), np.asarray(y, float)
    design = sm.add_constant(X)
    model = sm.OLS(y, design).fit()
    residuals = model.resid
    shapiro_p = float(stats.shapiro(residuals).pvalue)
    bp = het_breuschpagan(residuals, design)
    vif = [float(variance_inflation_factor(design, i)) for i in range(1, design.shape[1])]
    cooks = model.get_influence().cooks_distance[0]
    metrics = {
        "R²": float(model.rsquared),
        "调整R²": float(model.rsquared_adj),
        "残差正态性p": shapiro_p,
        "异方差BP_p": float(bp[1]),
        "最大VIF": float(max(vif)),
        "Cook距离>4/n 的样本数": int((cooks > 4 / len(y)).sum()),
    }
    return metrics, model, vif, residuals, np.asarray(cooks)


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    metrics, model, vif, residuals, cooks = solve(data["X"], data["y"], data["names"])
    report("回归诊断", R2=round(metrics["R²"], 4), 残差正态性p=round(metrics["残差正态性p"], 4),
           异方差p=round(metrics["异方差BP_p"], 4), 最大VIF=round(metrics["最大VIF"], 3),
           异常点数=metrics["Cook距离>4/n 的样本数"])
    save_table(__file__, "系数与检验", {"变量": ["常数"] + data["names"],
                                        "系数": np.round(model.params, 6),
                                        "标准误": np.round(model.bse, 6),
                                        "t值": np.round(model.tvalues, 4),
                                        "p值": np.round(model.pvalues, 6)})
    save_table(__file__, "共线性诊断", {"变量": data["names"], "VIF": np.round(vif, 4)})
    plt = set_style()
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.0))
    axes[0].scatter(model.fittedvalues, residuals, s=16, color="#0072B2")
    axes[0].axhline(0, color="#D55E00", lw=0.9)
    axes[0].set_xlabel("拟合值")
    axes[0].set_ylabel("残差")
    axes[0].set_title("残差-拟合图")
    axes[1].stem(np.arange(1, len(cooks) + 1), cooks, basefmt=" ")
    axes[1].axhline(4 / len(cooks), color="#D55E00", ls="--", lw=0.9)
    axes[1].set_xlabel("样本序号")
    axes[1].set_ylabel("Cook 距离")
    save_fig(__file__, fig, "regression_diagnostics")
