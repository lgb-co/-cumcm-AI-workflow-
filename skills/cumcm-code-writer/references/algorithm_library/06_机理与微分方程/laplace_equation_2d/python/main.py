"""二维拉普拉斯方程 · SOR 迭代（Python 最小可运行模板）

模型：∂²u/∂x² + ∂²u/∂y² = 0，上下边界 100 ℃、左右边界 0 ℃（稳态温度场）。
用超松弛迭代（SOR）求解，输出迭代次数、残差与温度场。
接口：solve(nx, ny, omega, tol) -> (温度场, 迭代次数, 残差)；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_fig, save_table, set_style  # noqa: E402


def build_demo() -> dict:
    return {"nx": 61, "ny": 61, "omega": 1.7, "tol": 1e-6, "max_iter": 20000}


def solve(nx: int, ny: int, omega: float = 1.7, tol: float = 1e-6, max_iter: int = 20000):
    u = np.zeros((ny, nx))
    u[0, :] = 100.0          # 上边界
    u[-1, :] = 100.0         # 下边界（左右保持 0）
    for iteration in range(1, max_iter + 1):
        residual = 0.0
        for j in range(1, ny - 1):
            for i in range(1, nx - 1):
                old = u[j, i]
                new = 0.25 * (u[j - 1, i] + u[j + 1, i] + u[j, i - 1] + u[j, i + 1])
                u[j, i] = old + omega * (new - old)
                residual = max(residual, abs(u[j, i] - old))
            # 用最新值同步边界列，保证下边界条件不被覆盖
            u[j, 0] = 0.0
            u[j, -1] = 0.0
        if residual < tol:
            return u, iteration, residual
    return u, max_iter, residual


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    u, iterations, residual = solve(int(data["nx"]), int(data["ny"]), float(data["omega"]),
                                    float(data["tol"]), int(data["max_iter"]))
    report("拉普拉斯方程", 网格=f"{data['nx']}×{data['ny']}", 松弛因子=data["omega"],
           迭代次数=iterations, 末次残差=f"{residual:.2e}", 中心温度=round(float(u[u.shape[0] // 2, u.shape[1] // 2]), 3))
    x = np.linspace(0, 1, int(data["nx"]))
    y = np.linspace(0, 1, int(data["ny"]))
    save_table(__file__, "中轴温度分布", {"y": np.round(y, 4), "u(x=0.5)": np.round(u[:, u.shape[1] // 2], 4)})
    plt = set_style()
    fig, axes = plt.subplots(1, 2, figsize=(7.6, 3.4))
    image = axes[0].imshow(u, origin="lower", extent=[0, 1, 0, 1], cmap="inferno", aspect="auto")
    axes[0].set_xlabel("x")
    axes[0].set_ylabel("y")
    axes[0].set_title(f"稳态温度场（{iterations} 次迭代）")
    axes[0].grid(False)
    fig.colorbar(image, ax=axes[0], fraction=0.046)
    for j, color in zip([0, u.shape[0] // 4, u.shape[0] // 2], ["#0072B2", "#E69F00", "#D55E00"]):
        axes[1].plot(x, u[j], color=color, label=f"y={y[j]:.2f}")
    axes[1].set_xlabel("x")
    axes[1].set_ylabel("温度 u")
    axes[1].legend()
    save_fig(__file__, fig, "laplace_equation_2d")
