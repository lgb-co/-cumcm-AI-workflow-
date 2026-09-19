"""生成结果文档：逐问结果、图表、自测结论、运行说明与限制。

用法：
    python build_results_doc.py --project 2026A
    python build_results_doc.py --project 2026A --source work/2026A/结果草稿.md

约定：
    - 正文内容来自 work/<项目名>/结果草稿.md（由技能在写码阶段按模板撰写）；
      缺失时自动按 tables/figures 生成骨架，提示补写结论。
    - 图片相对路径会解析到 output/<项目名>/ 下，DOCX 中直接嵌入原图。
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _docx import convert  # noqa: E402
from _paths import OUTPUT_DIR, WORKSPACE_DIR, project_work, rel  # noqa: E402

IMAGE_RE = re.compile(r"!\[(?P<alt>[^\]]*)\]\((?P<src>[^)]+)\)")


def figure_alt(path: Path, question: str = "") -> str:
    stem = path.stem.replace("_", " ")
    return f"图 {question} {stem}".strip()


def auto_sections(project_dir: Path, work_dir: Path) -> str:
    lines = ["## 四、结果与分析", ""]
    tables = sorted((project_dir / "tables").glob("*.csv")) if (project_dir / "tables").exists() else []
    if tables:
        lines += ["### 结果表", ""]
        for path in tables:
            try:
                frame = pd.read_csv(path)
            except Exception:
                lines.append(f"- `{rel(path)}`（读取失败，请人工检查）")
                continue
            head = frame.head(10)
            lines += [f"**{path.stem}**", "", head.to_markdown(index=False), ""]
            if len(frame) > 10:
                lines.append(f"（完整结果见 `{rel(path)}`，共 {len(frame)} 行）")
                lines.append("")
    else:
        lines += ["尚未生成 `tables/` 结果表。", ""]

    figures_dir = project_dir / "figures"
    figures = sorted(figures_dir.glob("*.png")) if figures_dir.exists() else []
    if figures:
        lines += ["### 图表", ""]
        for path in figures:
            lines += [f"![{figure_alt(path)}]({rel(path)})", ""]
    else:
        lines += ["尚未生成 `figures/` 图件。", ""]

    selftest = work_dir / "自测记录.md"
    lines += ["## 五、自测与验证", ""]
    if selftest.exists():
        lines += [f"完整过程见 `{rel(selftest)}`；结论摘录如下。", "", selftest.read_text(encoding="utf-8")[:2000], ""]
    else:
        lines += ["尚未生成自测记录，请先运行 `scripts/selftest.py`。", ""]
    return "\n".join(lines)


def normalize_images(markdown: str, project_dir: Path) -> str:
    def repl(match: re.Match) -> str:
        src = match.group("src").strip()
        if src.startswith("http"):
            return match.group(0)
        candidate = Path(src)
        if not candidate.is_absolute():
            for base in (project_dir, WORKSPACE_DIR):
                if (base / candidate).exists():
                    candidate = base / candidate
                    break
        if candidate.exists():
            return f"![{match.group('alt')}]({candidate.as_posix()})"
        return match.group(0)

    return IMAGE_RE.sub(repl, markdown)


def main() -> int:
    parser = argparse.ArgumentParser(description="生成结果文档")
    parser.add_argument("--project", required=True, help="项目名")
    parser.add_argument("--source", default="", help="结果草稿 Markdown 路径")
    parser.add_argument("--out", default="", help="输出 Markdown 路径")
    parser.add_argument("--no-docx", action="store_true", help="不生成 DOCX")
    args = parser.parse_args()

    project_dir = OUTPUT_DIR / args.project
    work_dir = project_work(args.project)
    source = Path(args.source) if args.source else work_dir / "结果草稿.md"
    if not source.is_absolute():
        source = WORKSPACE_DIR / source

    if source.exists():
        body = source.read_text(encoding="utf-8")
    else:
        body = "\n".join(
            [
                f"# {args.project} 结果文档",
                "",
                f"> 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}",
                "> 尚未提供结果草稿（`work/{}/结果草稿.md`），以下内容由脚本按现有产物生成骨架。".format(args.project),
                "",
                "## 一、结论摘要",
                "",
                "待补：逐问一句话结论与关键数字。",
                "",
                "## 二、数据与预处理",
                "",
                (work_dir / "数据说明.md").read_text(encoding="utf-8")[:1500] if (work_dir / "数据说明.md").exists() else "待补：数据来源、清洗口径与影响。",
                "",
                "## 三、模型与算法实现",
                "",
                "待补：逐问的模型、算法、参数来源与代码位置。",
                "",
                auto_sections(project_dir, work_dir),
                "",
                "## 六、运行说明与限制",
                "",
                (project_dir / "运行说明.md").read_text(encoding="utf-8") if (project_dir / "运行说明.md").exists() else "待补：环境、命令、耗时与已知限制。",
            ]
        )

    normalized = normalize_images(body, project_dir)
    target = Path(args.out) if args.out else project_dir / f"{args.project}_结果文档.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(normalized, encoding="utf-8")
    print(f"[写出] {rel(target)}")

    if not args.no_docx:
        docx_path = target.with_suffix(".docx")
        convert(normalized, docx_path, base_dir=project_dir)
        print(f"[写出] {rel(docx_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
