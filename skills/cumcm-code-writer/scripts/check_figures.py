"""图件合规检查：分辨率、成对输出、轴标签与命名规范。

用法：
    python check_figures.py --project 2026A
    python check_figures.py --figures output/2026A/figures --code-dir output/2026A/code

检查项（F1–F3 阻塞，F4–F5 提示）：
    F1 PNG 分辨率 ≥ 300 dpi（读 PNG 元数据）
    F2 每个 PNG 有同名 PDF（矢量版），反之亦然
    F3 PNG 宽度 ≥ 800 px（避免截图式小图）
    F4 绘图源码里 xlabel/ylabel 数量不少于图件数量（轴标签存在性）
    F5 文件名可自解释：含题号或语义前缀，避免 fig1/图片1 这类
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _paths import OUTPUT_DIR, WORKSPACE_DIR, project_work, rel  # noqa: E402

MIN_DPI = 300
MIN_WIDTH = 800
VAGUE_NAME = re.compile(r"^(fig|figure|图片|图)?\d+$", re.I)
MATLAB_PLOT = re.compile(r"exportgraphics\s*\(|saveas\s*\(|print\s*\([^)]*-(dpng|djpeg|depsc|dpdf)")


def read_png_meta(path: Path) -> dict:
    try:
        from PIL import Image

        with Image.open(path) as image:
            dpi = image.info.get("dpi")
            return {"width": image.size[0], "height": image.size[1],
                    "dpi": float(dpi[0]) if dpi else None}
    except Exception as exc:  # 无法读取时如实记录
        return {"error": str(exc)[:80]}


def label_count(code_dir: Path) -> int:
    count = 0
    for path in code_dir.rglob("*.py"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        count += len(re.findall(r"set_xlabel|set_ylabel", text))
    for path in code_dir.rglob("*.m"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        count += len(re.findall(r"\bxlabel\s*\(|\bylabel\s*\(", text))
    return count


def main() -> int:
    parser = argparse.ArgumentParser(description="图件合规检查")
    parser.add_argument("--project", default="", help="项目名")
    parser.add_argument("--figures", default="", help="图件目录（默认 output/<项目名>/figures）")
    parser.add_argument("--code-dir", default="", help="代码目录（用于轴标签存在性检查）")
    parser.add_argument("--out", default="", help="报告输出路径")
    args = parser.parse_args()

    if args.figures:
        figures = Path(args.figures)
        if not figures.is_absolute():
            candidate = Path.cwd() / figures
            figures = candidate if candidate.exists() else WORKSPACE_DIR / figures
    elif args.project:
        figures = OUTPUT_DIR / args.project / "figures"
    else:
        parser.error("需要 --project 或 --figures")
        return 2

    if not figures.exists():
        print(f"[失败] 图件目录不存在：{rel(figures)}")
        return 2

    code_dir = Path(args.code_dir) if args.code_dir else figures.parent / "code"
    if not code_dir.is_absolute():
        candidate = Path.cwd() / code_dir
        code_dir = candidate if candidate.exists() else WORKSPACE_DIR / code_dir

    pngs = sorted(figures.glob("*.png"))
    pdfs = {path.stem for path in figures.glob("*.pdf")}

    rows = []
    blocking = 0
    for png in pngs:
        meta = read_png_meta(png)
        problems = []
        if "error" in meta:
            problems.append(f"无法读取：{meta['error']}")
        else:
            if meta["dpi"] is None:
                problems.append("PNG 未写 dpi 元数据")
            elif meta["dpi"] < MIN_DPI - 1:
                problems.append(f"分辨率 {meta['dpi']:.0f} dpi < {MIN_DPI}")
            if meta["width"] < MIN_WIDTH:
                problems.append(f"宽度 {meta['width']} px < {MIN_WIDTH}")
        if png.stem not in pdfs:
            problems.append("缺少同名矢量 PDF")
        if VAGUE_NAME.match(png.stem):
            problems.append("文件名不可自解释")
        level = "通过"
        if problems:
            level = "未通过" if any("dpi" in item or "PDF" in item or "宽度" in item or "读取" in item for item in problems) else "提示"
        if level == "未通过":
            blocking += 1
        rows.append({"file": png.name, "level": level,
                     "size": "-" if "error" in meta else f"{meta['width']}×{meta['height']}",
                     "dpi": "-" if "error" in meta or meta.get("dpi") is None else f"{meta['dpi']:.0f}",
                     "problems": "；".join(problems) or "无"})

    orphan_pdfs = sorted(pdfs - {path.stem for path in pngs})
    labels = label_count(code_dir) if code_dir.exists() else 0
    python_saves = 0
    matlab_plots: list[str] = []
    if code_dir.exists():
        for path in code_dir.rglob("*.py"):
            python_saves += len(re.findall(r"savefig\s*\(", path.read_text(encoding="utf-8", errors="ignore")))
        for path in code_dir.rglob("*.m"):
            text = path.read_text(encoding="utf-8", errors="ignore")
            if MATLAB_PLOT.search(text):
                matlab_plots.append(path.name)
    python_ok = python_saves >= len(pngs) if pngs else True
    label_ok = labels >= len(pngs) if pngs else True

    lines = [
        f"# 图件合规检查 · {args.project or figures.parent.name}",
        "",
        f"> 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}；图件目录：`{rel(figures)}`",
        "",
        f"- PNG 数量：{len(pngs)}；PDF 数量：{len(pdfs)}；孤立 PDF：{len(orphan_pdfs)}",
        f"- 绘图源码中的轴标签语句：{labels} 条（{'满足' if label_ok else '少于图件数量，需检查'}）",
        f"- Python 源码中的 savefig 调用：{python_saves} 处（{'覆盖全部图件' if python_ok else '少于图件数量'}）",
        f"- MATLAB 出图调用：{len(matlab_plots)} 个文件（{'无' if not matlab_plots else '；'.join(matlab_plots)}）",
        "",
        "| 图件 | 结论 | 尺寸(px) | dpi | 问题 |",
        "|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(f"| `{row['file']}` | {row['level']} | {row['size']} | {row['dpi']} | {row['problems']} |")
    if orphan_pdfs:
        lines += ["", "孤立 PDF（无对应 PNG）：" + ", ".join(f"`{name}.pdf`" for name in orphan_pdfs)]
    if not pngs:
        lines.append("| - | 未发现图件 | - | - | - |")

    lines += ["", "## 结论", ""]
    if blocking:
        lines.append(f"{blocking} 个图件未达交付标准（分辨率/矢量版缺失），需重绘后再交付。")
    else:
        lines.append("图件全部达标。")
    if not label_ok:
        lines.append("- 轴标签语句少于图件数量：确认每张图都写了横纵轴标签与单位。")
    if not python_ok:
        lines.append("- 部分图件在 Python 源码里找不到 savefig：所有交付图件必须由 Python 生成。")
    if matlab_plots:
        lines.append("- 检测到 MATLAB 出图调用（" + "、".join(matlab_plots)
                     + "）：交付图件必须改由 Python 绘制，MATLAB 只做计算。")

    report = "\n".join(lines) + "\n"
    print(report)
    target = Path(args.out) if args.out else (project_work(args.project) / "图件检查.md" if args.project
                                             else figures / "图件检查.md")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(report, encoding="utf-8")
    print(f"[写出] {rel(target)}")
    return 1 if (blocking or not python_ok or matlab_plots) else 0


if __name__ == "__main__":
    raise SystemExit(main())
