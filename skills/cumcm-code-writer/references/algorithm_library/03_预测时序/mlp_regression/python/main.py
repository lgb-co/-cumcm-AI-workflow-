"""BP 神经网络（MLP）回归（Python 最小可运行模板）

网络：单隐藏层 16 神经元，ReLU，Adam，早停；输入先标准化，避免量纲影响收敛。
接口：solve(X, y, seed) -> (R², RMSE, 预测值)；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_table  # noqa: E402


def build_demo() -> dict:
    rng = np.random.default_rng(42)
    X = rng.uniform(-3, 3, size=(200, 2))
    y = np.sin(X[:, 0]) + 0.5 * X[:, 1] ** 2 + rng.normal(scale=0.1, size=200)
    return {"X": X, "y": y}


def solve(X, y, seed: int = 42):
    X = np.asarray(X, float)
    y = np.asarray(y, float)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=seed)
    scaler = StandardScaler().fit(X_train)
    model = MLPRegressor(hidden_layer_sizes=(16,), activation="relu", solver="adam",
                         max_iter=3000, random_state=seed, early_stopping=True, n_iter_no_change=30)
    model.fit(scaler.transform(X_train), y_train)
    pred = model.predict(scaler.transform(X_test))
    r2 = float(model.score(scaler.transform(X_test), y_test))
    rmse = float(np.sqrt(np.mean((pred - y_test) ** 2)))
    return r2, rmse, pred, y_test


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    r2, rmse, pred, y_test = solve(data["X"], data["y"])
    report("MLP 回归", R2=round(r2, 4), RMSE=round(rmse, 4), 测试样本=len(pred))
    save_table(__file__, "预测对照", {"样本": np.arange(1, len(pred) + 1),
                                      "实际值": np.round(y_test, 4), "预测值": np.round(pred, 4)})
