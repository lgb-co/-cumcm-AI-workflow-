"""按语料风格基线检查论文的 AI 味（硬门禁：全部指标必须落在语料 p25–p75 区间）。

用法：
    python check_paper_style.py 论文正文.md --out 风格体检报告.md
    python check_paper_style.py 论文正文.md --baseline references/风格基线.json

判定：每个指标给出 值 / p25–p75 区间 / 结论；任何一项越界即返回退出码 1。
报告含越界证据（长句、列表行、连接词、破折号、段首重复等）与逐条修改要求。
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mine_style_baseline import (  # noqa: E402
    CONNECTIVES, PERSON, VAGUE, clean, style_metrics,
)

HERE = os.path.dirname(os.path.abspath(__file__))

# Windows 控制台默认 GBK，emoji 输出会崩
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # pragma: no cover
    pass

# 主基线由 数据集/（真实获奖论文，有效 442 篇）统计；旧训练语料基线保留作交叉核对
DEFAULT_BASELINE = os.path.join(HERE, "..", "references", "风格基线_数据集.json")
if not os.path.exists(DEFAULT_BASELINE):
    DEFAULT_BASELINE = os.path.join(HERE, "..", "references", "风格基线.json")
FIX_HINT = {
    "句长均值": "拆开超长句、合并碎句，让平均句长落回区间",
    "句长标准差": "增加长短句交错，避免整段同长度",
    "句长变异系数": "句式起伏不足：把连续同构句改成因果/转折结构",
    "超长句占比": "把 60 字以上的句子拆成两句",
    "段落长度变异系数": "段落长短过于一致：让重点段落展开、过渡段落收紧",
    "含数字句占比": "结论要有具体数值支撑，别用形容词收尾",
    "连接词密度": "删掉“首先/其次/最后/综上所述/值得注意的是/由此可见”式推进，改因果衔接",
    "人称密度": "人称使用偏离语料习惯（可自然使用“我们”，但不要机械重复）",
    "空泛词密度": "删掉“重要/显著/极大/充分/有效地/具有重要意义”等无信息量修饰",
    "列表行占比": "正文清单化：把列表改写成叙述段落（清单只留给假设表与参数表）",
    "相邻段首词重复率": "相邻段落开头雷同：改写段首，避免每段同构起笔",
    "分号密度": "分号使用偏离语料习惯",
    "破折号密度": "破折号使用过多（AI 稿常见特征），改成逗号或分句",
    "感叹号密度": "删掉感叹号",
}


def evidence(text: str) -> dict[str, list[str]]:
    paras_text, raw_lines = clean(text)
    sents = []
    for p in [x for x in paras_text.split("\n") if x]:
        sents += [s.strip() for s in re.split(r"[。！？；…]", p) if len(s.strip()) >= 8]
    out = {
        "最长句（前 5）": sorted(sents, key=len, reverse=True)[:5],
        "列表行（前 5）": [ln for ln in raw_lines if re.match(r"^\s*(?:[-*+]|\d+[.、)]|（\d+）|\(\d+\))\s+", ln)][:5],
        "连接词": [f"{w}×{text.count(w)}" for w in CONNECTIVES if w in text],
        "人称": [f"{w}×{text.count(w)}" for w in PERSON if w in text],
        "空泛词": [f"{w}×{text.count(w)}" for w in VAGUE if w in text],
        "破折号": [f"第 {i+1} 行" for i, ln in enumerate(text.splitlines()) if "——" in ln or "—" in ln][:5],
        "感叹号": [f"第 {i+1} 行" for i, ln in enumerate(text.splitlines()) if "！" in ln or "!" in ln][:5],
    }
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="论文风格（低 AI 味）硬门禁检查")
    ap.add_argument("paper")
    ap.add_argument("--baseline", default=DEFAULT_BASELINE)
    ap.add_argument("--out")
    ap.add_argument("--calibrated", action="store_true",
                    help="按校准口径判定（越界项 ≤3 且全部落在语料 p05–p95 内），用于人类不可能全项达标的现实约束")
    ap.add_argument("--calibration", default=None,
                    help="校准结论文字（默认给出语料自检事实）")
    args = ap.parse_args()

    baseline = json.load(io.open(args.baseline, encoding="utf-8"))
    text = io.open(args.paper, encoding="utf-8", errors="ignore").read()
    body = re.split(r"\n\s*#{0,3}\s*(?:参考文献|附录)\s*\n", text, maxsplit=1)[0]
    metrics = style_metrics(body)
    if not metrics:
        print("无法统计风格指标：正文过短或格式异常", file=sys.stderr)
        return 2

    rows, bad = [], []
    for name, band in baseline["指标"].items():
        value = metrics.get(name)
        if value is None:
            continue
        lo, hi = band["p25"], band["p75"]
        if value < lo:
            status = "偏低（越界）"
        elif value > hi:
            status = "偏高（越界）"
        else:
            status = "达标"
        if status != "达标":
            bad.append(name)
        rows.append((name, value, lo, hi, status))

    severe = [n for n, v, lo, hi, st in rows
              if st != "达标" and not (baseline["指标"][n]["p05"] <= v <= baseline["指标"][n]["p95"])]
    calibrated_pass = len(bad) <= 3 and not severe
    ev = evidence(body)
    lines = ["# 论文风格体检报告（低 AI 味硬门禁）", "",
             f"- 严格口径（全部指标落在 p25–p75）：{'达标' if not bad else f'{len(bad)} 项越界'}",
             f"- 校准口径（越界 ≤3 且不超出 p05–p95）：{'达标' if calibrated_pass else '不达标'}"
             + (f"（严重越界：{'、'.join(severe)}）" if severe else ""),
             "- 校准依据：同一口径回测 数据集 444 篇真实获奖论文，全项达标 **0 篇**（越界项数中位 8，最少 3）——"
             "严格口径是改写目标，不是人类论文的现实水平。", "",
             f"- 稿件：`{args.paper}`（正文 {len(body)} 字，已截断参考文献与附录）",
             f"- 基线：`{os.path.relpath(args.baseline)}`（语料 {baseline['样本量']} 篇）",
             f"- 结论：{'✅ 全部达标' if not bad else '❌ ' + str(len(bad)) + ' 项越界：' + '、'.join(bad)}", "",
             "| 指标 | 论文值 | 基线 p25–p75 | 结论 |", "|---|---|---|---|"]
    for name, value, lo, hi, status in rows:
        lines.append(f"| {name} | {value:.4g} | {lo:.4g} – {hi:.4g} | {status} |")
    lines += ["", "## 修改要求", ""]
    for name in bad:
        lines.append(f"- **{name}**：{FIX_HINT.get(name, '按降 AI 味改写手册处理')}")
    lines += ["", "## 证据", ""]
    for key, items in ev.items():
        if items:
            lines.append(f"- {key}：" + "；".join(str(x)[:60] for x in items))
    lines += ["", "> 判据为语料 p25–p75 区间；本报告由 `check_paper_style.py` 生成，越界即不得交付。"]
    report = "\n".join(lines) + "\n"
    if args.out:
        io.open(args.out, "w", encoding="utf-8", newline="\n").write(report)
    print(report)
    if not bad:
        return 0
    if args.calibrated and calibrated_pass:
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
