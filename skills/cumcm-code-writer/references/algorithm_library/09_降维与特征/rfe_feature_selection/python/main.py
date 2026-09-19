"""递归特征消除 RFE（Python 最小可运行模板）

步骤：以交叉验证准确率为准则递归剔除最不重要特征，输出特征排名、最优子集与子集评分曲线。
接口：solve(X, y) -> (排名, 是否保留, 子集评分, 选择器)；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from sklearn.feature_selection import RFECV
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, train_test_split

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_fig, save_table, set_style  # noqa: E402


def build_demo() -> dict:
    rng = np.random.default_rng(42)
    X = rng.normal(size=(400, 8))
    score = 1.6 * X[:, 0] - 1.2 * X[:, 3] + 0.9 * X[:, 5] + rng.normal(scale=0.8, size=400)
    return {"X": X, "y": (score > 0).astype(int), "names": [f"特征{i + 1}" for i in range(8)]}


def solve(X, y, seed: int = 42):
    X, y = np.asarray(X, float), np.asarray(y)
    X_train, _, y_train, _ = train_test_split(X, y, test_size=0.3, random_state=seed, stratify=y)
    selector = RFECV(LogisticRegression(max_iter=2000), step=1,
                     cv=StratifiedKFold(5), scoring="accuracy", min_features_to_select=1)
    selector.fit(X_train, y_train)
    return selector.ranking_, selector.support_, selector.cv_results_["mean_test_score"], selector


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    ranking, support, scores, selector = solve(data["X"], data["y"])
    report("递归特征消除", 最优特征数=int(selector.n_features_),
           保留特征=[n for n, s in zip(data["names"], support) if s],
           交叉验证最优得分=round(float(scores.max()), 4))
    save_table(__file__, "特征排名", {"特征": data["names"], "排名": ranking,
                                      "是否保留": ["是" if s else "否" for s in support]})
    save_table(__file__, "子集评分", {"特征数": np.arange(1, len(scores) + 1), "交叉验证得分": np.round(scores, 6)})
    plt = set_style()
    fig, ax = plt.subplots()
    ax.plot(np.arange(1, len(scores) + 1), scores, "o-", color="#0072B2")
    ax.axvline(int(selector.n_features_), color="#D55E00", ls="--", lw=0.9)
    ax.set_xlabel("保留特征数")
    ax.set_ylabel("交叉验证准确率")
    save_fig(__file__, fig, "rfe_feature_selection")
