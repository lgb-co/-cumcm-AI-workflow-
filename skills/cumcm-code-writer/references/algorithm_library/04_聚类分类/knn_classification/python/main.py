"""KNN 分类（Python 最小可运行模板）

步骤：标准化特征 → 交叉验证选 K → 输出测试集准确率与混淆矩阵。
接口：solve(X, y, k_range) -> (最优 K, 准确率, 混淆矩阵, 各 K 得分)；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_table  # noqa: E402


def build_demo() -> dict:
    rng = np.random.default_rng(42)
    X = np.vstack([rng.normal(loc=[0, 0], scale=0.9, size=(80, 2)),
                   rng.normal(loc=[3, 3], scale=0.9, size=(80, 2)),
                   rng.normal(loc=[0, 4], scale=0.9, size=(80, 2))])
    y = np.repeat([0, 1, 2], 80)
    return {"X": X, "y": y, "k_range": [1, 3, 5, 7, 9, 11]}


def solve(X, y, k_range, seed: int = 42):
    X, y = np.asarray(X, float), np.asarray(y)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=seed, stratify=y)
    scaler = StandardScaler().fit(X_train)
    X_train, X_test = scaler.transform(X_train), scaler.transform(X_test)
    scores = {k: float(cross_val_score(KNeighborsClassifier(n_neighbors=k), X_train, y_train, cv=5).mean())
              for k in k_range}
    best_k = max(scores, key=scores.get)
    model = KNeighborsClassifier(n_neighbors=best_k).fit(X_train, y_train)
    pred = model.predict(X_test)
    return best_k, float(accuracy_score(y_test, pred)), confusion_matrix(y_test, pred), scores, pred, y_test


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    best_k, acc, cm, scores, pred, y_test = solve(data["X"], data["y"], data["k_range"])
    report("KNN 分类", 最优K=best_k, 测试准确率=round(acc, 4), 交叉验证最优=round(max(scores.values()), 4))
    save_table(__file__, "K值选择", {"K": list(scores), "交叉验证准确率": np.round(list(scores.values()), 6)})
    save_table(__file__, "混淆矩阵", {"真实类别": np.repeat(np.arange(cm.shape[0]), cm.shape[1]),
                                      "预测类别": np.tile(np.arange(cm.shape[1]), cm.shape[0]),
                                      "样本数": cm.ravel()})
