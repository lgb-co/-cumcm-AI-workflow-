# -*- coding: utf-8 -*-
"""把 cumcm-pipeline 的 Codex 技能移植成 Hermes 技能。

只做四件事，业务正文不改：
  1. frontmatter 换成 Hermes 规范（name/description/version/author/license/platforms/metadata）
  2. 目录名与技能名改成 Hermes 合法名（ASCII 小写连字符）——两个中文名技能被重命名
  3. 兄弟技能的路径/名称引用同步更新，并把 Codex 专有路径（$CODEX_HOME、~/.codex）换掉
  4. 根级散件归位（scripts/ references/），删掉 Codex 专有文件（agents/openai.yaml、install_skill.ps1）

规则驱动：每条替换规则都断言命中数，命中数不符会报警，避免“以为改了其实没匹配上”。
换行风格保持不变（CRLF 的仍写回 CRLF）。
"""
from __future__ import annotations

import os
import re
import shutil
import sys
from pathlib import Path

# 仓库根 = 本脚本所在目录的上一级（hermes-port/..），不写死本机路径
REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "skills"
TOOLS = REPO / "tools"
# 安装目标：Hermes 技能库下的一个分类目录，可用 HERMES_SKILLS_ROOT 覆盖
DST = Path(os.environ.get(
    "HERMES_SKILLS_ROOT",
    str(Path.home() / "AppData" / "Local" / "hermes" / "skills" / "research"),
))
SKILLS_ROOT = str(DST)
PORT_DATE = "2026-09-19"
UPSTREAM = "github.com/star1342354/cumcm-pipeline"

# Codex 目录名 -> Hermes 技能名（目录名即技能名的合法化）
RENAME = {
    "数学模型建立": "cumcm-model-build",
    "数学模型评价": "cumcm-model-review",
    "cumcm-code-writer": "cumcm-code-writer",
    "cumcm-code-reviewer": "cumcm-code-reviewer",
    "cumcm-paper-writer": "cumcm-paper-writer",
    "cumcm-fullflow": "cumcm-fullflow",
}

FM = {
    "cumcm-model-build": {
        "description": "国赛建模：拆题、选型、取数，产出建模方案与数据文档。",
        "platforms": "[windows]",
        "tags": "[cumcm, 数学建模, 建模方案, 国赛]",
        "related": "[cumcm-model-review, cumcm-code-writer]",
    },
    "cumcm-model-review": {
        "description": "评国赛建模方案：逐问四遍复读加联网查证，出诊断与优化方案。",
        "platforms": "[windows]",
        "tags": "[cumcm, 数学建模, 方案评审, 国赛]",
        "related": "[cumcm-model-build, cumcm-fullflow]",
    },
    "cumcm-code-writer": {
        "description": "按定稿模型写竞赛代码，三轮自测，产出附录与结果文档。",
        "platforms": "[linux, macos, windows]",
        "tags": "[cumcm, 数学建模, 代码实现, 国赛]",
        "related": "[cumcm-code-reviewer, cumcm-model-build]",
    },
    "cumcm-code-reviewer": {
        "description": "核验参赛代码是否兑现论文口径，出问题清单与参考分。",
        "platforms": "[linux, macos, windows]",
        "tags": "[cumcm, 数学建模, 代码评审, 国赛]",
        "related": "[cumcm-code-writer, cumcm-model-review]",
    },
    "cumcm-paper-writer": {
        "description": "把定稿材料写成可提交国赛论文，含附录与降 AI 味校验。",
        "platforms": "[linux, macos, windows]",
        "tags": "[cumcm, 数学建模, 论文写作, 国赛]",
        "related": "[cumcm-code-writer, cumcm-fullflow]",
    },
    "cumcm-fullflow": {
        "description": "编排数模全流程：建模到论文，阶段隔离、密封交接、守门禁。",
        "platforms": "[linux, macos, windows]",
        "tags": "[cumcm, 数学建模, 流程编排, 密封交接]",
        "related": "[cumcm-model-build, cumcm-model-review, cumcm-code-writer, cumcm-code-reviewer, cumcm-paper-writer]",
    },
}

