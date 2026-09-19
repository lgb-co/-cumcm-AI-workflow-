"""项目绘图助手：统一风格与保存口径（图件必须由 Python 生成）。

用法：
    from plotting import set_style, save_fig

    plt = set_style()                      # 已设置中文字体、300dpi、色盲友好网格
    fig, ax = plt.subplots()
    ax.plot(x, y, color=PALETTE[0])
    ax.set_xlabel("时间（天）")             # 轴标签带单位
    ax.set_ylabel("浓度（mg/L）")
    save_fig(fig, "q1_浓度变化")            # 同时输出 300dpi PNG 与矢量 PDF

约定：
    - 所有交付图件由 Python（matplotlib）绘制，MATLAB 只负责计算；
    - 图的数据来源写成 `tables/*.csv`，绘图脚本只读这些表，便于复现；
    - 保存前先确认轴标签与单位、图题编号（如「图 4-1 …」）与论文口径一致。
"""
from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FIGURE_DIR = PROJECT_ROOT / "figures"

# 色盲友好序列（Okabe-Ito 变体）；同一含义全篇同色
PALETTE = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#56B4E9", "#999999"]


def set_style():
    """返回配置好中文与论文样式的 matplotlib.pyplot。"""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({
        "font.sans-serif": ["Microsoft YaHei", "SimHei", "DejaVu Sans"],
        "axes.unicode_minus": False,
        "font.size": 9,
        "figure.dpi": 110,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "axes.grid": True,
        "grid.alpha": 0.3,
        "grid.linestyle": ":",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "legend.frameon": False,
        "figure.figsize": (6.0, 3.8),
    })
    return plt


def save_fig(fig, name: str) -> tuple[Path, Path]:
    """同时保存 300dpi PNG 与矢量 PDF，返回两个路径。"""
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    png = FIGURE_DIR / f"{name}.png"
    pdf = FIGURE_DIR / f"{name}.pdf"
    fig.savefig(png, dpi=300)
    fig.savefig(pdf)
    print(f"  图 -> {png.name} / {pdf.name}")
    return png, pdf
