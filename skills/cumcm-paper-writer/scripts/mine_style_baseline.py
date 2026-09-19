"""从真实国赛论文语料统计写作风格基线（句长、连接词、人称、列表化、标点习惯等）。

用法：
    python mine_style_baseline.py --corpus "…/训练语料/papers_text" \
        --out-json references/风格基线.json --out-md references/风格基线.md

处理要点：PDF 抽取文本按行断句，必须先合并换行再断句；剔除页眉页脚、页码、公式行、图片行与目录残留；
过滤有效正文不足 2000 字的样本，并在输出中记录样本量与剔除清单。
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import statistics
from pathlib import Path

CONNECTIVES = ["首先", "其次", "再次", "最后", "综上所述", "值得注意的是", "由此可见"]
PERSON = ["我们", "本文"]
VAGUE = ["重要", "显著", "极大", "充分", "有效地", "具有重要意义"]
SENT_END = "。！？；…"
NOISE_LINE = re.compile(r"^\s*(?:[-—–=_*·\s]{2,}|\d{1,3}|第\s*\d+\s*页|目录|摘\s*要|关键词[:：]?)\s*$")
HEADING_LINE = re.compile(r"^\s*(?:#{1,6}\s*|[一二三四五六七八九十]+[、.．]|\d+(?:\.\d+)*[、.．]?\s*$)")
CODE_FENCE = re.compile(r"^\s*```")
LIST_LINE = re.compile(r"^\s*(?:[-*+]|\d+[.、)]|（\d+）|\(\d+\))\s+")


def clean(text: str) -> tuple[str, list[str]]:
    """返回 (规整后的正文段落文本, 原始非空行列表)。"""
    text = re.sub(r"<!--.*?-->", " ", text, flags=re.S)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)
    text = re.sub(r"https?://\S+", " ", text)
    raw_lines = []
    blocks, cur, in_code = [], [], False
    for line in text.splitlines():
        s = line.strip()
        if CODE_FENCE.match(s):
            in_code = not in_code
            continue
        if in_code or not s:
            if cur:
                blocks.append("".join(cur)); cur = []
            continue
        if NOISE_LINE.match(s) or HEADING_LINE.match(s):
            if cur:
                blocks.append("".join(cur)); cur = []
            continue
        raw_lines.append(s)
        if s.startswith("|"):                      # 表格行不计入正文句子
            if cur:
                blocks.append("".join(cur)); cur = []
            continue
        if re.fullmatch(r"\$+[^$]*\$+", s) or s.startswith("$$"):
            if cur:
                blocks.append("".join(cur)); cur = []
            continue
        cur.append(s)                              # PDF 断行：直接拼接
    if cur:
        blocks.append("".join(cur))
    paras = [b for b in blocks if len(b) >= 50]
    # 去掉行内 Markdown 标记（**粗体**、`代码`、*斜体*），避免影响句长与段首统计
    paras = [re.sub(r"[*`_]{1,3}", "", b) for b in paras]
    return "\n".join(paras), raw_lines


def sentence_metrics(paras: list[str]) -> dict:
    sents = []
    for p in paras:
        for s in re.split(r"[。！？；…]", p):
            s = s.strip()
            if len(s) >= 8:
                sents.append(s)
    lens = [len(s) for s in sents]
    if len(lens) < 20:
        return {}
    mean = statistics.mean(lens)
    sd = statistics.pstdev(lens)
    return {
        "句长均值": mean,
        "句长标准差": sd,
        "句长变异系数": sd / mean if mean else 0.0,
        "超长句占比": sum(1 for x in lens if x > 60) / len(lens),
        # 段落长度用变异系数（尺度无关），避免短论文天然方差偏小
        "段落长度变异系数": (statistics.pstdev([len(p) for p in paras]) / statistics.mean([len(p) for p in paras]))
        if len(paras) > 1 and statistics.mean([len(p) for p in paras]) else 0.0,
        "含数字句占比": sum(1 for s in sents if re.search(r"\d", s)) / len(sents),
    }


def density(text: str, words: list[str]) -> float:
    n = len(text)
    if not n:
        return 0.0
    return sum(text.count(w) for w in words) / n * 1000.0


def punct_density(text: str, pattern: str) -> float:
    n = len(text)
    if not n:
        return 0.0
    return len(re.findall(pattern, text)) / n * 1000.0


def style_metrics(text: str) -> dict:
    paras_text, raw_lines = clean(text)
    paras = [p for p in paras_text.split("\n") if p]
    m = sentence_metrics(paras)
    if not m:
        return {}
    body = paras_text
    m["连接词密度"] = density(body, CONNECTIVES)
    m["人称密度"] = density(body, PERSON)
    m["空泛词密度"] = density(body, VAGUE)
    lines = [ln for ln in raw_lines if ln]
    m["列表行占比"] = (sum(1 for ln in lines if LIST_LINE.match(ln)) / len(lines)) if lines else 0.0
    firsts = [p[:2] for p in paras]
    m["相邻段首词重复率"] = (sum(1 for a, b in zip(firsts, firsts[1:]) if a == b) / max(1, len(firsts) - 1))
    m["分号密度"] = punct_density(body, r"[；;]")
    m["破折号密度"] = punct_density(body, r"——|—|--")
    m["感叹号密度"] = punct_density(body, r"[！!]")
    return m


def percentiles(values: list[float]) -> dict:
    values = sorted(values)
    def q(p):
        if not values:
            return 0.0
        k = (len(values) - 1) * p
        lo, hi = int(k), min(int(k) + 1, len(values) - 1)
        return values[lo] + (values[hi] - values[lo]) * (k - lo)
    return {"p05": q(0.05), "p25": q(0.25), "p50": q(0.50), "p75": q(0.75), "p95": q(0.95),
            "mean": statistics.mean(values) if values else 0.0}


def main() -> int:
    ap = argparse.ArgumentParser(description="统计国赛论文写作风格基线")
    ap.add_argument("--corpus", required=True, help="语料目录（papers_text）")
    ap.add_argument("--out-json", required=True)
    ap.add_argument("--out-md", required=True)
    ap.add_argument("--min-chars", type=int, default=2000)
    args = ap.parse_args()

    files = sorted(Path(args.corpus).glob("*.md"))
    per_metric: dict[str, list[float]] = {}
    used, skipped = [], []
    for f in files:
        text = io.open(f, encoding="utf-8", errors="ignore").read()
        if len(text) < args.min_chars:
            skipped.append({"file": f.name, "reason": "正文不足"}); continue
        # 只统计正文：遇到参考文献/附录即截断
        cut = re.split(r"\n\s*#{0,3}\s*(?:参考文献|附录)\s*\n", text, maxsplit=1)[0]
        m = style_metrics(cut)
        if not m or len(cut) < args.min_chars:
            skipped.append({"file": f.name, "reason": "有效正文不足"}); continue
        used.append(f.name)
        for k, v in m.items():
            per_metric.setdefault(k, []).append(v)

    baseline = {"样本量": len(used), "语料目录": str(args.corpus), "指标": {}}
    for k, values in per_metric.items():
        baseline["指标"][k] = percentiles(values)
    with io.open(args.out_json, "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"样本量": len(used), "剔除": skipped, "指标": baseline["指标"]}, fh,
                  ensure_ascii=False, indent=2)

    lines = ["# 国赛论文写作风格基线", "",
             f"> 语料：{args.corpus}（{len(files)} 篇，有效 {len(used)} 篇，剔除 {len(skipped)} 篇）",
             "> 判定口径：**硬门禁 = 全部指标落在 p25–p75 区间**；p05–p95 仅作参考。", "",
             "| 指标 | p25（下界） | p50（中位） | p75（上界） | p05 | p95 | 说明 |",
             "|---|---|---|---|---|---|---|"]
    NOTES = {
        "句长均值": "平均每句字数；过小=碎句，过大=长句堆砌",
        "句长标准差": "句长起伏；偏低说明句式单调",
        "句长变异系数": "标准差/均值，衡量句式变化比例",
        "超长句占比": "超过 60 字的句子比例",
        "段落长度变异系数": "段落长度差异比例；偏低=段落同构",
        "含数字句占比": "结论落到具体量的比例",
        "连接词密度": "首先/其次/最后/综上所述/值得注意的是/由此可见 每千字",
        "人称密度": "我们/本文 每千字",
        "空泛词密度": "重要/显著/极大/充分/有效地/具有重要意义 每千字",
        "列表行占比": "正文列表行占比；偏高=正文清单化",
        "相邻段首词重复率": "相邻段落开头两字相同的比例；偏高=段落同构",
        "分号密度": "每千字分号数",
        "破折号密度": "每千字破折号数",
        "感叹号密度": "每千字感叹号数",
    }
    for k, st in baseline["指标"].items():
        lines.append(f"| {k} | {st['p25']:.4g} | {st['p50']:.4g} | {st['p75']:.4g} | {st['p05']:.4g} | {st['p95']:.4g} | {NOTES.get(k,'')} |")
    lines += ["", "## 用法", "",
              "1. 论文定稿前运行 `scripts/check_paper_style.py`，任何指标越界即视为不达标；",
              "2. 越界项按 `references/降AI味改写手册.md` 的句级操作修改，改完重跑，最多 3 轮；",
              "3. 基线只统计正文（遇到“参考文献/附录”截断），不含表格、公式与源码。"]
    with io.open(args.out_md, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"[基线] 有效样本 {len(used)}/{len(files)}，指标 {len(baseline['指标'])} 项")
    for k, st in baseline["指标"].items():
        print(f"  {k}: p25={st['p25']:.4g} p50={st['p50']:.4g} p75={st['p75']:.4g}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