# 根级散件 -> 归位目标（相对技能根）
ROOT_RELOCATE = {
    "数学模型评价": [
        ("run.ps1", "scripts/run.ps1"),
        ("setup-dependencies.ps1", "scripts/setup-dependencies.ps1"),
        ("requirements-extraction.txt", "scripts/requirements-extraction.txt"),
        ("manifest.json", "references/_上游原包校验单_manifest.json"),
    ],
    "cumcm-code-writer": [
        ("README.md", "references/_上游README.md"),
        ("安装说明.md", "references/_上游安装说明_Codex版.md"),
    ],
}
# Codex 专有件（Hermes 无对应物，直接删）
ROOT_DROP = {
    "数学模型评价": ["agents"],
    "cumcm-code-writer": ["VERSION", "scripts/install_skill.ps1"],
}

# 显式规则：{技能: [(相对 glob, old, new, 必须命中数)]}
RULES = {
    "数学模型建立": [
        ("SKILL.md", "# 数学模型建立", "# 数学模型建立（cumcm-model-build）", 1),
        # 原 description 里的「只评论文用 数学模型评价…」已随 frontmatter 整块重写删除，
        # 边界语义保留在正文（见下方两条规则）。
        ("SKILL.md", "只给论文要求评分走 `数学模型评价`", "只给论文要求评分走 `cumcm-model-review`", 1),
        ("SKILL.md", "`数学模型评价/work/赛题文本/", "`$SKILLS/cumcm-model-review/work/赛题文本/", 1),
        ("SKILL.md", "`数学模型评价/references/problem_cards/", "`$SKILLS/cumcm-model-review/references/problem_cards/", 1),
        ("SKILL.md", "`数学模型评价\\`、`代码编写评价\\`", "`$SKILLS/cumcm-model-review/`、`$SKILLS/cumcm-code-reviewer/`", 1),
        ("SKILL.md", "`cumcm-code-reviewer/scripts/ocr_pdf.py`", "`$SKILLS/cumcm-code-reviewer/scripts/ocr_pdf.py`", 1),
        ("references/文档导出与工具检测.md", "数学模型建立/scripts/check_docx_toolchain.py",
         "$SKILLS/cumcm-model-build/scripts/check_docx_toolchain.py", 1),
    ],
    "数学模型评价": [
        ("SKILL.md", "# 数学模型评价", "# 数学模型评价（cumcm-model-review）", 1),
        # 正文与 review.py 里的 `数学模型评价` 是运行期产物（报告文件夹/文件名），保持原样。
        # 以下把「由 Codex 完成」这类宿主指称改为 Hermes（宿主换了，行文不能留在旧宿主上）。
        ("references/review-schema.md", "必须由运行 Skill 的 Codex 完成", "必须由运行技能的 Hermes 完成", 1),
        ("references/review-schema.md", "Codex 必须先阅读确认", "Hermes 必须先阅读确认", 1),
        ("references/review-schema.md", "仍需 Codex 检查具体建议是否可执行", "仍需 Hermes 检查具体建议是否可执行", 1),
        ("scripts/review.py", "Offline structural checks for Codex reviews", "Offline structural checks for Hermes reviews", 1),
        ("scripts/review.py", "由宿主 Codex 搜索工具提供", "由宿主 Hermes 搜索工具提供", 1),
        ("scripts/run.ps1", "can still be read by Codex.", "can still be read by Hermes.", 1),
    ],
    "cumcm-code-writer": [
        ("SKILL.md", "查代码用 `代码编写评价/`（cumcm-code-reviewer）", "查代码用 `cumcm-code-reviewer`", 1),
        ("SKILL.md", "只想评价已有代码（转 `代码编写评价`）；只想评论文（转 `数学模型评价`）",
         "只想评价已有代码（转 `cumcm-code-reviewer`）；只想评论文（转 `cumcm-model-review`）", 1),
        ("SKILL.md", "技能被安装到全局（`~/.codex/skills/`）后", "技能装在 Hermes 技能库（`$SKILLS/`）后", 1),
        ("SKILL.md", "| `install_skill.ps1` | 把本技能安装到 `~/.codex/skills`（需你手动运行） | `powershell -File install_skill.ps1` |\n", "", 1),
        ("references/低AI味代码规范.md", "`代码编写评价/references/报告写作风格_自然专业.md`",
         "`$SKILLS/cumcm-code-reviewer/references/报告写作风格_自然专业.md`", 1),
        ("references/附录与结果文档规范.md", "`代码编写评价/references/报告写作风格_自然专业.md`",
         "`$SKILLS/cumcm-code-reviewer/references/报告写作风格_自然专业.md`", 1),
        ("references/official/2026_论文格式规范_附录与支撑材料要求.md", "`代码编写评价/references/official/`",
         "`$SKILLS/cumcm-code-reviewer/references/official/`", 1),
    ],
    "cumcm-code-reviewer": [
        ("SKILL.md", "应转论文评价技能。", "应转 `cumcm-model-review`（只评模型与方案口径）。", 1),
        ("SKILL.md", "需要论文评分时提示另用 `数学模型评价`", "需要论文评分时提示另用 `cumcm-model-review`", 1),
        ("references/rubric_代码评价.md", '给"代码编写评价 Skill"提供', "给 cumcm-code-reviewer 提供", 1),
        ("scripts/extract_code.py", "CUMCM 代码编写评价 Skill 的一部分", "cumcm-code-reviewer 的一部分", 1),
    ],
    "cumcm-paper-writer": [
        ("SKILL.md", "建模选型走 `数学模型建立`/`cumcm-model-review`",
         "建模选型走 `cumcm-model-build`/`cumcm-model-review`", 1),
    ],
    "cumcm-fullflow": [
        ("SKILL.md", "安装包附带 `工具/cumcm-flow`", "技能包附带 `scripts/tools/cumcm-flow`", 1),
        ("SKILL.md", "按名称查找技能目录：先 `$CODEX_HOME/skills/<名称>/SKILL.md`，找不到再查当前工作区同名目录。",
         "按名称查找技能目录：先 `$SKILLS/<名称>/SKILL.md`（本项目六个技能同在一层），"
         "或用 `skill_view(name=...)` 直接加载；找不到再查当前工作区同名目录。", 1),
        ("SKILL.md", "| S1 | `数学模型建立` |", "| S1 | `cumcm-model-build` |", 1),
        ("SKILL.md", "| S4R | `数学模型评价`（cumcm-model-review，结果驱动复盘） |",
         "| S4R | `cumcm-model-review`（结果驱动复盘） |", 1),
        ("SKILL.md", "**用什么技能**：`数学模型评价`（`cumcm-model-review`）",
         "**用什么技能**：`cumcm-model-review`", 1),
        ("references/阶段契约与门禁.md", "## S1 建模（技能：数学模型建立）", "## S1 建模（技能：cumcm-model-build）", 1),
        ("references/阶段契约与门禁.md", "## S4R 结果驱动的模型复盘与优化（技能：数学模型评价 / cumcm-model-review）",
         "## S4R 结果驱动的模型复盘与优化（技能：cumcm-model-review）", 1),
    ],
}

