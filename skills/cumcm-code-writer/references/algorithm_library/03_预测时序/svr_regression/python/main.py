"""支持向量回归 SVR（Python 最小可运行模板）

模型：在 ε-不敏感损失下做核回归；RBF 核的 C、γ、ε 用交叉验证网格搜索。
适合小样本、非线性、含噪声的预测问题；对量纲敏感，必须先标准化。
接口：solve(X, y) -> (R², RMSE, 最优参数)；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVR

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_table  # noqa: E402


def build_demo() -> dict:
    rng = np.random.default_rng(42)
    X = rng.uniform(-3, 3, size=(160, 2))
    y = np.exp(-0.5 * X[:, 0] ** 2) + 0.4 * np.sin(2 * X[:, 1]) + rng.normal(scale=0.05, size=160)
    return {"X": X, "y": y}


def solve(X, y, seed: int = 42):
    X, y = np.asarray(X, float), np.asarray(y, float)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=seed)
    scaler = StandardScaler().fit(X_train)
    grid = GridSearchCV(
        SVR(kernel="rbf"),
        {"C": [0.1, 1, 10, 100], "gamma": ["scale", 0.1, 0.5, 1.0], "epsilon": [0.01, 0.05, 0.1]},
        cv=5, scoring="neg_root_mean_squared_error",
    )
    grid.fit(scaler.transform(X_train), y_train)
    pred = grid.best_estimator_.predict(scaler.transform(X_test))
    r2 = float(1 - ((pred - y_test) ** 2).sum() / ((y_test - y_test.mean()) ** 2).sum())
    rmse = float(np.sqrt(np.mean((pred - y_test) ** 2)))
    return r2, rmse, grid.best_params_, pred, y_test


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    r2, rmse, params, pred, y_test = solve(data["X"], data["y"])
    report("支持向量回归", R2=round(r2, 4), RMSE=round(rmse, 4), 最优参数=str(params),
           支持向量占比="见最优参数" if params else "-")
    save_table(__file__, "预测对照", {"样本": np.arange(1, len(pred) + 1),
                                      "实际值": np.round(y_test, 6), "预测值": np.round(pred, 6)})
    save_table(__file__, "最优参数", {"参数": list(params), "取值": [str(v) for v in params.values()]})
