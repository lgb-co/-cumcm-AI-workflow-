"""论文口径一致性检查：把论文里声明写进论文的数值与代码产出的结果表逐条对照。

用法：
    python check_paper_consistency.py --project 2026A
    python check_paper_consistency.py --project 2026A --declared work/2026A/论文口径.md

声明文件格式（work/<项目名>/论文口径.md）：

    | 指标 | 论文数值 | 来源表 | 容差 |
    |---|---|---|---|
    | 最优总成本 | 1350.0 | q2_最优方案.csv | 1e-4 |
    | 方案A 得分 | 0.7879 | q1_评价结果.csv | |

行为：
    - 声明文件不存在时输出"跳过"并返回 0（不阻塞），但在报告中明确写出未核对；
    - 有声明时，逐条在 tables/ 的结果表里按列名匹配（精确或包含），比较数值；
      找不到指标或数值不一致记为未通过，返回 1。
"""
from __future__ import annotations

import argparse
import csv
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _paths import OUTPUT_DIR, WORKSPACE_DIR, project_work, rel  # noqa: E402


def read_declarations(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or "---" in stripped:
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) < 3 or cells[0] in {"指标", ""}:
            continue
        rows.append({"metric": cells[0], "value": cells[1], "table": cells[2],
                     "tolerance": cells[3] if len(cells) > 3 else ""})
    return rows


def load_table(path: Path) -> list[dict]:
    try:
        with path.open(encoding="utf-8-sig", newline="") as handle:
            return list(csv.DictReader(handle))
    except Exception:
        return []


def find_value(rows: list[dict], metric: str):
    """按列名或行标签匹配指标，精确优先、其次最长子串，返回 (列名, 数值)。"""

    def score(label: str) -> int:
        if metric == label:
            return 1000 + len(label)
        if metric in label or label in metric:
            return 100 + len(label)
        return 0

    best = (None, None, 0)
    for row in rows:
        candidates = [(str(key).strip(), value) for key, value in row.items() if key is not None]
        values = list(row.values())
        if len(values) >= 2 and values[0] is not None:
            candidates.append((str(values[0]).strip(), values[1]))
        for label, value in candidates:
            grade = score(label)
            if grade <= best[2]:
                continue
            try:
                number = float(str(value).strip())
            except (TypeError, ValueError):
                continue
            best = (label, number, grade)
    return best[0], best[1]


def main() -> int:
    parser = argparse.ArgumentParser(description="论文口径一致性检查")
    parser.add_argument("--project", required=True, help="项目名")
    parser.add_argument("--declared", default="", help="声明文件（默认 work/<项目名>/论文口径.md）")
    parser.add_argument("--out", default="", help="报告输出路径")
    args = parser.parse_args()

    work = project_work(args.project)
    project_dir = OUTPUT_DIR / args.project
    tables_dir = project_dir / "tables"
    declared_path = Path(args.declared) if args.declared else work / "论文口径.md"
    if not declared_path.is_absolute():
        candidate = Path.cwd() / declared_path
        declared_path = candidate if candidate.exists() else WORKSPACE_DIR / declared_path

    lines = [
        f"# 论文口径一致性检查 · {args.project}",
        "",
        f"> 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"> 声明文件：`{rel(declared_path)}`",
        "",
    ]

    if not declared_path.exists():
        lines += [
            "未提供论文口径声明，本次**未做**论文数值核对（不阻塞交付，但结果文档的限制说明中应写明）。",
            "",
            "声明方式：在 `work/<项目名>/论文口径.md` 里按模板写三列表格（指标 / 论文数值 / 来源表）。",
        ]
        report = "\n".join(lines) + "\n"
        print(report)
        target = Path(args.out) if args.out else work / "论文口径核对.md"
        target.write_text(report, encoding="utf-8")
        print(f"[写出] {rel(target)}")
        return 0

    declarations = read_declarations(declared_path)
    if not declarations:
        lines += ["声明文件存在但没有解析到数据行（需要 `| 指标 | 论文数值 | 来源表 | 容差 |` 三列以上）。", ""]
        report = "\n".join(lines) + "\n"
        print(report)
        target = Path(args.out) if args.out else work / "论文口径核对.md"
        target.write_text(report, encoding="utf-8")
        print(f"[写出] {rel(target)}")
        return 1

    lines += [f"共 {len(declarations)} 条声明，结果表目录 `{rel(tables_dir)}`。", "",
              "| 指标 | 论文数值 | 代码取值 | 来源表 | 结论 |", "|---|---|---|---|---|"]
    cache: dict[str, list[dict]] = {}
    failures = 0
    for item in declarations:
        table_path = tables_dir / item["table"] if item["table"] else None
        if table_path is not None and not table_path.is_absolute():
            table_path = tables_dir / item["table"]
        if table_path is None or not table_path.exists():
            lines.append(f"| {item['metric']} | {item['value']} | - | {item['table'] or '-'} | 未找到来源表 |")
            failures += 1
            continue
        if table_path.name not in cache:
            cache[table_path.name] = load_table(table_path)
        column, actual = find_value(cache[table_path.name], item["metric"])
        if actual is None:
            lines.append(f"| {item['metric']} | {item['value']} | - | {item['table']} | 表中未找到该指标 |")
            failures += 1
            continue
        try:
            expected = float(item["value"].replace(",", "").replace("%", ""))
        except ValueError:
            lines.append(f"| {item['metric']} | {item['value']} | {actual:.6g} | {item['table']} | 论文数值无法解析 |")
            failures += 1
            continue
        tolerance = float(item["tolerance"]) if item["tolerance"] else 1e-6
        ok = abs(actual - expected) <= tolerance * max(1.0, abs(expected))
        if not ok:
            failures += 1
        lines.append(
            f"| {item['metric']} | {expected:.6g} | {actual:.6g} | {item['table']}（列 `{column}`） | "
            f"{'一致' if ok else '不一致'} |"
        )

    lines += ["", "## 结论", ""]
    if failures:
        lines.append(f"{failures} 条未对上：论文数值与代码输出不一致或无法定位。")
        lines.append("资格红线要求代码结果与论文一致，交付前必须改到一致（或修论文）。")
    else:
        lines.append("全部声明数值与代码结果一致。")

    report = "\n".join(lines) + "\n"
    print(report)
    target = Path(args.out) if args.out else work / "论文口径核对.md"
    target.write_text(report, encoding="utf-8")
    print(f"[写出] {rel(target)}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