# 全局规则：作用于本技能下所有 .md（跳过 references/algorithm_library 的 421 个模板）
GLOBAL_RULES = [
    ("**/*.md", "`代码编写评价/references/", "`$SKILLS/cumcm-code-reviewer/references/", None),
    ("**/*.md", "`代码编写评价/`", "`$SKILLS/cumcm-code-reviewer/`", None),
]

NOTE = (
    "> **移植说明（Hermes 版）**：本技能原为 Codex 技能 `{orig}`，取自 `{upstream}` v1.1.0（MIT，作者 star1342354），"
    "{date} 移植到 Hermes 技能库。改动范围仅限：frontmatter 改写为 Hermes 规范、技能目录名改为 `{new}`、"
    "兄弟技能的路径与名称引用同步更新、Codex 专有安装件移除（`agents/openai.yaml`、`install_skill.ps1`）。"
    "**正文业务逻辑一字未改**。本机技能根目录 `$SKILLS` = `{root}`；原 Codex 版完整保留在 "
    "`{src}\\{orig}\\`。"
)

FM_TMPL = (
    "---\n"
    "name: {name}\n"
    "description: {description}\n"
    "version: 1.1.0+hermes.1\n"
    "author: star1342354, Hermes Agent\n"
    "license: MIT\n"
    "platforms: {platforms}\n"
    "metadata:\n"
    "  hermes:\n"
    "    tags: {tags}\n"
    "    related_skills: {related}\n"
    "---\n"
)

report: list[str] = []
problems: list[str] = []


