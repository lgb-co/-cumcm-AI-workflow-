# -*- coding: utf-8 -*-
"""独立探针模板（把"独立复算"压到分钟级）。

用途：评审/检测阶段用来从原始参数独立复算关键量，**不依赖作者代码**。
用法：复制到 04_代码检测/独立探针/ 下改成本题参数，然后：
    python probe_template.py            # 默认网格序列
本模板给的是「1D 圆柱 + 变扩散系数 + Robin 边界 + 阈值判据」的骨架，示例参数取自 2026A 药材烘干问题。
注意：探针若固定了温度或简化了边界，必须在报告里写明这是「下界/上界口径」。
"""
from __future__ import annotations

import sys
import numpy as np
from scipy.linalg import solve_banded

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ==== 题目参数（改成被评题目的参数）====
R = 0.02          # 几何半径/半厚，m
C_INIT = 2.55     # 初值
C_AIR = 0.04987   # 环境值（边界驱动）
HM = 8.0e-7       # 对流传质系数，m/s
T_K = 323.15      # 固定温度（K）——若用可变温度，写明口径
C_STOP = 0.15     # 判据阈值


def D_of(C: np.ndarray) -> np.ndarray:
    """扩散系数（示例：D = 2.4e-3·exp(-0.45/C)·exp(-3850/T)）。"""
    return 2.4e-3 * np.exp(-0.45 / np.maximum(C, 1e-12)) * np.exp(-3850.0 / T_K)


def solve(n: int, dt: float = 60.0, t_max_h: float = 5000.0):
    """全隐式有限体积 + banded 求解；返回 (达标用时 h, 步数)。"""
    dr = R / n
    r = (np.arange(n) + 0.5) * dr
    rf = np.arange(1, n) * dr
    vol = r * dr
    C = np.full(n, C_INIT)
    steps = int(t_max_h * 3600.0 / dt)
    for k in range(1, steps + 1):
        D = D_of(C)
        Df = 0.5 * (D[:-1] + D[1:])
        af = Df * rf / dr
        main = vol / dt + np.concatenate(([af[0]], af[:-1] + af[1:], [af[-1] + HM * R]))
        lower = np.concatenate(([0.0], -af))
        upper = np.concatenate((-af, [0.0]))
        rhs = vol / dt * C
        rhs[-1] += HM * R * C_AIR
        ab = np.zeros((3, n))
        ab[0, 1:] = upper[:-1]
        ab[1, :] = main
        ab[2, :-1] = lower[1:]
        C = solve_banded((1, 1), ab, rhs)
        if C.max() < C_STOP:
            return k * dt / 3600.0, k
    return float("nan"), steps


if __name__ == "__main__":
    print(f"固定 T={T_K-273.15:.0f} °C，判据 max C < {C_STOP}（若固定温度，请在报告中声明为下界口径）")
    for n in (20, 40, 80, 160, 320):
        t_h, k = solve(n)
        print(f"n={n:4d}  结果={t_h:8.2f}  ({k} 步)")
