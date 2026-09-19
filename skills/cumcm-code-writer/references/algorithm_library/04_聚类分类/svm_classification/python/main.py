"""支持向量机分类（Python 最小可运行模板）

步骤：标准化 → 在 RBF 核上网格搜索 (C, gamma) → 输出准确率、支持向量占比与混淆矩阵。
接口：solve(X, y) -> (准确率, 最优参数, 支持向量占比, 混淆矩阵)；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_table  # noqa: E402


def build_demo() -> dict:
    rng = np.random.default_rng(42)
    X = np.vstack([rng.normal(loc=[-1.5, -1.5], scale=1.0, size=(90, 2)),
                   rng.normal(loc=[1.5, 1.5], scale=1.0, size=(90, 2))])
    return {"X": X, "y": np.repeat([0, 1], 90)}


def solve(X, y, seed: int = 42):
    X, y = np.asarray(X, float), np.asarray(y)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=seed, stratify=y)
    scaler = StandardScaler().fit(X_train)
    grid = GridSearchCV(SVC(kernel="rbf"), {"C": [0.1, 1, 10], "gamma": ["scale", 0.1, 1]}, cv=5)
    grid.fit(scaler.transform(X_train), y_train)
    model = grid.best_estimator_
    pred = model.predict(scaler.transform(X_test))
    return (float(accuracy_score(y_test, pred)), grid.best_params_,
            len(model.support_) / len(X_train), confusion_matrix(y_test, pred))


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    acc, params, ratio, cm = solve(data["X"], data["y"])
    report("SVM 分类", 测试准确率=round(acc, 4), 最优参数=str(params), 支持向量占比=round(ratio, 4))
    save_table(__file__, "混淆矩阵", {"真实类别": np.repeat(np.arange(cm.shape[0]), cm.shape[1]),
                                      "预测类别": np.tile(np.arange(cm.shape[1]), cm.shape[0]),
                                      "样本数": cm.ravel()})
