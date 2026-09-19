"""随机森林回归（Python 最小可运行模板）

模型：Bootstrap 抽样 + 决策树集成；输出特征重要性与袋外误差。
接口：solve(X, y, seed) -> (R², RMSE, 特征重要性)；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_table  # noqa: E402


def build_demo() -> dict:
    rng = np.random.default_rng(42)
    X = rng.normal(size=(300, 5))
    y = 2 * X[:, 0] + X[:, 1] ** 2 - 1.5 * X[:, 2] + rng.normal(scale=0.4, size=300)
    return {"X": X, "y": y}


def solve(X, y, seed: int = 42, n_estimators: int = 300):
    X = np.asarray(X, float)
    y = np.asarray(y, float)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=seed)
    model = RandomForestRegressor(n_estimators=n_estimators, random_state=seed, oob_score=True,
                                  max_features="sqrt", n_jobs=-1).fit(X_train, y_train)
    pred = model.predict(X_test)
    r2 = float(model.score(X_test, y_test))
    rmse = float(np.sqrt(np.mean((pred - y_test) ** 2)))
    return r2, rmse, model.feature_importances_, pred, y_test


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    r2, rmse, importance, pred, y_test = solve(data["X"], data["y"])
    report("随机森林", R2=round(r2, 4), RMSE=round(rmse, 4),
           特征重要性=np.round(importance, 4).tolist())
    save_table(__file__, "特征重要性", {"特征": [f"X{i + 1}" for i in range(len(importance))],
                                        "重要性": np.round(importance, 6)})
    save_table(__file__, "预测对照", {"样本": np.arange(1, len(pred) + 1),
                                      "实际值": np.round(y_test, 4), "预测值": np.round(pred, 4)})
