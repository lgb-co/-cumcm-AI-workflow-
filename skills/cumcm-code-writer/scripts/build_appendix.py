"""生成论文附录（支撑材料文件列表 + 全部完整源码 + 数据与结果清单）。

用法：
    python build_appendix.py --project 2026A
    python build_appendix.py --project 2026A --title "2026A 论文附录" --no-docx

合规要点（对应官方规范第五条/第十一条）：
    - 收录全部完整源程序，逐文件 SHA256 校对后再写入，避免附录与工程目录不一致；
    - 自动扫描身份信息与个人绝对路径；
    - 只列支撑材料文件清单，不打包压缩包。
"""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _docx import convert  # noqa: E402
from _paths import OUTPUT_DIR, WORKSPACE_DIR, project_work, rel  # noqa: E402

CODE_SUFFIXES = {".py", ".m", ".mlx", ".r", ".sql", ".ipynb", ".bat", ".ps1", ".sh", ".txt", ".md"}
SKIP_DIRS = {"__pycache__", ".git", ".ipynb_checkpoints", ".venv", "venv"}
FENCE_BY_SUFFIX = {
    ".py": "python",
    ".m": "matlab",
    ".mlx": "matlab",
    ".r": "r",
    ".sql": "sql",
    ".ipynb": "json",
    ".bat": "bat",
    ".ps1": "powershell",
    ".sh": "bash",
    ".md": "markdown",
    ".txt": "text",
}
IDENTITY_PATTERNS = [
    (re.compile(r"[A-Za-z]:\\Users\\[^\\\s]+"), "个人绝对路径"),
    (re.compile(r"[\u4e00-\u9fa5]{2,}(大学|学院|中学)"), "可能含学校信息"),
    (re.compile(r"\b1[3-9]\d{9}\b"), "疑似手机号"),
]
DEFAULT_FORBIDDEN = ["学校", "赛区", "指导教师", "参赛队号"]


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collect_files(root: Path, suffixes: set[str]) -> list[Path]:
    if not root.exists():
        return []
    out = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if suffixes and path.suffix.lower() not in suffixes:
            continue
        out.append(path)
    return out


def read_text(path: Path) -> str:
    for encoding in ("utf-8", "utf-8-sig", "gbk", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="replace")


def scan_identity(text: str, forbidden: list[str]) -> list[str]:
    findings: list[str] = []
    for pattern, label in IDENTITY_PATTERNS:
        for match in pattern.finditer(text):
            findings.append(f"{label}：{match.group(0)[:40]}")
    for word in forbidden:
        if word and word in text:
            findings.append(f"命中敏感词：{word}")
    return sorted(set(findings))


def verify_consistency(paths: list[Path]) -> tuple[list[dict], list[str]]:
    """先算哈希并读取内容，再重读校验，确保附录内容与磁盘一致。"""
    entries = []
    problems = []
    for path in paths:
        first = sha256_of(path)
        content = read_text(path)
        second = sha256_of(path)
        if first != second:
            problems.append(f"{rel(path)} 在读取过程中发生变化，附录未收录")
            continue
        entries.append({"path": path, "hash": first, "content": content})
    return entries, problems


def embed(md_text: str, offset: int = 2) -> str:
    """把被引用的说明文档嵌入附录：去掉其一级标题，其余标题降级，避免与附录章节冲突。"""
    lines = []
    for line in md_text.splitlines():
        if line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            if level == 1:
                continue
            line = "#" * min(level + offset, 6) + line[level:]
        lines.append(line)
    return "\n".join(lines).strip()


def build_markdown(
    project: str,
    title: str,
    code_entries: list[dict],
    data_files: list[Path],
    result_files: list[Path],
    run_notes: str,
    data_notes: str,
    refs_notes: str,
    warnings: list[str],
    problems: list[str],
) -> str:
    lines = [
        f"# {title}",
        "",
        f"> 项目：{project}　生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"> 本附录按《全国大学生数学建模竞赛论文格式规范（2026 年修订稿）》第四条、第五条、第十一条生成。",
        "",
        "## 一、支撑材料文件列表",
        "",
        "| 类别 | 文件 | 说明 |",
        "|---|---|---|",
    ]
    for entry in code_entries:
        lines.append(f"| 源程序 | `{rel(entry['path'])}` | {entry['path'].suffix} 源文件 |")
    for path in data_files:
        lines.append(f"| 数据 | `{rel(path)}` | 建模输入数据 |")
    for path in result_files:
        lines.append(f"| 结果 | `{rel(path)}` | 中间/最终结果 |")
    if len(code_entries) + len(data_files) + len(result_files) == 0:
        lines.append("| - | - | 未发现可收录文件 |")

    lines += ["", "## 二、运行说明", "", embed(run_notes) or "未提供运行说明。", ""]
    lines += ["", "## 三、源程序", ""]
    for entry in code_entries:
        fence = FENCE_BY_SUFFIX.get(entry["path"].suffix.lower(), "text")
        lines += [
            f"### {rel(entry['path'])}",
            "",
            f"> SHA256：`{entry['hash'][:16]}…`　读取校验：一致",
            "",
            f"```{fence}",
            entry["content"].rstrip(),
            "```",
            "",
        ]

    lines += ["## 四、数据文件说明", "", embed(data_notes) or "未提供数据说明。", ""]
    lines += ["## 五、参考依据与偏离说明", "", embed(refs_notes) or "未提供参考依据说明。", ""]
    lines += ["## 六、结果文件清单", ""]
    if result_files:
        for path in result_files:
            lines.append(f"- `{rel(path)}`")
    else:
        lines.append("- 本次未生成结果文件。")

    if warnings or problems:
        lines += ["", "## 七、生成检查", ""]
        if problems:
            lines += ["**一致性/完整性问题：**", "", *[f"- {item}" for item in problems]]
        if warnings:
            lines += ["", "**身份信息与路径扫描（请人工确认后删除）：**", "", *[f"- {item}" for item in warnings]]
    return "\n".join(lines) + "\n"


