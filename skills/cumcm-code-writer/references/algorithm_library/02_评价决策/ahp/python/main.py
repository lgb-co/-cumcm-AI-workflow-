"""层次分析法 AHP · 指标权重（Python 最小可运行模板）

步骤：构造判断矩阵 → 求最大特征值对应的特征向量 → 归一化得权重 → 一致性检验 CR<0.1。
接口：solve(A) -> (权重, CR)；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_table  # noqa: E402

RI = {1: 0.0, 2: 0.0, 3: 0.58, 4: 0.90, 5: 1.12, 6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45}


def build_demo() -> dict:
    return {"A": [[1, 2, 5], [1 / 2, 1, 3], [1 / 5, 1 / 3, 1]]}


def solve(A):
    A = np.asarray(A, float)
    n = A.shape[0]
    values, vectors = np.linalg.eig(A)
    k = int(np.argmax(values.real))
    weight = np.abs(vectors[:, k].real)
    weight = weight / weight.sum()
    lambda_max = values.real[k]
    CI = (lambda_max - n) / (n - 1) if n > 2 else 0.0
    CR = CI / RI.get(n, 1.45) if RI.get(n, 1.45) else 0.0
    return weight, float(CR), float(lambda_max)


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    weight, CR, lambda_max = solve(data["A"])
    report("层次分析法", 权重=np.round(weight, 4).tolist(), CR=round(CR, 4),
           一致性通过="是" if CR < 0.1 else "否")
    save_table(__file__, "指标权重", {"指标": [f"C{i + 1}" for i in range(len(weight))],
                                      "权重": np.round(weight, 6)})
