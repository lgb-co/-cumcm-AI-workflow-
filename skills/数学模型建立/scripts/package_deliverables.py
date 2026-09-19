# -*- coding: utf-8 -*-
"""把交付物归集到「用户指定路径 / 论文建模 / 题目目录」下，并生成交付清单。

用法：
    python package_deliverables.py --src "建模方案/2025A-烟幕干扰弹的投放策略" \
        --base "D:/综合处理/codex/演示"
    python package_deliverables.py --src ... --base ... --flat        # 不建题目子目录
    python package_deliverables.py --src ... --base ... --no-data     # 不带 data 目录
    python package_deliverables.py --src ... --base ... --folder 论文建模

约定：
  - 目标目录 = <base>/<folder>/<题目目录名>；--flat 时 = <base>/<folder>
  - 复制两份 DOCX、Markdown 源稿、图片（diagrams/*.png 或 图片/）、data 目录（可用 --no-data 跳过）
  - 幂等：同名文件覆盖；最后写入《交付清单.md》，列出内容、来源与大小
"""
from __future__ import annotations

import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def copy_file(src: Path, dst_dir: Path) -> tuple[str, int]:
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst = dst_dir / src.name
    shutil.copy2(src, dst)
    return dst.name, dst.stat().st_size


def copy_tree(src: Path, dst: Path) -> int:
    count = 0
    for item in sorted(src.rglob("*")):
        if item.is_file():
            target = dst / item.relative_to(src)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)
            count += 1
    return count


def main() -> int:
    ap = argparse.ArgumentParser(description="归集交付物到 论文建模 文件夹")
    ap.add_argument("--src", required=True, help="交付目录，如 建模方案/2025A-烟幕干扰弹的投放策略")
    ap.add_argument("--base", required=True, help="用户指定的基础路径")
    ap.add_argument("--folder", default="论文建模", help="归集文件夹名，默认 论文建模")
    ap.add_argument("--flat", action="store_true", help="不建题目子目录，直接放进目标文件夹")
    ap.add_argument("--no-data", action="store_true", help="不复制 data 目录")
    args = ap.parse_args()

    src = Path(args.src).resolve()
    if not src.is_dir():
        print(f"[FAIL] 交付目录不存在：{src}")
        return 1
    base = Path(args.base).resolve()
    if not base.is_dir():
        print(f"[FAIL] 基础路径不存在：{base}")
        return 1

    target = base / args.folder if args.flat else base / args.folder / src.name
    if target.exists() and target.is_file():
        print(f"[FAIL] 目标位置被同名文件占用：{target}")
        return 1
    target.mkdir(parents=True, exist_ok=True)

    rows: list[tuple[str, str, int]] = []
    docx = sorted(src.glob("*.docx"))
    if not docx:
        print("[WARN] 交付目录下没有 .docx：请先运行 scripts/export_docx.py 生成 Word 版")
    for f in docx:
        name, size = copy_file(f, target)
        rows.append((name, "Word 交付文档", size))

    for f in sorted(src.glob("*.md")):
        name, size = copy_file(f, target)
        rows.append((name, "Markdown 源稿", size))

    diagrams = src / "diagrams"
    pngs = sorted(diagrams.glob("*.png")) if diagrams.is_dir() else sorted((src / "图片").glob("*.png"))
    if pngs:
        n = copy_tree(diagrams if diagrams.is_dir() else src / "图片", target / "图片")
        rows.append((f"图片/（{n} 张思路图）", "思路图 PNG", sum(p.stat().st_size for p in pngs)))

    if not args.no_data and (src / "data").is_dir():
        n = copy_tree(src / "data", target / "data")
        total = sum(p.stat().st_size for p in (target / "data").rglob("*") if p.is_file())
        rows.append((f"data/（{n} 个文件）", "数据原始文件、清洗结果与汇总表", total))

    now = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S%z")
    lines = [f"# 交付清单（{src.name}）", "",
             f"- 生成时间：{now}",
             f"- 来源目录：`{src}`",
             f"- 交付目录：`{target}`", "",
             "## 内容", "",
             "| 文件/目录 | 说明 | 大小 |", "|---|---|---|"]
    for name, kind, size in rows:
        lines.append(f"| {name} | {kind} | {size / 1024:.0f} KB |")
    lines += ["", "## 使用提示", "",
              "- 《建模方案_模型与公式》是建模主体文档（含公式、思路图与参考文献）；《数据与来源》说明数据出处、清洗过程与质量报告。",
              "- `data/raw` 为原始数据（不修改），`data/clean` 为清洗结果，`data/汇总数据.xlsx` 为汇总表。",
              "- 若本轮导出的 Word 公式为图片版，需要可编辑公式时请提出，另行处理。"]
    (target / "交付清单.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"[OK] 已归集到 {target}")
    for name, kind, size in rows:
        print(f"     - {name}（{kind}，{size / 1024:.0f} KB）")
    print(f"     交付清单：{target / '交付清单.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
