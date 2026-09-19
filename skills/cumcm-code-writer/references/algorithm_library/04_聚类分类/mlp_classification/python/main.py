"""BP 神经网络分类（MLP，Python 最小可运行模板）

网络：单隐藏层 24 神经元、ReLU、Adam、早停；输入标准化；输出混淆矩阵与各类精确率。
接口：solve(X, y) -> (准确率, 混淆矩阵, 分类报告)；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, precision_recall_fscore_support
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_table  # noqa: E402


def build_demo() -> dict:
    rng = np.random.default_rng(42)
    X = np.vstack([rng.normal(loc, scale=0.9, size=(110, 3)) for loc in
                   ([0, 0, 0], [3, 2, 0], [1, 4, 2])])
    y = np.repeat([0, 1, 2], 110)
    return {"X": X, "y": y, "names": ["类别A", "类别B", "类别C"]}


def solve(X, y, names, seed: int = 42):
    X, y = np.asarray(X, float), np.asarray(y)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=seed, stratify=y)
    scaler = StandardScaler().fit(X_train)
    model = MLPClassifier(hidden_layer_sizes=(24,), activation="relu", solver="adam",
                          max_iter=3000, early_stopping=True, n_iter_no_change=30, random_state=seed)
    model.fit(scaler.transform(X_train), y_train)
    pred = model.predict(scaler.transform(X_test))
    precision, recall, f1, _ = precision_recall_fscore_support(y_test, pred, zero_division=0)
    rows = [{"类别": names[i] if i < len(names) else f"类别{i}", "精确率": round(float(precision[i]), 4),
             "召回率": round(float(recall[i]), 4), "F1": round(float(f1[i]), 4)}
            for i in range(len(precision))]
    return float(accuracy_score(y_test, pred)), confusion_matrix(y_test, pred), rows, \
        classification_report(y_test, pred, zero_division=0)


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    accuracy, cm, rows, report_text = solve(data["X"], data["y"], data["names"])
    report("MLP 分类", 测试准确率=round(accuracy, 4), 类别数=len(rows))
    save_table(__file__, "分类指标", rows)
    save_table(__file__, "混淆矩阵", {"真实类别": np.repeat(np.arange(cm.shape[0]), cm.shape[1]),
                                      "预测类别": np.tile(np.arange(cm.shape[1]), cm.shape[0]),
                                      "样本数": cm.ravel()})
    print(report_text)
