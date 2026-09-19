# -*- coding: utf-8 -*-
"""用 Python 生成带数据标注的图表（可复现：脚本 + 数据 + 参数全部留痕）。

用法：
    python make_figures.py --data <data.csv|data.xlsx> --spec <spec.json> --outdir <图片目录>
    python make_figures.py --data data.csv --spec spec.json --outdir 图片 --no-svg

spec.json 为图表列表，每项支持：
    {
      "name": "文件名词干",
      "kind": "line | bar | scatter | dual | timeline",
      "x": "列名", "y": ["列名", ...], "y2": ["列名"]        # dual 用右轴
      "xlabel": "横轴标题", "ylabel": "纵轴标题", "ylabel2": "右轴标题",
      "title": "图标题", "note": "图注（写数据来源与口径）",
      "annotate": "all | max | last | none",                 # 数据标注方式
      "label_fmt": "{:.2f}", "xlim": [a, b], "ylim": [a, b],
      "series_labels": ["曲线A", "曲线B"],                    # 与 y 对应
      "intervals": [["起点列", "终点列", "标签列"]]            # timeline 专用
    }

输出：<outdir>/<name>.png（300 dpi）与同名 .svg，以及 <outdir>/绘图清单.md（记录数据源、
列映射与可复现命令）。图中文字默认使用系统中文黑体，避免方框乱码。
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib import font_manager  # noqa: E402

PALETTE = ["#2F5597", "#C00000", "#2E7D32", "#B26A00", "#6A1B9A", "#00838F"]


def setup_fonts() -> str:
    """优先选系统里的中文字体，返回实际使用的字体名。"""
    preferred = ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "Source Han Sans SC",
                 "PingFang SC", "WenQuanYi Zen Hei", "SimSun"]
    available = {f.name for f in font_manager.fontManager.ttflist}
    for name in preferred:
        if name in available:
            plt.rcParams["font.sans-serif"] = [name]
            plt.rcParams["axes.unicode_minus"] = False
            return name
    plt.rcParams["axes.unicode_minus"] = False
    return "(未找到中文字体，中文可能显示为方框)"


def load_data(path: Path, sheet: str | None) -> pd.DataFrame:
    if path.suffix.lower() in {".xlsx", ".xls"}:
        return pd.read_excel(path, sheet_name=sheet or 0)
    return pd.read_csv(path, encoding="utf-8-sig")


def annotate_points(ax, xs, ys, mode: str, fmt: str) -> None:
    if mode == "none" or not len(xs):
        return
    if mode == "max":
        idx = [max(range(len(ys)), key=lambda i: ys[i])]
    elif mode == "last":
        idx = [len(ys) - 1]
    else:
        idx = list(range(len(ys)))
    for i in idx:
        ax.annotate(fmt.format(ys[i]), (xs[i], ys[i]), textcoords="offset points",
                    xytext=(0, 8), ha="center", fontsize=9, color="#333333")


def draw(fig_spec: dict, df: pd.DataFrame) -> None:
    kind = fig_spec.get("kind", "line")
    fmt = fig_spec.get("label_fmt", "{:.2f}")
    mode = fig_spec.get("annotate", "max")
    xs = df[fig_spec["x"]].tolist() if "x" in fig_spec else list(range(len(df)))

    fig, ax = plt.subplots(figsize=(7.2, 4.2), dpi=100)
    if kind == "bar":
        ys = df[fig_spec["y"][0]].tolist()
        ax.bar([str(v) for v in xs], ys, color=PALETTE[0], width=0.6)
        annotate_points(ax, list(range(len(ys))), ys, mode, fmt)
        ax.set_xticks(range(len(xs)))
        ax.set_xticklabels([str(v) for v in xs], rotation=0)
    elif kind == "scatter":
        ys = df[fig_spec["y"][0]].tolist()
        ax.scatter(xs, ys, s=42, color=PALETTE[1], zorder=3)
        annotate_points(ax, xs, ys, mode, fmt)
    elif kind == "dual":
        ys = df[fig_spec["y"][0]].tolist()
        ax.plot(xs, ys, marker="o", color=PALETTE[0], linewidth=2,
                label=(fig_spec.get("series_labels") or ["左轴"])[0])
        annotate_points(ax, xs, ys, mode, fmt)
        ax2 = ax.twinx()
        y2 = fig_spec.get("y2") or []
        for i, col in enumerate(y2):
            ax2.plot(xs, df[col].tolist(), marker="s", linestyle="--",
                     color=PALETTE[i + 1], linewidth=1.8,
                     label=(fig_spec.get("series_labels") or [])[i + 1] if len(
                         fig_spec.get("series_labels") or []) > i + 1 else col)
        if y2:
            ax2.set_ylabel(fig_spec.get("ylabel2", y2[0]))
        h1, l1 = ax.get_legend_handles_labels()
        h2, l2 = ax2.get_legend_handles_labels()
        if l1 or l2:
            ax.legend(h1 + h2, l1 + l2, frameon=False, loc="best", fontsize=9)
    elif kind == "timeline":
        for row_i, row in df.iterrows():
            start, end = float(row[fig_spec["intervals"][0]]), float(row[fig_spec["intervals"][1]])
            label = str(row[fig_spec["intervals"][2]]) if len(fig_spec["intervals"]) > 2 else str(row_i + 1)
            ax.barh(row_i, end - start, left=start, color=PALETTE[row_i % len(PALETTE)],
                    height=0.5, alpha=0.85)
            ax.text(end + 0.1, row_i, f"{label}  {end - start:.2f}s", va="center", fontsize=9)
        ax.set_yticks(range(len(df)))
        ax.set_yticklabels([f"第 {i + 1} 段" for i in range(len(df))])
        ax.invert_yaxis()
    else:  # line
        labels = fig_spec.get("series_labels") or fig_spec["y"]
        for i, col in enumerate(fig_spec["y"]):
            ys = df[col].tolist()
            ax.plot(xs, ys, marker="o", color=PALETTE[i % len(PALETTE)], linewidth=2,
                    label=labels[i] if i < len(labels) else col)
            annotate_points(ax, xs, ys, mode, fmt)
        if len(fig_spec["y"]) > 1:
            ax.legend(frameon=False, loc="best", fontsize=9)

    ax.set_xlabel(fig_spec.get("xlabel", fig_spec.get("x", "")))
    ax.set_ylabel(fig_spec.get("ylabel", (fig_spec.get("y") or [""])[0]))
    ax.set_title(fig_spec.get("title", ""), fontsize=12)
    ax.grid(alpha=0.25, linestyle="--", linewidth=0.6)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    if fig_spec.get("xlim"):
        ax.set_xlim(*fig_spec["xlim"])
    if fig_spec.get("ylim"):
        ax.set_ylim(*fig_spec["ylim"])
    if fig_spec.get("note"):
        fig.text(0.01, 0.01, fig_spec["note"], fontsize=8, color="#555555")
    fig.tight_layout(rect=(0, 0.03, 1, 1))


def main() -> int:
    ap = argparse.ArgumentParser(description="用 Python 生成带标注的图表")
    ap.add_argument("--data", required=True, help="数据文件（csv/xlsx）")
    ap.add_argument("--spec", required=True, help="图表定义 JSON")
    ap.add_argument("--outdir", required=True, help="输出目录（如图片/）")
    ap.add_argument("--sheet", default=None, help="xlsx 的 sheet 名")
    ap.add_argument("--no-svg", action="store_true", help="只出 PNG")
    args = ap.parse_args()

    data_path = Path(args.data).resolve()
    spec_path = Path(args.spec).resolve()
    out_dir = Path(args.outdir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    specs = json.loads(spec_path.read_text(encoding="utf-8"))
    if isinstance(specs, dict):
        specs = [specs]
    font = setup_fonts()

    made = []
    for spec in specs:
        # 每张图可自带数据源；未指定则用命令行给的 --data
        raw = spec.get("data")
        if raw:
            cand = Path(raw)
            spec_data = cand if cand.is_absolute() else (spec_path.parent / cand).resolve()
        else:
            spec_data = data_path
        df = load_data(spec_data, spec.get("sheet") or args.sheet)
        draw(spec, df)
        png = out_dir / f"{spec['name']}.png"
        plt.savefig(png, dpi=300, bbox_inches="tight")
        if not args.no_svg:
            plt.savefig(out_dir / f"{spec['name']}.svg", bbox_inches="tight")
        plt.close()
        made.append((spec, png, spec_data))
        print(f"[OK] {png.name}")

    lines = [f"# 绘图清单（{datetime.now().astimezone():%Y-%m-%d %H:%M}）", "",
             f"- 数据源：`{data_path}`" + (f"（sheet: {args.sheet}）" if args.sheet else ""),
             f"- 图表定义：`{spec_path}`", f"- 中文字体：{font}", "",
             "| 图 | 类型 | 数据列 | 输出 |", "|---|---|---|---|"]
    for spec, png, spec_data in made:
        cols = ", ".join([spec.get("x", "")] + spec.get("y", []) + spec.get("y2", [])).strip(", ")
        lines.append(f"| {spec['name']} | {spec.get('kind', 'line')} | {cols} | {png.name}（数据：{spec_data.name}） |")
    lines += ["", "## 复现命令", "", "```bash",
              f"python scripts/make_figures.py --data \"{data_path}\" --spec \"{spec_path}\" --outdir \"{out_dir}\"",
              "```", "",
              "> 图中所有数值标注均由脚本按数据生成，不手工修改；换数据后重跑同一条命令即可复现。"]
    (out_dir / "绘图清单.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[OK] 绘图清单：{out_dir / '绘图清单.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
