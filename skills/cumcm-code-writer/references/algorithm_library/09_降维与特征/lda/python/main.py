"""线性判别分析 LDA（Python 最小可运行模板）

用途：有监督降维与分类；输出判别系数、降维投影与交叉验证准确率。
接口：solve(X, y) -> (投影, 准确率, 判别系数)；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_fig, save_table, set_style  # noqa: E402


def build_demo() -> dict:
    rng = np.random.default_rng(42)
    X = np.vstack([rng.normal(loc=[0, 0, 0], scale=1.0, size=(90, 3)),
                   rng.normal(loc=[2.2, 1.6, 0.8], scale=1.0, size=(90, 3))])
    return {"X": X, "y": np.repeat([0, 1], 90), "names": ["X1", "X2", "X3"]}


def solve(X, y):
    X, y = np.asarray(X, float), np.asarray(y)
    Xs = StandardScaler().fit_transform(X)
    model = LinearDiscriminantAnalysis(n_components=1).fit(Xs, y)
    projection = model.transform(Xs)
    accuracy = float(cross_val_score(LinearDiscriminantAnalysis(), Xs, y, cv=5).mean())
    return projection, accuracy, model.coef_[0]


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    projection, accuracy, coefficients = solve(data["X"], data["y"])
    report("线性判别分析", 交叉验证准确率=round(accuracy, 4),
           判别系数=np.round(coefficients, 4).tolist(), 样本数=len(projection))
    save_table(__file__, "判别系数", {"变量": data["names"], "系数": np.round(coefficients, 6)})
    save_table(__file__, "投影结果", {"样本": np.arange(1, len(projection) + 1),
                                      "投影值": np.round(projection[:, 0], 6), "类别": data["y"]})
    plt = set_style()
    fig, ax = plt.subplots()
    for label, color in zip(sorted(set(data["y"])), ["#0072B2", "#D55E00"]):
        mask = np.asarray(data["y"]) == label
        ax.hist(projection[mask, 0], bins=25, alpha=0.65, color=color, label=f"类别 {label + 1}")
    ax.set_xlabel("第一判别方向投影值")
    ax.set_ylabel("频数")
    ax.legend()
    save_fig(__file__, fig, "lda")
