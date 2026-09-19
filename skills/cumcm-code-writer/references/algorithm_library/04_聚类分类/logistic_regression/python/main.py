"""Logistic 回归（Python 最小可运行模板）

步骤：极大似然估计 → 输出系数与优势比 OR、AUC 与混淆矩阵。
接口：solve(X, y, names) -> (AUC, 系数, OR, 混淆矩阵)；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_table  # noqa: E402


def build_demo() -> dict:
    rng = np.random.default_rng(42)
    X = rng.normal(size=(500, 3))
    logit = 1.5 * X[:, 0] - 1.0 * X[:, 1] + 0.5 * X[:, 2]
    y = (rng.random(500) < 1 / (1 + np.exp(-logit))).astype(int)
    return {"X": X, "y": y, "names": ["X1", "X2", "X3"]}


def solve(X, y, seed: int = 42):
    X, y = np.asarray(X, float), np.asarray(y)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=seed, stratify=y)
    scaler = StandardScaler().fit(X_train)
    model = LogisticRegression(max_iter=2000).fit(scaler.transform(X_train), y_train)
    prob = model.predict_proba(scaler.transform(X_test))[:, 1]
    auc = float(roc_auc_score(y_test, prob))
    cm = confusion_matrix(y_test, (prob > 0.5).astype(int))
    return auc, model.coef_[0], np.exp(model.coef_[0]), cm


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    auc, coef, odds, cm = solve(data["X"], data["y"])
    report("Logistic 回归", AUC=round(auc, 4), 系数=np.round(coef, 4).tolist(), 优势比=np.round(odds, 4).tolist())
    save_table(__file__, "系数与优势比", {"变量": data["names"], "系数": np.round(coef, 6), "OR": np.round(odds, 6)})
    save_table(__file__, "混淆矩阵", {"真实类别": np.repeat(np.arange(cm.shape[0]), cm.shape[1]),
                                      "预测类别": np.tile(np.arange(cm.shape[1]), cm.shape[0]),
                                      "样本数": cm.ravel()})
