"""NAR 非线性自回归神经网络预测（Python 最小可运行模板）

思路：把时序展开成滞后特征 X = [y_{t-1}, ..., y_{t-p}]，用 MLP 拟合 y_t，再递归多步预测。
适用于非线性、非平稳但自相关明显的序列；比线性 AR 更能捕捉阈值与饱和效应。
接口：solve(series, lags, steps) -> (预测值, 拟合优度)；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_fig, save_table, set_style  # noqa: E402


def build_demo() -> dict:
    rng = np.random.default_rng(42)
    t = np.arange(120)
    series = 30 + 6 * np.sin(2 * np.pi * t / 24) + 0.05 * t + rng.normal(scale=0.4, size=120)
    return {"series": series, "lags": 6, "steps": 12}


def make_supervised(series, lags: int):
    X = np.column_stack([series[lags - k - 1: len(series) - k - 1] for k in range(lags)])
    return X, series[lags:]


def solve(series, lags: int = 6, steps: int = 12, seed: int = 42):
    series = np.asarray(series, float)
    X, y = make_supervised(series, lags)
    split = int(len(X) * 0.8)
    scaler = StandardScaler().fit(X[:split])
    model = MLPRegressor(hidden_layer_sizes=(16,), activation="tanh", solver="lbfgs",
                         max_iter=3000, random_state=seed)
    model.fit(scaler.transform(X[:split]), y[:split])
    fitted = model.predict(scaler.transform(X))
    window = list(series[-lags:])
    forecast = []
    for _ in range(steps):
        features = np.array(window[-lags:][::-1]).reshape(1, -1)
        value = float(model.predict(scaler.transform(features))[0])
        forecast.append(value)
        window.append(value)
    rmse = float(np.sqrt(np.mean((fitted[split:] - y[split:]) ** 2)))
    return np.array(forecast), fitted, y, rmse


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    forecast, fitted, y, rmse = solve(data["series"], int(data["lags"]), int(data["steps"]))
    report("NAR 神经网络", 滞后阶数=int(data["lags"]), 留出RMSE=round(rmse, 4),
           预测首期=round(float(forecast[0]), 4), 预测末期=round(float(forecast[-1]), 4))
    save_table(__file__, "拟合与预测",
               {"类型": ["拟合"] * len(y) + ["预测"] * len(forecast),
                "数值": np.round(np.concatenate([y, forecast]), 4)})
    plt = set_style()
    fig, ax = plt.subplots()
    t_fit = np.arange(int(data["lags"]), int(data["lags"]) + len(y))
    t_pred = np.arange(t_fit[-1] + 1, t_fit[-1] + 1 + len(forecast))
    ax.plot(t_fit, y, color="#0072B2", label="观测值")
    ax.plot(t_fit, fitted, "--", color="#56B4E9", label="拟合值")
    ax.plot(t_pred, forecast, color="#D55E00", label="递归预测")
    ax.set_xlabel("时间")
    ax.set_ylabel("取值")
    ax.legend()
    save_fig(__file__, fig, "nar_mlp_forecast")
