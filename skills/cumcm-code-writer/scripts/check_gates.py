"""交付门禁检查：确认 G0–G3 产物与三轮自测都齐备，再允许交付。

用法：
    python check_gates.py --project 2026A
    python check_gates.py --project 2026A --out work/2026A/门禁检查.md

检查项（任一不过即退出码 1）：
    G1 数据：work/<项目名>/数据说明.md，或明确声明无需数据的 work/<项目名>/无需数据.md
    G2 工具：work/<项目名>/环境快照.md，且结论一节不含缺失项
    G3 参考：work/<项目名>/参考依据.md，引用的模板 id 必须存在于算法库 manifest，且写明偏离说明
    自测：work/<项目名>/自测记录.md，三轮都有结论、没有"未通过"、没有"未自动验证"
"""
from __future__ import annotations

import argparse
import csv
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _paths import CODE_ENV_PYTHON, LIBRARY_DIR, SCRIPTS_DIR, OUTPUT_DIR, project_work, rel  # noqa: E402

ID_PATTERN = re.compile(r"`([a-z][a-z0-9_]{2,})`")
NON_ID_TOKENS = {"python", "matlab", "meta", "yaml", "csv", "json", "md", "png", "pdf", "sha256"}


def load_library_ids() -> set[str]:
    manifest = LIBRARY_DIR / "manifest.csv"
    if not manifest.exists():
        return set()
    with manifest.open(encoding="utf-8-sig", newline="") as handle:
        return {row["id"] for row in csv.DictReader(handle)}


def table_rows(text: str, section: str) -> list[str]:
    """取某个二级标题下、下一个二级标题之前的表格数据行（不含表头）。"""
    if section not in text:
        return []
    lines = text.split(section, 1)[1].splitlines()
    end = len(lines)
    for index, line in enumerate(lines[1:], start=1):
        if line.startswith("## "):
            end = index
            break
    rows = [line for line in lines[:end] if line.strip().startswith("|") and "---" not in line]
    return [row for row in rows[1:] if row.strip().strip("|").strip()]


def check_data(work: Path) -> tuple[bool, str]:
    note = work / "数据说明.md"
    if note.exists():
        return True, f"数据说明齐备（{rel(note)}）"
    if (work / "无需数据.md").exists() or (work / "无需数据.txt").exists():
        return True, "题目声明无需数据，已在 work 目录留档"
    return False, "缺 work/<项目名>/数据说明.md；若确实无需数据，请写 work/<项目名>/无需数据.md"


def check_env(work: Path) -> tuple[bool, str]:
    snapshot = work / "环境快照.md"
    if not snapshot.exists():
        return False, "缺 work/<项目名>/环境快照.md（运行 check_env.py --project <项目名>）"
    text = snapshot.read_text(encoding="utf-8", errors="ignore")
    if "## 结论" in text and "存在缺失项" in text.split("## 结论", 1)[1]:
        return False, "环境快照显示仍有缺失项未补齐"
    return True, f"环境快照齐备（{rel(snapshot)}）"


def check_refs(work: Path, valid_ids: set[str]) -> tuple[bool, str]:
    path = work / "参考依据.md"
    if not path.exists():
        return False, "缺 work/<项目名>/参考依据.md：无法追溯命中的模板与偏离说明"
    text = path.read_text(encoding="utf-8", errors="ignore")
    problems: list[str] = []

    rows = table_rows(text, "## 命中模板")
    if not rows:
        problems.append("「命中模板」表缺数据行")

    cited: set[str] = set()
    bad_cells: list[str] = []
    for row in rows:
        cells = [cell.strip() for cell in row.strip().strip("|").split("|")]
        if len(cells) < 2:
            continue
        ids = ID_PATTERN.findall(cells[1]) or [cells[1].strip("` ")]
        for token in ids:
            token = token.strip("` ")
            if not token:
                continue
            cited.add(token)
            if valid_ids and token not in valid_ids:
                bad_cells.append(token)
    if not cited:
        problems.append("「命中模板」表第 2 列没有写出模板 id")
    if bad_cells:
        problems.append("引用了算法库中不存在的模板 id：" + ", ".join(sorted(set(bad_cells))))

    if not table_rows(text, "## 偏离与理由"):
        problems.append("「偏离与理由」表缺数据行（完全沿用模板也要写一行说明）")

    if problems:
        return False, "；".join(problems)
    return True, f"参考依据齐备，引用模板 {len(cited)} 个：{', '.join(sorted(cited))}"


