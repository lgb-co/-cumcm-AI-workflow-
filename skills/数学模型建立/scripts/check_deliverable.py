# -*- coding: utf-8 -*-
"""交付前自检：问项覆盖、公式编号、尾注闭合、思路图与数据文件、目录约束。

用法：
    python check_deliverable.py --dir "<交付目录>"
    python check_deliverable.py --dir "<交付目录>" --mode data --json

--mode auto（默认）会按 data/raw 是否存在自动判断是否属于“需要外部数据”的题。
退出码：0 全部通过或有告警；1 存在错误。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FENCE_RE = re.compile(r"```mermaid(.*?)```", re.DOTALL)
TAG_RE = re.compile(r"\\tag\{(\d+)\}")
LINENUM_RE = re.compile(r"^\s*\((\d+)\)\s*$", re.MULTILINE)
FOOT_REF_RE = re.compile(r"\[\^([^\]]+)\](?!:)")
FOOT_DEF_RE = re.compile(r"^\[\^([^\]]+)\]:", re.MULTILINE)


class Checker:
    def __init__(self, root: Path, mode: str, min_refs: int = 8) -> None:
        self.root = root
        self.mode = mode
        self.min_refs = min_refs
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.notes: list[str] = []

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def note(self, msg: str) -> None:
        self.notes.append(msg)

    def find(self, pattern: str) -> Path | None:
        matches = sorted(self.root.glob(pattern))
        return matches[0] if matches else None

    def check_layout(self) -> None:
        resolved = self.root.resolve()
        if "数据集" in resolved.parts:
            self.error(f"交付目录落在 数据集/ 内，违反目录约束：{resolved}")
        plan = self.find("01_*.md")
        data = self.find("02_*.md")
        if plan is None:
            self.error("缺少 01_建模方案_模型与公式.md")
        if data is None:
            self.error("缺少 02_数据与来源.md")
        self.plan_path, self.data_path = plan, data

    def check_plan(self) -> None:
        if not getattr(self, "plan_path", None):
            return
        text = self.plan_path.read_text(encoding="utf-8")
        self.plan_text = text

        if not any(k in text for k in ("数学问题定义", "数学问题陈述")):
            self.error("01 文档缺少《数学问题定义》小节：数据检索前必须先完成数学化审题，见 references/数学化理解题意.md")
        if "数据需求清单" not in text:
            self.warn("01 文档未见《数据需求清单》，建议补上（取数与门禁一的验收标准）")
        if "问项卡" not in text:
            self.error("01 文档缺少“问项卡”小节（题目逐问拆解）")
        else:
            rows = [ln for ln in text.splitlines() if ln.strip().startswith("|") and "问" in ln]
            if len(rows) < 2:
                self.warn("问项卡看起来只有表头，确认逐问是否列全")
            else:
                self.note(f"问项卡候选行 {len(rows)} 行")

        if not FENCE_RE.search(text):
            self.error("01 文档没有任何 ```mermaid 思路图")
        else:
            self.note(f"检测到 {len(FENCE_RE.findall(text))} 个 Mermaid 思路图")

        tags = [int(n) for n in TAG_RE.findall(text)]
        nums = [int(n) for n in LINENUM_RE.findall(text)]
        seq = tags or nums
        convention = "\\tag{}" if tags else ("独立行 (n)" if nums else "无")
        if not seq:
            self.warn("未检测到公式编号（建议用 \\tag{n} 或独立行 (n)），请确认公式是否编号")
        else:
            self.note(f"公式编号约定：{convention}，共 {len(seq)} 个")
            expected = list(range(1, len(seq) + 1))
            if sorted(seq) != expected:
                dup = {n for n in seq if seq.count(n) > 1}
                self.error(f"公式编号不连续或有重复：{sorted(set(seq))}（重复：{sorted(dup)}）")

        refs = [m for m in FOOT_REF_RE.findall(text) if not m.startswith("^")]
        defs = FOOT_DEF_RE.findall(text)
        refs = [r for r in refs if r.strip()]
        missing_def = sorted({r for r in refs if r not in defs})
        unused = sorted({d for d in defs if d not in refs})
        if not refs and not defs:
            self.warn("未检测到尾注引用/定义，确认是否使用了脚注式引用")
        if missing_def:
            self.error(f"正文引用了未定义的尾注：{missing_def}")
        if unused:
            self.error(f"定义了但正文未引用的尾注：{unused}")
        if refs and defs and not missing_def and not unused:
            self.note(f"尾注闭合良好：引用 {len(set(refs))} 条，定义 {len(set(defs))} 条")
        uniq_defs = sorted(set(defs))
        if uniq_defs and len(uniq_defs) < self.min_refs:
            self.warn(f"参考文献仅 {len(uniq_defs)} 条，低于 {self.min_refs} 条的要求；建议按 references/检索与引用规范.md 补充国际权威来源")
        if uniq_defs and not re.search(r"DOI|doi\.org|arXiv|arxiv\.org", text):
            self.warn("参考文献未见 DOI 或 arXiv 标识，建议补充可核验的国际来源（Springer/arXiv/OpenAlex 等）")

        if "参考文献" not in text:
            self.error("01 文档缺少“参考文献”小节")

    def check_data_doc(self) -> None:
        if not getattr(self, "data_path", None):
            return
        text = self.data_path.read_text(encoding="utf-8")
        required = ["数据清单", "来源", "字段说明", "清洗", "质量报告"]
        missing = [k for k in required if k not in text]
        if missing:
            self.error(f"02 数据文档缺少小节：{'、'.join(missing)}")
        else:
            self.note("02 数据文档小节齐全")

    def check_data_files(self) -> None:
        raw, clean, xlsx = self.root / "data" / "raw", self.root / "data" / "clean", self.root / "data" / "汇总数据.xlsx"
        has_raw = raw.is_dir() and any(raw.iterdir())
        mode = self.mode
        if mode == "auto":
            mode = "data" if has_raw else "nodata"
        if mode == "data":
            if not has_raw:
                self.error("判定为数据题，但 data/raw 为空")
            if not (clean.is_dir() and any(clean.glob("*.clean.csv"))):
                self.error("判定为数据题，但 data/clean 下没有清洗结果")
            if not xlsx.exists():
                self.error("缺少 data/汇总数据.xlsx")
            if not (clean / "质量报告.md").exists():
                self.warn("data/clean 下没有 质量报告.md")
        else:
            self.note("判定为非外部数据题，跳过 raw/clean/汇总要求（请在 02 中注明不依赖外部数据）")
            text = self.data_path.read_text(encoding="utf-8") if getattr(self, "data_path", None) else ""
            if not any(k in text for k in ["不依赖外部数据", "无外部数据", "题给附件"]):
                self.warn("非数据题：建议在 02 中明确写“本题不依赖外部数据，数据来源为题给附件”")

    def check_diagrams(self) -> None:
        ddir = self.root / "diagrams"
        pngs = sorted(ddir.glob("*.png")) if ddir.is_dir() else []
        if not pngs:
            if getattr(self, "plan_path", None):
                self.warn("未发现 diagrams/*.png：思路图目前只以 Mermaid 源码存在，需要贴进 Word 时再运行 render_mermaid.py")
            return
        text = self.plan_path.read_text(encoding="utf-8")
        missing = [p.name for p in pngs if p.name not in text]
        if missing:
            self.warn(f"以下图片未被 01 文档引用：{'、'.join(missing)}")
        else:
            self.note(f"图片引用完整：{len(pngs)} 张")

    def check_figures_and_tables(self) -> None:
        """图表与表格检查：表格必须是原生表格，图必须由脚本生成且可复现。"""
        if not getattr(self, "plan_path", None):
            return
        text = self.plan_path.read_text(encoding="utf-8")
        refs = re.findall(IMG_REF_RE, text)
        missing = []
        for ref in refs:
            cand = ref.split(" ")[0].strip()
            candidates = [self.root / cand, self.plan_path.parent / cand, self.root / Path(cand).name]
            if not any(c.exists() for c in candidates):
                missing.append(cand)
        if missing:
            self.error(f"文档引用的图片文件不存在：{missing[:3]}")
        elif refs:
            self.note(f"文档引用的图片全部存在（{len(refs)} 张）")
        pics = [p for p in self.root.rglob("*") if p.suffix.lower() in {".png", ".jpg", ".jpeg"}]
        table_like = [p.name for p in pics if TABLE_LIKE_RE.search(p.stem)]
        if table_like:
            self.error(f"检测到疑似“把表格做成图片”的文件：{table_like[:3]}；表格必须是原生表格（Markdown 表格→Word 表格）")
        table_rows = len(TABLE_ROW_RE.findall(text))
        if table_rows < 3:
            self.warn(f"01 文档原生表格行偏少（{table_rows} 行）：请确认表格没有被图片或截图替代")
        else:
            self.note(f"原生表格行 {table_rows} 行")
        fig_dir = self.root / "图片"
        if fig_dir.is_dir() and list(fig_dir.glob("*.png")) and not (fig_dir / "绘图清单.md").exists():
            self.warn("图片/ 下有图但缺少 绘图清单.md：数据图应由 scripts/make_figures.py 生成并留下数据与图表定义")
        else:
            data_figs = [p.name for p in fig_dir.glob("*.png")] if fig_dir.is_dir() else []
            if data_figs:
                self.note(f"数据图 {len(data_figs)} 张，附绘图清单（Python 生成，可复现）")

    def run(self) -> int:
        if not self.root.is_dir():
            print(f"[FAIL] 目录不存在：{self.root}")
            return 1
        self.check_layout()
        self.check_plan()
        self.check_data_doc()
        self.check_data_files()
        self.check_diagrams()
        self.check_figures_and_tables()

        print(f"交付自检：{self.root}")
        for n in self.notes:
            print(f"  [INFO] {n}")
        for w in self.warnings:
            print(f"  [WARN] {w}")
        for e in self.errors:
            print(f"  [FAIL] {e}")
        print(f"结论：{'通过' if not self.errors else '存在问题'}（错误 {len(self.errors)}，告警 {len(self.warnings)}）")
        return 1 if self.errors else 0


IMG_REF_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
TABLE_ROW_RE = re.compile(r"^\|.*\|\s*$", re.MULTILINE)
TABLE_LIKE_RE = re.compile(r"表|table", re.IGNORECASE)


def main() -> int:
    ap = argparse.ArgumentParser(description="交付物自检")
    ap.add_argument("--dir", required=True, help="交付目录")
    ap.add_argument("--mode", default="auto", choices=["auto", "data", "nodata"])
    ap.add_argument("--json", action="store_true", help="额外输出 JSON 结果")
    ap.add_argument("--min-refs", type=int, default=8, help="参考文献最低条数（默认 8，含国际来源）")
    args = ap.parse_args()

    checker = Checker(Path(args.dir), args.mode, args.min_refs)
    code = checker.run()
    if args.json:
        print(json.dumps({"errors": checker.errors, "warnings": checker.warnings, "notes": checker.notes},
                         ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
