"""数据门禁（G1）：可读性、字段、缺失、异常、时间口径检查。

用法：
    python check_data.py data/*.csv --project 2026A
    python check_data.py 数据.xlsx --out work/2026A/数据说明.md

输出《数据说明》Markdown：逐文件概况 + 字段字典草稿 + 质量问题 + 待用户确认。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _paths import project_work, rel  # noqa: E402

TEXT_SUFFIXES = {".csv", ".txt", ".tsv", ".dat"}
EXCEL_SUFFIXES = {".xlsx", ".xls"}


def read_table(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix in EXCEL_SUFFIXES:
        return pd.read_excel(path)
    if suffix == ".json":
        return pd.read_json(path)
    if suffix in TEXT_SUFFIXES:
        for encoding in ("utf-8-sig", "utf-8", "gbk"):
            for sep in (None, ",", "\t", ";", r"\s+"):
                try:
                    df = pd.read_csv(path, encoding=encoding, sep=sep, engine="python")
                    if df.shape[1] >= 1:
                        return df
                except Exception:
                    continue
        raise ValueError(f"无法解析文本表格：{path}")
    raise ValueError(f"暂不支持的文件类型：{suffix}（可用 CSV/XLSX/JSON/TXT）")


def describe(df: pd.DataFrame) -> dict:
    info: dict = {"rows": int(df.shape[0]), "cols": int(df.shape[1])}
    info["duplicated"] = int(df.duplicated().sum())
    columns = []
    for name in df.columns:
        series = df[name]
        entry = {
            "name": str(name),
            "dtype": str(series.dtype),
            "missing": int(series.isna().sum()),
            "missing_rate": round(float(series.isna().mean()), 4),
            "unique": int(series.nunique(dropna=True)),
        }
        numeric = pd.to_numeric(series, errors="coerce")
        numeric_rate = float(numeric.notna().mean()) if len(series) else 0.0
        if numeric_rate > 0.8:
            valid = numeric.dropna()
            if not valid.empty:
                entry.update(
                    {
                        "min": float(valid.min()),
                        "max": float(valid.max()),
                        "q25": float(valid.quantile(0.25)),
                        "q50": float(valid.quantile(0.5)),
                        "q75": float(valid.quantile(0.75)),
                        "negative": int((valid < 0).sum()),
                    }
                )
        columns.append(entry)
    info["columns"] = columns
    return info


def detect_time_column(df: pd.DataFrame) -> list[str]:
    hits = []
    for name in df.columns:
        if df[name].dtype.kind in "OM":
            sample = df[name].dropna().astype(str).head(20)
            if sample.empty:
                continue
            parsed = pd.to_datetime(sample, errors="coerce")
            if parsed.notna().mean() > 0.8:
                hits.append(str(name))
    return hits


def build_markdown(reports: list[tuple[Path, dict, list[str]]], issues: list[str]) -> str:
    lines = ["# 数据说明", ""]
    for path, info, time_cols in reports:
        lines += [
            f"## {path.name}",
            "",
            f"- 路径：`{rel(path)}`",
            f"- 规模：{info['rows']} 行 × {info['cols']} 列；完全重复行 {info['duplicated']} 条",
        ]
        if time_cols:
            lines.append(f"- 时间列：{', '.join(time_cols)}")
        lines += ["", "### 字段字典（草稿，请补全含义与单位）", "", "| 字段 | 类型 | 缺失率 | 唯一值 | 最小值 | 最大值 |", "|---|---|---|---|---|---|"]
        for col in info["columns"]:
            lines.append(
                "| {name} | {dtype} | {rate:.2%} | {uniq} | {mn} | {mx} |".format(
                    name=col["name"],
                    dtype=col["dtype"],
                    rate=col["missing_rate"],
                    uniq=col["unique"],
                    mn=col.get("min", "-"),
                    mx=col.get("max", "-"),
                )
            )
        lines.append("")
    lines += ["## 质量问题与处理建议", ""]
    lines += [f"- {item}" for item in issues] if issues else ["- 未发现结构性问题。"]
    lines += [
        "",
        "## 待用户确认",
        "",
        "1. 上表字段的含义与单位是否准确？",
        "2. 缺失值采用插补还是不插补，业务上是否允许？",
        "3. 统计上识别出的异常值是否属于真实业务情况？",
        "4. 多表合并时主键是否唯一、是否存在需要对齐的口径差异？",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="数据检查（门禁 G1）")
    parser.add_argument("paths", nargs="+", help="数据文件路径")
    parser.add_argument("--project", default="", help="写入 work/<项目名>/数据说明.md")
    parser.add_argument("--out", default="", help="Markdown 输出路径")
    args = parser.parse_args()

    reports: list[tuple[Path, dict, list[str]]] = []
    issues: list[str] = []
    failed = False

    for raw in args.paths:
        path = Path(raw)
        if not path.is_absolute():
            candidates = [Path.cwd() / path, Path(__file__).resolve().parents[2] / path]
            path = next((c for c in candidates if c.exists()), path)
        if not path.exists():
            issues.append(f"文件不存在：{rel(path)}")
            failed = True
            continue
        try:
            df = read_table(path)
        except Exception as exc:
            issues.append(f"读取失败：{rel(path)} —— {exc}")
            failed = True
            continue
        info = describe(df)
        time_cols = detect_time_column(df)
        reports.append((path, info, time_cols))
        for col in info["columns"]:
            if col["missing_rate"] >= 0.2:
                issues.append(f"{path.name}·{col['name']} 缺失率 {col['missing_rate']:.1%}，建议弃用或做敏感性分析。")
            elif col["missing_rate"] > 0:
                issues.append(f"{path.name}·{col['name']} 缺失率 {col['missing_rate']:.1%}，需说明插补方法。")
            if col["unique"] == 1 and info["rows"] > 1:
                issues.append(f"{path.name}·{col['name']} 为常量列，建模前确认是否无用。")
            if col.get("negative", 0) > 0:
                issues.append(f"{path.name}·{col['name']} 含 {col['negative']} 个负值，确认是否允许为负。")
        if info["duplicated"] > 0:
            issues.append(f"{path.name} 有 {info['duplicated']} 条完全重复行，需确认是否去重。")

    markdown = build_markdown(reports, issues)
    print(markdown)

    targets = [Path(args.out)] if args.out else []
    if args.project:
        targets.append(project_work(args.project) / "数据说明.md")
    for target in targets:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(markdown, encoding="utf-8")
        print(f"[写出] {rel(target)}")

    return 1 if failed or not reports else 0


if __name__ == "__main__":
    raise SystemExit(main())