def default_run_notes(project: str) -> str:
    return "\n".join(
        [
            "```text",
            f"# 在项目代码目录下运行（Windows PowerShell）",
            f'& "D:\\综合处理\\codex\\演示\\工具\\code_env\\Scripts\\python.exe" run_all.py',
            "# 或使用 MATLAB",
            'matlab -batch "run(\'run_all.m\')"',
            "```",
            "",
            "依赖清单见 `code/requirements.txt`；结果写入 `tables/` 与 `figures/`。",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="生成论文附录")
    parser.add_argument("--project", required=True, help="项目名")
    parser.add_argument("--code-dir", default="", help="代码目录，默认 output/<项目名>/code")
    parser.add_argument("--data", nargs="*", default=[], help="数据文件路径（可多个）")
    parser.add_argument("--title", default="", help="附录标题")
    parser.add_argument("--out", default="", help="输出 Markdown 路径")
    parser.add_argument("--no-docx", action="store_true", help="不生成 DOCX")
    parser.add_argument("--allow-missing-refs", action="store_true",
                        help="允许缺 work/<项目名>/参考依据.md（默认缺就报错，不生成附录）")
    parser.add_argument("--forbid", default=",".join(DEFAULT_FORBIDDEN), help="额外敏感词，逗号分隔")
    args = parser.parse_args()

    project_dir = OUTPUT_DIR / args.project
    code_dir = Path(args.code_dir) if args.code_dir else project_dir / "code"
    if not code_dir.is_absolute():
        code_dir = WORKSPACE_DIR / code_dir
    work_dir = project_work(args.project)

    code_paths = collect_files(code_dir, CODE_SUFFIXES)
    entries, problems = verify_consistency(code_paths)

    data_paths = []
    for raw in args.data:
        path = Path(raw)
        if not path.is_absolute():
            candidate = Path.cwd() / path
            path = candidate if candidate.exists() else WORKSPACE_DIR / path
        if path.exists():
            data_paths.append(path)
        else:
            problems.append(f"数据文件不存在：{raw}")

    result_paths = collect_files(project_dir / "tables", {".csv", ".xlsx", ".md"}) + collect_files(
        project_dir / "figures", {".png", ".pdf", ".svg"}
    )

    run_notes = ""
    for candidate in [project_dir / "运行说明.md", work_dir / "运行说明.md"]:
        if candidate.exists():
            run_notes = read_text(candidate)
            break
    if not run_notes:
        run_notes = default_run_notes(args.project)

    data_notes = ""
    for candidate in [work_dir / "数据说明.md", project_dir / "数据说明.md"]:
        if candidate.exists():
            data_notes = read_text(candidate)
            break

    warnings: list[str] = []
    refs_notes = ""
    refs_path = work_dir / "参考依据.md"
    if refs_path.exists():
        refs_notes = read_text(refs_path)
    elif args.allow_missing_refs:
        refs_notes = "已按 --allow-missing-refs 豁免：本次未提供参考依据与偏离说明。"
        warnings.append("缺少参考依据留痕（已豁免），无法追溯命中的算法模板。")
    else:
        print("[中止] 缺少 work/参考依据.md：无法追溯命中的算法模板与偏离说明。")
        print("        请先补齐参考依据（模板见 templates/参考依据模板.md）；"
              "确需跳过时加 --allow-missing-refs。")
        return 2

    forbidden = [w.strip() for w in args.forbid.split(",") if w.strip()]
    for entry in entries:
        warnings += [f"{rel(entry['path'])}：{item}" for item in scan_identity(entry["content"], forbidden)]

    title = args.title or f"{args.project} 论文附录"
    markdown = build_markdown(
        args.project,
        title,
        entries,
        data_paths,
        result_paths,
        run_notes,
        data_notes,
        refs_notes,
        warnings,
        problems,
    )

    target = Path(args.out) if args.out else project_dir / f"{args.project}_附录.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(markdown, encoding="utf-8")
    print(f"[写出] {rel(target)}  收录源程序 {len(entries)} 个，数据 {len(data_paths)} 个，结果 {len(result_paths)} 个")

    if not args.no_docx:
        docx_path = target.with_suffix(".docx")
        convert(markdown, docx_path, base_dir=project_dir)
        print(f"[写出] {rel(docx_path)}")

    for item in problems:
        print(f"[问题] {item}")
    for item in warnings:
        print(f"[待确认] {item}")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
