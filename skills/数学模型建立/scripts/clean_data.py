# -*- coding: utf-8 -*-
"""把 data/raw 里的原始数据清洗成 data/clean，并生成清洗日志与质量报告。

用法：
    python clean_data.py --raw "<交付目录>/data/raw" --out "<交付目录>/data/clean"
    python clean_data.py --raw ... --out ... --config clean_config.json

默认行为（可用 --config 覆盖单个文件的设置）：
  - 自动尝试 utf-8-sig / gbk / utf-8 编码，自动嗅探分隔符
  - 列名去空白；字符串单元格去首尾空白
  - 统一识别常见缺失编码（空串、-、--、NA、N/A、null、None、… 等）
  - 删除全空行列、删除完全重复行
  - 可转换率 >=80% 的文本列转为数值列
  - 统计缺失率、重复数、IQR 异常值数量（默认只统计不删除）

同时读取 <交付目录>/data/sources.csv（若存在），把来源信息带进质量报告。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import pandas as pd  # noqa: E402

MISSING_TOKENS = {"", "-", "--", "---", "na", "n/a", "null", "none", "nan", "…", "...", "－", "—",
                  "无", "不详", "未提供", "-999", "-9999", "999999"}
ENCODINGS = ("utf-8-sig", "gbk", "utf-8", "latin-1")


def read_table(path: Path, spec: dict) -> dict[str, pd.DataFrame]:
    suffix = path.suffix.lower()
    if suffix in {".xlsx", ".xls"}:
        sheets = pd.read_excel(path, sheet_name=None, dtype=object)
        return {name: df for name, df in sheets.items()}
    if suffix in {".csv", ".txt", ".tsv"}:
        last_error: Exception | None = None
        encodings = [spec["encoding"]] if spec.get("encoding") else list(ENCODINGS)
        for enc in encodings:
            try:
                sep = spec.get("sep", None)
                df = pd.read_csv(path, dtype=object, encoding=enc, sep=sep,
                                 engine="python" if sep is None else "c", skip_blank_lines=True)
                return {spec.get("sheet", path.stem): df}
            except Exception as exc:
                last_error = exc
        raise RuntimeError(f"无法读取 {path.name}: {last_error}")
    raise RuntimeError(f"暂不支持的格式：{path.name}")


def normalize_missing(df: pd.DataFrame) -> pd.DataFrame:
    for col in df.columns:
        series = df[col]
        if series.dtype == object:
            cleaned = series.map(lambda v: v.strip() if isinstance(v, str) else v)
            cleaned = cleaned.map(lambda v: None if (isinstance(v, str) and v.lower() in MISSING_TOKENS) else v)
            df[col] = cleaned
    return df


def coerce_numeric(df: pd.DataFrame, log: list[str]) -> pd.DataFrame:
    for col in df.columns:
        series = df[col]
        if pd.api.types.is_numeric_dtype(series) or pd.api.types.is_bool_dtype(series):
            continue
        non_null = series.dropna()
        if len(non_null) == 0:
            continue
        converted = pd.to_numeric(non_null.astype(str).str.replace(",", "", regex=False)
                                  .str.replace("%", "", regex=False), errors="coerce")
        if converted.notna().mean() >= 0.8:
            df[col] = pd.to_numeric(series.astype(str).str.replace(",", "", regex=False)
                                    .str.replace("%", "", regex=False).where(series.notna()),
                                    errors="coerce")
            log.append(f"列 `{col}` 可转换率 {converted.notna().mean():.0%}，已转为数值型")
    return df


def drop_empty(df: pd.DataFrame, log: list[str]) -> pd.DataFrame:
    rows_before, cols_before = df.shape
    df = df.dropna(axis=0, how="all").dropna(axis=1, how="all")
    if df.shape[0] != rows_before:
        log.append(f"删除全空行 {rows_before - df.shape[0]} 行")
    if df.shape[1] != cols_before:
        log.append(f"删除全空列 {cols_before - df.shape[1]} 列")
    return df


def drop_duplicates(df: pd.DataFrame, spec: dict, log: list[str]) -> pd.DataFrame:
    subset = spec.get("drop_duplicates")
    before = len(df)
    df = df.drop_duplicates(subset=subset, keep="first")
    if len(df) != before:
        scope = "全列" if not subset else "、".join(subset)
        log.append(f"按 {scope} 删除重复行 {before - len(df)} 行")
    return df


def quality_of(df: pd.DataFrame, spec: dict, log: list[str]) -> dict:
    info: dict = {"行数": int(df.shape[0]), "列数": int(df.shape[1]), "列": {}}
    for col in df.columns:
        series = df[col]
        col_info: dict = {
            "缺失数": int(series.isna().sum()),
            "缺失率": round(float(series.isna().mean()), 4),
            "唯一值": int(series.nunique(dropna=True)),
        }
        if pd.api.types.is_numeric_dtype(series) and series.notna().any():
            q1, q3 = series.quantile(0.25), series.quantile(0.75)
            iqr = q3 - q1
            if iqr > 0:
                lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
                outliers = int(((series < lower) | (series > upper)).sum())
            else:  # 四分位距为 0（如常量列或高度离散的整数列）时不做 IQR 异常判定
                lower = upper = float(q1)
                outliers = 0
            col_info.update({
                "最小": float(series.min()), "最大": float(series.max()),
                "均值": round(float(series.mean()), 6), "中位数": float(series.median()),
                "标准差": round(float(series.std()), 6) if len(series.dropna()) > 1 else 0.0,
                "IQR异常值数": outliers,
                "IQR下界": None if pd.isna(lower) else float(lower),
                "IQR上界": None if pd.isna(upper) else float(upper),
            })
            if outliers and spec.get("drop_outliers"):
                log.append(f"列 `{col}` 按 IQR 删除异常值 {outliers} 个（config 指定 drop_outliers）")
        else:
            top = series.dropna().astype(str).value_counts().head(3)
            col_info["常见取值"] = {str(k): int(v) for k, v in top.items()}
        info["列"][str(col)] = col_info
    return info


def apply_drop_outliers(df: pd.DataFrame, spec: dict) -> pd.DataFrame:
    if not spec.get("drop_outliers"):
        return df
    mask = pd.Series(True, index=df.index)
    for col in df.columns:
        series = df[col]
        if pd.api.types.is_numeric_dtype(series) and series.notna().any():
            q1, q3 = series.quantile(0.25), series.quantile(0.75)
            iqr = q3 - q1
            if iqr <= 0:
                continue
            mask &= series.between(q1 - 1.5 * iqr, q3 + 1.5 * iqr) | series.isna()
    return df[mask]


def safe_name(name: str) -> str:
    cleaned = re.sub(r"[^\w\u4e00-\u9fff.-]+", "_", str(name)).strip("_")
    return cleaned or "sheet"


def main() -> int:
    ap = argparse.ArgumentParser(description="清洗原始数据并生成质量报告")
    ap.add_argument("--raw", required=True, help="原始数据目录")
    ap.add_argument("--out", required=True, help="清洗结果目录")
    ap.add_argument("--config", default=None, help="JSON 配置：{文件名: {选项}}")
    ap.add_argument("--sheet", action="append", default=[], help="只处理指定 sheet/表名")
    args = ap.parse_args()

    raw_dir, out_dir = Path(args.raw), Path(args.out)
    if not raw_dir.is_dir():
        print(f"[FAIL] 原始数据目录不存在：{raw_dir}")
        return 1
    out_dir.mkdir(parents=True, exist_ok=True)
    config = json.loads(Path(args.config).read_text(encoding="utf-8")) if args.config else {}

    data_files = [p for p in sorted(raw_dir.rglob("*")) if p.is_file() and p.suffix.lower() in {".csv", ".xlsx", ".xls", ".txt", ".tsv"}]
    if not data_files:
        print(f"[FAIL] {raw_dir} 下没有可清洗的 csv/xlsx/txt 文件")
        return 1

    log: list[str] = [f"# 清洗日志", "", f"- 运行时间：{datetime.now().astimezone():%Y-%m-%d %H:%M:%S%z}", f"- 原始目录：`{raw_dir}`", f"- 清洗目录：`{out_dir}`", ""]
    quality: dict = {"生成时间": datetime.now().astimezone().isoformat(), "文件": {}}

    for path in data_files:
        spec = dict(config.get(path.name, {}))
        log.append(f"## {path.name}")
        log.append("")
        try:
            tables = read_table(path, spec)
        except Exception as exc:
            log.append(f"- 跳过：{exc}")
            log.append("")
            quality["文件"][path.name] = {"错误": str(exc)}
            continue
        for sheet_name, df in tables.items():
            if args.sheet and sheet_name not in args.sheet:
                continue
            if df.empty:
                log.append(f"- sheet `{sheet_name}` 为空，跳过")
                continue
            df = df.copy()
            df.columns = [str(c).strip() for c in df.columns]
            df = normalize_missing(df)
            df = drop_empty(df, log)
            df = drop_duplicates(df, spec, log)
            df = coerce_numeric(df, log)
            info_before_outlier = quality_of(df, spec, log)
            df = apply_drop_outliers(df, spec)
            if spec.get("drop_columns"):
                keep = [c for c in df.columns if c not in spec["drop_columns"]]
                df = df[keep]
                log.append(f"- 按要求删除列：{'、'.join(spec['drop_columns'])}")
            if spec.get("rename"):
                df = df.rename(columns=spec["rename"])
                log.append(f"- 列重命名：{spec['rename']}")
            stem_part = safe_name(path.stem)
            sheet_part = safe_name(sheet_name)
            fname = f"{stem_part}.clean.csv" if sheet_part == stem_part else f"{stem_part}__{sheet_part}.clean.csv"
            target = out_dir / fname
            df.to_csv(target, index=False, encoding="utf-8-sig")
            quality["文件"].setdefault(path.name, {})[sheet_name] = {
                "输出": target.name,
                "清洗前": info_before_outlier,
                "清洗后": quality_of(df, {}, []),
            }
            log.append(f"- sheet `{sheet_name}` → `{target.name}`：{df.shape[0]} 行 × {df.shape[1]} 列")
            log.append("")

    (out_dir / "清洗日志.md").write_text("\n".join(log), encoding="utf-8")
    (out_dir / "_quality.json").write_text(json.dumps(quality, ensure_ascii=False, indent=2), encoding="utf-8")

    report: list[str] = ["# 数据质量报告", "", f"> 生成时间：{quality['生成时间']}", ""]
    sources = out_dir.parent / "sources.csv"
    if sources.exists():
        report += ["## 来源清单", "", "见表 `data/sources.csv`（文件、URL、来源、抓取时间、HTTP状态、字节数、sha256、备注）。", ""]
    for fname, sheets in quality["文件"].items():
        report.append(f"## {fname}")
        report.append("")
        if "错误" in sheets:
            report += [f"- 读取失败：{sheets['错误']}", ""]
            continue
        for sheet_name, info in sheets.items():
            before, after = info["清洗前"], info["清洗后"]
            report += [
                f"### {sheet_name} → `{info['输出']}`",
                "",
                f"- 规模：清洗前 {before['行数']} 行 × {before['列数']} 列，清洗后 {after['行数']} 行 × {after['列数']} 列",
                "",
                "| 列 | 类型 | 缺失率 | 唯一值 | 要点 |",
                "|---|---|---|---|---|",
            ]
            for col, cinfo in before["列"].items():
                missing = f"{cinfo['缺失率']:.1%}"
                if "IQR异常值数" in cinfo:
                    kind = "数值"
                    note = f"均值 {cinfo['均值']}，IQR 界 [{cinfo['IQR下界']}, {cinfo['IQR上界']}]，异常值 {cinfo['IQR异常值数']}"
                else:
                    kind = "文本/日期"
                    common = "、".join(f"{k}({v})" for k, v in list(cinfo.get("常见取值", {}).items())[:3])
                    note = f"常见取值：{common}" if common else "-"
                report.append(f"| {col} | {kind} | {missing} | {cinfo['唯一值']} | {note} |")
            report.append("")
    (out_dir / "质量报告.md").write_text("\n".join(report), encoding="utf-8")

    print(f"[OK] 已清洗 {len(quality['文件'])} 个文件 → {out_dir}")
    print(f"     报告：{out_dir / '质量报告.md'}；日志：{out_dir / '清洗日志.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
