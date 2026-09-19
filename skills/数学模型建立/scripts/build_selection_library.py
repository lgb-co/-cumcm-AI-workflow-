# -*- coding: utf-8 -*-
"""统计训练语料论文档案里的方法关键词分布，生成选型库的语料依据（只读入参目录）。"""
from __future__ import annotations

import argparse
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def _default_workspace() -> Path:
    """工作区定位：环境变量 → 技能目录的上一级，避免写死打包者机器路径。"""
    env = os.environ.get("MODELING_WORKSPACE") or os.environ.get("CUMCM_WORKSPACE")
    if env:
        return Path(env)
    return Path(__file__).resolve().parents[2]


WORKSPACE = _default_workspace()
DEFAULT_ANCHORS = str(WORKSPACE / "训练语料" / "papers_anchors")
DEFAULT_OUT = str(Path(__file__).resolve().parent.parent / "references" / "选型库_语料统计.md")

FIELD_RE = re.compile(r"^\|\s*([^|]+?)\s*\|\s*(.*?)\s*\|\s*$")
KEYWORD_ROW_RE = re.compile(r"^\|\s*([^|]+?)\s*\|\s*(\d+)\s*\|\s*([^|]*?)\s*\|\s*$")


def parse_anchor(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    info: dict[str, object] = {}
    keywords: list[tuple[str, int]] = []
    in_kw = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("## 方法关键词计数"):
            in_kw = True
            continue
        if in_kw and stripped.startswith("## "):
            in_kw = False
        if in_kw:
            km = KEYWORD_ROW_RE.match(stripped)
            if km and km.group(1) not in {"关键词", "---"}:
                try:
                    keywords.append((km.group(1), int(km.group(2))))
                except ValueError:
                    pass
            continue
        fm = FIELD_RE.match(stripped)
        if fm:
            key, value = fm.group(1), fm.group(2)
            if key not in {"字段", "---"} and set(key) != {"-"}:
                info.setdefault(key, value)
    info["_file"] = path.name
    info["_keywords"] = keywords
    return info


def to_int(value: object, default: int = 0) -> int:
    m = re.search(r"\d+", str(value or ""))
    return int(m.group()) if m else default


def main() -> int:
    ap = argparse.ArgumentParser(description="统计论文档案中的方法关键词分布")
    ap.add_argument("--anchors", default=DEFAULT_ANCHORS, help="papers_anchors 目录")
    ap.add_argument("--out", default=DEFAULT_OUT, help="输出的 Markdown 文件")
    ap.add_argument("--top", type=int, default=12, help="每类榜单保留条目数")
    args = ap.parse_args()

    anchors_dir = Path(args.anchors)
    if not anchors_dir.is_dir():
        print(f"[FAIL] 找不到档案目录：{anchors_dir}")
        print("请用 --anchors 指定 papers_anchors 目录，或设置 MODELING_WORKSPACE 指向工作区根目录。")
        return 1

    total = with_kw = 0
    overall: Counter[str] = Counter()
    by_topic: dict[str, Counter[str]] = defaultdict(Counter)
    by_contest: dict[str, Counter[str]] = defaultdict(Counter)
    by_award: dict[str, Counter[str]] = defaultdict(Counter)

    for path in sorted(anchors_dir.glob("*.md")):
        total += 1
        info = parse_anchor(path)
        keywords = info["_keywords"]
        assert isinstance(keywords, list)
        topic = str(info.get('topic', '') or '').strip()
        if not topic or topic == '?':
            continue
        label = f"{info.get('year', '?')}{topic}"
        if keywords:
            with_kw += 1
            for kw, _cnt in keywords:
                overall[kw] += 1
                by_topic[topic][kw] += 1
                by_contest[label][kw] += 1
                by_award[str(info.get("award", "?"))][kw] += 1

    out: list[str] = []
    out.append("# 选型库语料统计（自动生成）")
    out.append("")
    out.append("> 由 `scripts/build_selection_library.py` 从 `训练语料/papers_anchors/` 重算，")
    out.append("> 记录“获奖论文里实际出现过哪些方法关键词”，用于校准 `选型库.md` 的先验排序。")
    out.append("> 频次不代表方法优劣，也不能替代题目适配性分析。")
    out.append("")
    out.append("## 语料规模")
    out.append("")
    out.append(f"- 论文档案总数：{total}")
    if total:
        out.append(f"- 检出方法关键词的档案：{with_kw}（{with_kw / total:.1%}）")
    out.append(f"- 出现过的不同方法关键词：{len(overall)}")
    out.append("")
    out.append("## 全局方法频次（按论文篇数计）")
    out.append("")
    out.append("| 排名 | 方法关键词 | 出现论文数 | 占有效档案比 |")
    out.append("|---|---|---|---|")
    for rank, (kw, cnt) in enumerate(overall.most_common(args.top), 1):
        ratio = f"{cnt / with_kw:.1%}" if with_kw else "-"
        out.append(f"| {rank} | {kw} | {cnt} | {ratio} |")
    out.append("")
    out.append("## 按题号（A/B/C）分布")
    out.append("")
    for topic in sorted(by_topic):
        out.append(f"### {topic} 题")
        out.append("")
        out.append("| 排名 | 方法关键词 | 出现论文数 |")
        out.append("|---|---|---|")
        for rank, (kw, cnt) in enumerate(by_topic[topic].most_common(args.top), 1):
            out.append(f"| {rank} | {kw} | {cnt} |")
        out.append("")
    out.append("## 按年份-题号分布（近期年份）")
    out.append("")
    for label in sorted(by_contest, reverse=True)[:20]:
        top = "、".join(f"{kw}({cnt})" for kw, cnt in by_contest[label].most_common(6))
        out.append(f"- **{label}**：{top}")
    out.append("")
    out.append("## 按奖次分布")
    out.append("")
    for award in sorted(by_award):
        top = "、".join(f"{kw}({cnt})" for kw, cnt in by_award[award].most_common(args.top))
        out.append(f"- **{award}**：{top}")
    out.append("")
    out.append("## 使用提示")
    out.append("")
    out.append("- 高频关键词只回答“同类问题常考虑哪些方法”，是否采用取决于题意、数据与可检验性。")
    out.append("- 联网检索若发现更贴合题意的模型或算法，以更合适者为准，并写明取舍理由与出处。")
    out.append("- 档案是结构抽取结果，关键词缺失不等于论文未用模型；需要细节时读 `训练语料/papers_text/` 原文。")
    out.append("")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(out), encoding="utf-8")
    print(f"[OK] 已写入 {out_path}")
    print(f"     档案 {total} 份，含关键词 {with_kw} 份，关键词种类 {len(overall)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