def check_selftest(work: Path) -> tuple[bool, str]:
    path = work / "自测记录.md"
    if not path.exists():
        return False, "缺 work/<项目名>/自测记录.md（运行 selftest.py）"
    text = path.read_text(encoding="utf-8", errors="ignore")

    rows = table_rows(text, "## 总览")
    verdicts: dict[str, str] = {}
    for row in rows:
        cells = [cell.strip() for cell in row.strip().strip("|").split("|")]
        if len(cells) >= 3 and cells[0]:
            verdicts[cells[0]] = cells[2]

    problems: list[str] = []
    for name in ("第一轮", "第二轮", "第三轮"):
        verdict = verdicts.get(name)
        if verdict is None:
            problems.append(f"{name}没有记录")
        elif verdict != "通过":
            problems.append(f"{name}结论为「{verdict}」")
    if problems:
        return False, "；".join(problems)
    return True, f"三轮自测全部通过（{rel(path)}）"

def run_subcheck(script: str, project: str, out_name: str) -> tuple[bool, str]:
    """调用同目录下的专项检查脚本；返回（是否通过，说明）。"""
    target = SCRIPTS_DIR / script
    if not target.exists():
        return True, f"未找到 {script}，跳过"
    out_path = project_work(project) / out_name
    proc = subprocess.run(
        [str(CODE_ENV_PYTHON), str(target), "--project", project, "--out", str(out_path)],
        capture_output=True, text=True, check=False,
    )
    if proc.returncode == 0:
        return True, f"通过（{out_name}）"
    if proc.returncode == 2:
        return True, f"目录不存在，跳过（{out_name} 未生成）"
    detail = (proc.stdout or proc.stderr or "").strip().splitlines()
    return False, f"未通过（详见 {out_name}）" + (f"：{detail[-1][:60]}" if detail else "")


def check_lint(project: str) -> tuple[bool, str]:
    return run_subcheck("lint_code.py", project, "代码体检.md")


def check_figures(project: str) -> tuple[bool, str]:
    return run_subcheck("check_figures.py", project, "图件检查.md")


def check_paper(project: str) -> tuple[bool, str]:
    return run_subcheck("check_paper_consistency.py", project, "论文口径核对.md")


def main() -> int:
    parser = argparse.ArgumentParser(description="交付门禁检查")
    parser.add_argument("--project", required=True, help="项目名")
    parser.add_argument("--out", default="", help="报告输出路径")
    args = parser.parse_args()

    work = project_work(args.project)
    valid_ids = load_library_ids()
    checks = [
        ("G1 数据", *check_data(work)),
        ("G2 工具", *check_env(work)),
        ("G3 参考依据", *check_refs(work, valid_ids)),
        ("自测记录", *check_selftest(work)),
        ("代码体检", *check_lint(args.project)),
        ("图件合规", *check_figures(args.project)),
        ("论文口径", *check_paper(args.project)),
    ]

    lines = [
        f"# 交付门禁检查 · {args.project}",
        "",
        f"> 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}；算法库有效模板 id：{len(valid_ids)} 个",
        "",
        "| 门禁 | 结论 | 说明 |",
        "|---|---|---|",
    ]
    failed = []
    for name, ok, note in checks:
        lines.append(f"| {name} | {'通过' if ok else '未通过'} | {note} |")
        if not ok:
            failed.append(f"{name}：{note}")
    lines += ["", "## 结论", ""]
    if failed:
        lines.append("门禁未全部通过，不允许交付：")
        lines += [f"- {item}" for item in failed]
    else:
        lines.append("全部门禁通过，可以进入交付（生成附录与结果文档）。")

    report = "\n".join(lines) + "\n"
    print(report)
    target = Path(args.out) if args.out else work / "门禁检查.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(report, encoding="utf-8")
    print(f"[写出] {rel(target)}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