def robust_rmtree(path: Path, tries: int = 12, delay: float = 1.0) -> bool:
    """Windows 上目录会被长时间占用（索引/杀软/某进程把它当 cwd）。

    这种情况下 rmdir 永远失败，重试无意义 —— 返回 False，由 sync_tree 改走原地覆盖。
    """
    import time
    last: Exception | None = None
    for _ in range(tries):
        try:
            shutil.rmtree(path)
            return True
        except PermissionError as exc:
            last = exc
            time.sleep(delay)
    print(f"  [提示] 目录被占用无法删除，改为原地覆盖：{path}（{last}）")
    return False


def sync_tree(src: Path, dst: Path) -> None:
    """把 src 同步到 dst：能删就删干净重建，删不掉就原地覆盖（可能残留上游已删文件）。"""
    if dst.exists() and not robust_rmtree(dst):
        print(f"  [提示] {dst.name}/ 用原地覆盖同步，若本次改了文件名请手动清理残留")
    shutil.copytree(src, dst, dirs_exist_ok=True)


def read_raw(path: Path) -> str:
    """3.11 的 Path.read_text 不接受 newline=，用 open 保持行尾原样。"""
    with open(path, encoding="utf-8", newline="") as fh:
        return fh.read()


def write_raw(path: Path, text: str) -> None:
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)


def edit(path: Path, fn):
    """按行尾风格无关的方式改写文件，并保持原 CRLF/LF 风格。"""
    raw = read_raw(path)
    norm = raw.replace("\r\n", "\n")
    out = fn(norm)
    if out is None or out == norm:
        return 0
    write_raw(path, out.replace("\n", "\r\n") if "\r\n" in raw else out)
    return 1


def reloc(orig: str, root: Path) -> None:
    for name, target in ROOT_RELOCATE.get(orig, []):
        src = root / name
        if src.exists():
            dst = root / target
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
            report.append(f"  归位 {name} -> {target}")
    for name in ROOT_DROP.get(orig, []):
        p = root / name
        if p.is_dir():
            if robust_rmtree(p):
                report.append(f"  删除 Codex 专有目录 {name}/")
        elif p.is_file():
            p.unlink()
            report.append(f"  删除 Codex 专有文件 {name}")


def apply_rules(orig: str, root: Path) -> None:
    for pattern, old, new, expect in list(RULES.get(orig, [])) + list(GLOBAL_RULES):
        hits = 0
        for p in sorted(root.glob(pattern)) if pattern.startswith("**/") else sorted(root.rglob(pattern)):
            if "algorithm_library" in str(p):
                continue
            n = p.read_text(encoding="utf-8").replace("\r\n", "\n").count(old)
            if not n:
                continue
            hits += n
            edit(p, lambda t, o=old, w=new: t.replace(o, w))
        if expect is not None and hits != expect:
            problems.append(f"{orig}: 规则 [{old[:38]}…] 期望 {expect} 处，实际 {hits} 处")
        elif hits:
            report.append(f"  改写 {hits} 处：{old[:44]}")


def rewrite_frontmatter(orig: str, new: str, root: Path) -> None:
    p = root / "SKILL.md"
    raw = read_raw(p)
    norm = raw.replace("\r\n", "\n")
    m = re.match(r"^---\n.*?\n---\n", norm, re.DOTALL)
    if not m:
        problems.append(f"{orig}: SKILL.md 找不到可闭合的 frontmatter")
        return
    body = norm[m.end():]
    cfg = FM[new]
    head = FM_TMPL.format(name=new, **cfg)
    note = NOTE.format(orig=orig, new=new, upstream=UPSTREAM, date=PORT_DATE,
                       root=SKILLS_ROOT, src=str(SRC))
    out = head + note + "\n\n" + body
    write_raw(p, out.replace("\n", "\r\n") if "\r\n" in raw else out)
    report.append(f"  frontmatter 重写：name={new}，description {len(cfg['description'])} 字，platforms {cfg['platforms']}")


