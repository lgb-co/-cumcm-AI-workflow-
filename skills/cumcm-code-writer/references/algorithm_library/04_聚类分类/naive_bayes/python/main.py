"""朴素贝叶斯分类（Python 最小可运行模板）

模型：高斯朴素贝叶斯，假设类别内各特征服从正态分布且条件独立；输出准确率与类条件参数。
接口：solve(X, y) -> (准确率, 先验, 类均值, 类方差)；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import GaussianNB

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_table  # noqa: E402


def build_demo() -> dict:
    rng = np.random.default_rng(42)
    X = np.vstack([rng.normal(loc=[1.0, 1.0], scale=[0.8, 1.0], size=(120, 2)),
                   rng.normal(loc=[3.5, 2.0], scale=[1.0, 0.8], size=(120, 2))])
    return {"X": X, "y": np.repeat([0, 1], 120)}


def solve(X, y, seed: int = 42):
    X, y = np.asarray(X, float), np.asarray(y)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=seed, stratify=y)
    model = GaussianNB().fit(X_train, y_train)
    acc = float(accuracy_score(y_test, model.predict(X_test)))
    return acc, model.class_prior_, model.theta_, model.var_


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    acc, prior, theta, var = solve(data["X"], data["y"])
    report("朴素贝叶斯", 测试准确率=round(acc, 4), 先验=np.round(prior, 4).tolist(),
           类均值=np.round(theta, 4).tolist())
    save_table(__file__, "类条件参数", {"类别": ["C1", "C2"],
                                        "均值X1": np.round(theta[:, 0], 6), "均值X2": np.round(theta[:, 1], 6),
                                        "方差X1": np.round(var[:, 0], 6), "方差X2": np.round(var[:, 1], 6)})
