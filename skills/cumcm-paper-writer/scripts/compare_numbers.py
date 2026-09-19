"""比对改写前后论文的数字多重集合：改写只允许改表达，不允许改任何数字。

用法：python compare_numbers.py 改写前.md 改写后.md --out 数字一致性报告.md
退出码 0 = 完全一致；1 = 有差异（逐条列出）。
"""
from __future__ import annotations

import argparse
import io
import os
import re
import sys
from collections import Counter

NUM = re.compile(r"\d+(?:\.\d+)?")


def numbers(path: str) -> Counter:
    text = io.open(path, encoding="utf-8", errors="ignore").read()
    return Counter(NUM.findall(text))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("before")
    ap.add_argument("after")
    ap.add_argument("--out")
    args = ap.parse_args()
    a, b = numbers(args.before), numbers(args.after)
    missing = a - b
    added = b - a
    ok = not missing and not added
    lines = ["# 数字一致性报告（改写前后）", "",
             f"- 改写前：`{args.before}`（{sum(a.values())} 个数字）",
             f"- 改写后：`{args.after}`（{sum(b.values())} 个数字）",
             f"- 结论：{'✅ 数字多重集合完全一致' if ok else '❌ 存在差异'}", ""]
    if missing:
        lines += ["## 改写后丢失的数字", ""] + [f"- `{k}` 少 {v} 次" for k, v in sorted(missing.items())][:50] + [""]
    if added:
        lines += ["## 改写后新增的数字", ""] + [f"- `{k}` 多 {v} 次" for k, v in sorted(added.items())][:50] + [""]
    report = "\n".join(lines) + "\n"
    if args.out:
        io.open(args.out, "w", encoding="utf-8", newline="\n").write(report)
    print(report)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
