"""AdaBoost 集成分类（Python 最小可运行模板）

思路：串行训练弱分类器（深度 1 的决策树桩），每次提高错分样本权重，按加权投票输出。
输出准确率、弱学习器数量与各轮训练误差曲线，便于判断是否早停。
接口：solve(X, y, n_estimators) -> (准确率, 训练误差曲线)；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from sklearn.ensemble import AdaBoostClassifier
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_fig, save_table, set_style  # noqa: E402


def build_demo() -> dict:
    rng = np.random.default_rng(42)
    X = rng.normal(size=(400, 5))
    score = 1.4 * X[:, 0] - 1.1 * X[:, 1] + 0.9 * X[:, 2] * X[:, 3] + rng.normal(scale=0.6, size=400)
    return {"X": X, "y": (score > 0).astype(int), "n_estimators": 200}


def solve(X, y, n_estimators: int = 200, seed: int = 42):
    X, y = np.asarray(X, float), np.asarray(y)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=seed, stratify=y)
    model = AdaBoostClassifier(
        estimator=DecisionTreeClassifier(max_depth=1, random_state=seed),
        n_estimators=n_estimators, learning_rate=0.5, random_state=seed,
    )
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    staged = np.array([accuracy_score(y_train, p) for p in model.staged_predict(X_train)])
    return float(accuracy_score(y_test, pred)), confusion_matrix(y_test, pred), staged, model


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    accuracy, cm, staged, model = solve(data["X"], data["y"], int(data["n_estimators"]))
    report("AdaBoost", 测试准确率=round(accuracy, 4), 弱学习器数=len(model.estimators_),
           训练集末轮准确率=round(float(staged[-1]), 4))
    save_table(__file__, "训练误差曲线", {"轮次": np.arange(1, len(staged) + 1), "训练准确率": np.round(staged, 6)})
    save_table(__file__, "混淆矩阵", {"真实类别": np.repeat(np.arange(cm.shape[0]), cm.shape[1]),
                                      "预测类别": np.tile(np.arange(cm.shape[1]), cm.shape[0]),
                                      "样本数": cm.ravel()})
    plt = set_style()
    fig, ax = plt.subplots()
    ax.plot(staged, color="#0072B2")
    ax.set_xlabel("弱学习器轮次")
    ax.set_ylabel("训练集准确率")
    ax.set_title("AdaBoost 训练过程")
    save_fig(__file__, fig, "adaboost_classification")
