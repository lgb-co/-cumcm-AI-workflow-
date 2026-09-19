"""决策树分类（Python 最小可运行模板）

步骤：CART 建树 → 代价复杂度剪枝选 ccp_alpha → 输出准确率、树深度与特征重要性。
接口：solve(X, y, names) -> (准确率, 深度, 重要性)；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_table  # noqa: E402


def build_demo() -> dict:
    rng = np.random.default_rng(42)
    X = rng.normal(size=(400, 4))
    score = 1.2 * X[:, 0] - 0.8 * X[:, 1] + 0.5 * X[:, 2] + rng.normal(scale=0.5, size=400)
    return {"X": X, "y": (score > 0).astype(int), "names": ["指标A", "指标B", "指标C", "指标D"]}


def solve(X, y, seed: int = 42):
    X, y = np.asarray(X, float), np.asarray(y)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=seed, stratify=y)
    base = DecisionTreeClassifier(random_state=seed).fit(X_train, y_train)
    path = base.cost_complexity_pruning_path(X_train, y_train)
    best_acc, best_model = 0.0, base
    for alpha in path.ccp_alphas[::5]:
        model = DecisionTreeClassifier(random_state=seed, ccp_alpha=float(alpha)).fit(X_train, y_train)
        acc = float(accuracy_score(y_test, model.predict(X_test)))
        if acc >= best_acc:
            best_acc, best_model = acc, model
    return best_acc, int(best_model.get_depth()), best_model.feature_importances_


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    acc, depth, importance = solve(data["X"], data["y"])
    report("决策树", 测试准确率=round(acc, 4), 剪枝后深度=depth, 特征重要性=np.round(importance, 4).tolist())
    save_table(__file__, "特征重要性", {"特征": data["names"], "重要性": np.round(importance, 6)})
