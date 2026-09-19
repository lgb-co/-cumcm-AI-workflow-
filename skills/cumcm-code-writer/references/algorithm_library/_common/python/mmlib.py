"""参考模板公共工具：统一演示数据、结果输出与中文绘图样式。

模板统一约定：
    - 用 `demo(__file__, builder)` 生成确定性演示数据，并在首次运行时留档到 `data/sample.csv`；
    - 用 `report(...)` 打印关键数字，用 `save_table/save_json` 写 `out/`；
    - 画图用 `set_style()` 拿 plt，保存用 `save_fig(__file__, fig, name)`，自动出 300dpi PNG 与矢量 PDF。
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

PALETTE = [
    "#0072B2",
    "#D55E00",
    "#009E73",
    "#CC79A7",
    "#E69F00",
    "#56B4E9",
    "#F0E442",
    "#666666",
]
CHINESE_FONTS = ["Microsoft YaHei", "SimHei", "SimSun", "DejaVu Sans"]


def seed(value: int = 42) -> np.random.Generator:
    """统一随机数发生器；模板里不要直接用 np.random.*。"""
    return np.random.default_rng(value)


def algo_dir(script_file: str) -> Path:
    return Path(script_file).resolve().parent


def out_dir(script_file: str) -> Path:
    path = algo_dir(script_file) / "out"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _json_safe(value):
    """把元组/整数键等非字符串键转成字符串，供演示数据落盘使用。"""
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, np.ndarray):
        return _json_safe(value.tolist())
    return value


def demo(script_file: str, builder, filename: str = "sample.csv") -> dict:
    """生成演示数据；首次运行时把数据留档到 data/（等长数组写 CSV，否则写 JSON）。"""
    data = builder()
    folder = algo_dir(script_file) / "data"
    folder.mkdir(parents=True, exist_ok=True)
    csv_path = folder / filename
    json_path = folder / (Path(filename).stem + ".json")
    if not csv_path.exists() and not json_path.exists():
        frame: dict[str, np.ndarray] = {}
        for key, value in data.items():
            array = np.atleast_1d(np.asarray(value))
            frame[key] = array if array.ndim == 1 else array.reshape(array.shape[0], -1)[:, 0]
        lengths = {len(value) for value in frame.values()}
        if len(lengths) == 1:
            pd.DataFrame(frame).to_csv(csv_path, index=False, encoding="utf-8-sig")
        else:
            json_path.write_text(
                json.dumps(_json_safe(data), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
    return data

def report(title: str, **fields) -> None:
    body = "  ".join(f"{key}={value}" for key, value in fields.items())
    print(f"[{title}] {body}" if body else f"[{title}]")


def save_table(script_file: str, name: str, data) -> Path:
    frame = data if isinstance(data, pd.DataFrame) else pd.DataFrame(data)
    path = out_dir(script_file) / f"{name}.csv"
    frame.to_csv(path, index=False, encoding="utf-8-sig")
    print(f"  结果表 -> {path.name}")
    return path


def save_json(script_file: str, name: str, payload: dict) -> Path:
    path = out_dir(script_file) / f"{name}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"  结果 -> {path.name}")
    return path


def set_style():
    """返回配置好中文与论文样式的 matplotlib.pyplot。"""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update(
        {
            "font.sans-serif": CHINESE_FONTS,
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
        }
    )
    return plt


def save_fig(script_file: str, fig, name: str) -> tuple[Path, Path]:
    path_png = out_dir(script_file) / f"{name}.png"
    path_pdf = out_dir(script_file) / f"{name}.pdf"
    fig.savefig(path_png, dpi=300)
    fig.savefig(path_pdf)
    print(f"  图 -> {path_png.name} / {path_pdf.name}")
    return path_png, path_pdf