def patch_fullflow_cli(root: Path) -> None:
    cli = root / "scripts" / "tools" / "cumcm_flow.py"
    if not cli.is_file():
        problems.append("cumcm-fullflow: scripts/tools/cumcm_flow.py 缺失，CLI 未打补丁")
        return

    def patch(text: str) -> str:
        old = "    candidates.append(codex_root / name)\n"
        assert old in text, "_skill_candidates 注入点"
        new = (
            "    candidates.append(codex_root / name)\n"
            "    # Hermes 移植版：技能装在 <hermes>/skills/<分类>/<技能名>；两个中文名技能已重命名。\n"
            '    hermes_root = Path(os.environ.get("HERMES_SKILLS_ROOT",\n'
            '                                       Path.home() / "AppData" / "Local" / "hermes" / "skills"))\n'
            '    hermes_alias = {"数学模型建立": "cumcm-model-build", "数学模型评价": "cumcm-model-review"}\n'
            '    for _category in sorted(hermes_root.glob("*")):\n'
            "        if _category.is_dir():\n"
            "            candidates.append(_category / hermes_alias.get(name, name))\n"
        )
        text = text.replace(old, new, 1)
        text = text.replace("    mismatches: list[str] = []\n", "    mismatches: list[str] = []\n    ported: list[str] = []\n", 1)
        text = text.replace('            mismatches.append(entry["name"])', '            ported.append(entry["name"])', 1)
        old2 = '''    if mismatches:
        return Check("metadata", "fail", "Skill 哈希与安装包元数据不一致", mismatches)'''
        assert old2 in text, "_check_metadata 注入点"
        text = text.replace(
            old2,
            old2 + '''
    if ported:
        return Check("metadata", "warn",
                     "Skill 哈希与上游 Codex 包不一致（Hermes 移植改写了 frontmatter，属预期）", ported)''',
            1,
        )
        old_h = "def _skill_candidates(name: str) -> list[Path]:"
        assert old_h in text, "helper 注入点"
        text = text.replace(old_h, '''def _hermes_skills_root() -> Path:
    """Hermes 移植：技能装在 <hermes>/skills/<分类>/ 下，这里返回 <hermes>/skills。"""
    return Path(os.environ.get(
        "HERMES_SKILLS_ROOT",
        str(Path.home() / "AppData" / "Local" / "hermes" / "skills"),
    ))


def _code_writer_config() -> Path:
    """Hermes 移植：技能装在分类子目录里，靠技能查找结果定位它的 环境配置.json。"""
    for candidate in _skill_candidates("cumcm-code-writer"):
        config = candidate / "环境配置.json"
        if candidate.is_dir() and config.is_file():
            return config
    return Path(".")


def _skill_candidates(name: str) -> list[Path]:''', 1)
        old_hm = '''    hermes_root = Path(os.environ.get("HERMES_SKILLS_ROOT",
                                       Path.home() / "AppData" / "Local" / "hermes" / "skills"))
    hermes_alias = {"数学模型建立": "cumcm-model-build", "数学模型评价": "cumcm-model-review"}
    for _category in sorted(hermes_root.glob("*")):'''
        assert old_hm in text, "hermes_root 注入点"
        text = text.replace(old_hm, '''    hermes_alias = {"数学模型建立": "cumcm-model-build", "数学模型评价": "cumcm-model-review"}
    for _category in sorted(_hermes_skills_root().glob("*")):''', 1)

        old_env = '''def _check_runtime_env(strict: bool = False) -> list[Check]:
    result: list[Check] = []
    for rel, label in (("code_env", "代码计算环境"), ("ocr_env", "OCR/PDF 环境")):
        path = _here() / rel
        if path.is_dir():
            result.append(Check(f"env:{label}", "ok", f"{label}已发现", str(path)))
        else:
            result.append(Check(f"env:{label}", "fail" if strict else "warn",
                                f"{label}未安装；相关阶段首次运行可能需补依赖", str(path)))
    return result'''
        assert old_env in text, "运行时环境检查注入点"
        new_env = '''def _resolve_env_dir(rel: str) -> Path | None:
    """Hermes 移植：环境可装在技能库之外的任意工作区，按 环境变量 → 配置 → 技能库/工具 的顺序找。"""
    if rel == "code_env":
        for key in ("CUMCM_CODE_ENV", "CUMCM_PYTHON", "MODELING_PY"):
            raw = os.environ.get(key)
            if not raw:
                continue
            path = Path(raw).expanduser()
            if path.is_file():
                path = path.parent.parent
            if path.is_dir():
                return path
        for config in (_here() / "环境配置.json",
                       _install_root() / "cumcm-code-writer" / "环境配置.json",
                       _code_writer_config()):
            data = _read_json(config) if config.is_file() else None
            for key in ("code_env", "python"):
                value = (data or {}).get(key)
                if isinstance(value, str) and value.strip():
                    path = Path(value).expanduser()
                    if path.is_file():
                        path = path.parent.parent
                    if path.is_dir():
                        return path
    for root in (_here(), _hermes_skills_root() / "工具"):
        candidate = root / rel
        if candidate.is_dir():
            return candidate
    return None


def _check_runtime_env(strict: bool = False) -> list[Check]:
    result: list[Check] = []
    for rel, label in (("code_env", "代码计算环境"), ("ocr_env", "OCR/PDF 环境")):
        path = _resolve_env_dir(rel)
        if path is not None:
            result.append(Check(f"env:{label}", "ok", f"{label}已发现", str(path)))
        else:
            result.append(Check(f"env:{label}", "fail" if strict else "warn",
                                f"{label}未安装；相关阶段首次运行可能需补依赖",
                                f"未找到 {rel}（可用 CUMCM_CODE_ENV 或 环境配置.json 指定）"))
    return result'''
        text = text.replace(old_env, new_env, 1)

        old_cfg = '        (_install_root() / "cumcm-code-writer" / "环境配置.json", "代码 Skill 环境配置", ("python", "code_env")),\n'
        assert old_cfg in text, "环境配置检查注入点"
        text = text.replace(old_cfg, old_cfg + '        (_code_writer_config(), "代码 Skill 环境配置（Hermes）", ("python", "code_env")),\n', 1)
        report.append("  CLI 补丁：环境定位支持 CUMCM_CODE_ENV/环境配置.json + Hermes 技能库布局")

        old_c = "its skills are split between the local Codex skill\n    directory"
        assert old_c in text, "docstring 宿主指称注入点"
        text = text.replace(old_c, "its skills are split between the local Hermes skill\n    directory", 1)
        old4 = "# Installed/source Codex skills (the four protected execution skills)."
        assert old4 in text, "codex_root 注释注入点"
        text = text.replace(
            old4,
            "# 兼容旧安装：本机若同时装了 Codex 版（~/.codex/skills），也能找到同名技能。",
            1,
        )
        old3 = 'checks.append(Check("host", "info", "独立任务/子代理能力由 Codex 宿主提供，CLI 不替宿主做能力承诺"))'
        assert old3 in text, "host 说明注入点"
        text = text.replace(
            old3,
            'checks.append(Check("host", "info", '
            '"独立任务/子代理能力由 Hermes 宿主提供（delegate_task 子代理），CLI 不替宿主做能力承诺"))',
            1,
        )
        report.append("  CLI 补丁：host 说明由 Codex 宿主改为 Hermes 宿主")
        return text

    try:
        edit(cli, patch)
    except AssertionError as exc:
        problems.append(f"cumcm-fullflow: CLI 补丁失败 —— {exc}")
        return
    report.append("  CLI 补丁：技能查找指向 Hermes 技能库（含重命名别名）+ 移植哈希不一致降级为 warn")


def main() -> int:
    if not SRC.is_dir():
        print(f"源技能目录不存在：{SRC}")
        return 2
    DST.mkdir(parents=True, exist_ok=True)
    print(f"源：{SRC}\n目标：{DST}\n")
    for orig, new in RENAME.items():
        src, dst = SRC / orig, DST / new
        print(f"── {orig} -> {new}")
        sync_tree(src, dst)
        reloc(orig, dst)
        if orig == "cumcm-fullflow":
            tools_dst = dst / "scripts" / "tools"
            sync_tree(TOOLS, tools_dst)
            report.append(f"  内置总指挥 CLI：tools/ -> scripts/tools/（{len(list(tools_dst.iterdir()))} 项）")
        rewrite_frontmatter(orig, new, dst)
        apply_rules(orig, dst)
        if orig == "cumcm-fullflow":
            patch_fullflow_cli(dst)
        for line in report:
            print(line)
        report.clear()
    print("\n════════ 结果 ════════")
    if problems:
        print("发现问题：")
        for p in problems:
            print("  ✗ " + p)
        return 1
    print("全部规则均按预期命中。")
    return 0


if __name__ == "__main__":
    sys.exit(main())