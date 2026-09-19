"""梯度提升回归（Python 最小可运行模板）

模型：以决策树为基学习器做函数空间梯度下降；用早停控制过拟合，报告验证曲线最优轮数。
接口：solve(X, y, seed) -> (R², RMSE, 最优轮数)；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_table  # noqa: E402


def build_demo() -> dict:
    rng = np.random.default_rng(42)
    X = rng.uniform(-2, 2, size=(400, 3))
    y = np.exp(X[:, 0]) + np.sin(2 * X[:, 1]) - X[:, 2] ** 2 + rng.normal(scale=0.2, size=400)
    return {"X": X, "y": y}


def solve(X, y, seed: int = 42):
    X = np.asarray(X, float)
    y = np.asarray(y, float)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=seed)
    model = GradientBoostingRegressor(n_estimators=500, learning_rate=0.05, max_depth=3,
                                      subsample=0.8, random_state=seed, validation_fraction=0.15,
                                      n_iter_no_change=30, tol=1e-4)
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    r2 = float(model.score(X_test, y_test))
    rmse = float(np.sqrt(np.mean((pred - y_test) ** 2)))
    curve = np.asarray(model.train_score_)
    return r2, rmse, model.n_estimators_, curve, pred, y_test


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    r2, rmse, n_trees, curve, pred, y_test = solve(data["X"], data["y"])
    report("梯度提升", R2=round(r2, 4), RMSE=round(rmse, 4), 实际使用树数=n_trees)
    save_table(__file__, "训练偏差", {"树序号": np.arange(1, len(curve) + 1), "偏差": np.round(curve, 6)})
    save_table(__file__, "预测对照", {"样本": np.arange(1, len(pred) + 1),
                                      "实际值": np.round(y_test, 4), "预测值": np.round(pred, 4)})
