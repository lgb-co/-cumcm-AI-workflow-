"""模糊综合评价（Python 最小可运行模板）

步骤：权重向量 W 与隶属度矩阵 R 做模糊合成（加权平均型）→ 归一化得评价向量 → 最大隶属度定级。
接口：solve(W, R) -> (评价向量, 等级)；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_table  # noqa: E402


def build_demo() -> dict:
    W = np.array([0.30, 0.25, 0.25, 0.20])
    R = np.array([[0.40, 0.35, 0.20, 0.05],
                  [0.30, 0.40, 0.20, 0.10],
                  [0.20, 0.30, 0.35, 0.15],
                  [0.25, 0.35, 0.30, 0.10]])
    return {"W": W, "R": R, "levels": ["优", "良", "中", "差"]}


def solve(W, R):
    W = np.asarray(W, float)
    R = np.asarray(R, float)
    B = (W[:, None] * R).sum(axis=0)
    B = B / B.sum()
    return B, int(np.argmax(B))


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    B, level = solve(data["W"], data["R"])
    report("模糊综合评价", 评价向量=np.round(B, 4).tolist(), 等级=data["levels"][level])
    save_table(__file__, "评价结果", {"等级": data["levels"], "隶属度": np.round(B, 6)})
