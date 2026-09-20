# -*- coding: utf-8 -*-
"""验证 Hermes 移植结果：frontmatter 合法性 / 残留 Codex 痕迹 / 引用一致性。"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

import yaml

DST = Path(os.environ.get(
    "HERMES_SKILLS_ROOT",
    str(Path.home() / "AppData" / "Local" / "hermes" / "skills" / "research"),
))
NAMES = ["cumcm-model-build", "cumcm-model-review", "cumcm-code-writer",
         "cumcm-code-reviewer", "cumcm-paper-writer", "cumcm-fullflow"]
# 环境配置.json 是 wire_code_env.py 写进去的本机接线（_paths.py 读 SKILL_DIR/环境配置.json），属正常项
ALLOWED_TOP = {"SKILL.md", "环境配置.json", "references", "scripts", "templates", "assets"}

fail: list[str] = []
warn: list[str] = []
print("═══ 1) frontmatter 合法性（对齐 Hermes 校验器要求）═══")
for name in NAMES:
    d = DST / name
    skill = d / "SKILL.md"
    if not skill.is_file():
        fail.append(f"{name}: SKILL.md 缺失")
        continue
    raw = skill.read_bytes().decode("utf-8")
    if not raw.startswith("---"):
        fail.append(f"{name}: 未以 --- 开头")
        continue
    m = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n(.*)$", raw, re.DOTALL)
    if not m:
        fail.append(f"{name}: frontmatter 未闭合")
        continue
    fm, body = m.group(1), m.group(2)
    try:
        meta = yaml.safe_load(fm)
    except Exception as exc:
        fail.append(f"{name}: YAML 解析失败 {exc}")
        continue
    if meta.get("name") != name:
        fail.append(f"{name}: frontmatter name={meta.get('name')!r} 与目录名不一致")
    desc = meta.get("description", "")
    if not desc:
        fail.append(f"{name}: description 为空")
    elif len(desc) > 60:
        fail.append(f"{name}: description 超 60 字（{len(desc)}）")
    elif not desc.endswith("。"):
        warn.append(f"{name}: description 未以。结尾")
    if not meta.get("platforms"):
        fail.append(f"{name}: 缺 platforms")
    for k in ("version", "author", "license"):
        if not meta.get(k):
            warn.append(f"{name}: 缺 {k}")
    if not meta.get("metadata", {}).get("hermes", {}).get("tags"):
        warn.append(f"{name}: 缺 metadata.hermes.tags")
    if not body.strip():
        fail.append(f"{name}: 正文为空")
    extra = sorted(p.name for p in d.iterdir() if p.name not in ALLOWED_TOP)
    if extra:
        warn.append(f"{name}: 根目录非常规项 {extra}")
    print(f"  ✓ {name:20s} name/desc({len(desc)}字)/platforms={'/'.join(meta['platforms'])}")
    print(f"      desc: {desc}")
    print(f"      tags: {meta['metadata']['hermes']['tags']}  body {len(body)} 字  "
          f"顶层: {sorted(p.name for p in d.iterdir())}")

def classify(rel: str, line_text: str) -> str:
    """把命中分成 expected（移植说明/上游归档/兼容分支）与 real（真依赖）。"""
    if rel.startswith("references\\_上游") or rel.startswith("_上游"):
        return "expected:上游归档件（原样保留的 Codex 文档）"
    if "移植说明（Hermes 版）" in line_text or "兼容旧安装" in line_text:
        return "expected:移植说明/CLI 兼容分支在说明被移除或保留的旧路径"
    if rel.endswith("风格来源.md") and ("openai.yaml" in line_text or "Codex" in line_text):
        return "expected:上游在讲各 Agent 对 SKILL.md 的支持（行文举例）"
    return "real"


print("\n═══ 2) 残留 Codex 痕迹（expected = 有意保留，real = 真依赖）═══")
patterns = {
    r"\$CODEX_HOME": "CODEX_HOME 变量",
    r"~/\.codex": "~/.codex 路径",
    r"~\\\.codex": "~/.codex 路径(反斜杠)",
    r"工具[\\/]cumcm-flow": "旧 CLI 相对路径",
    r"\.codex[\\/]skills": ".codex/skills",
    r"install_skill\.ps1": "已删的安装脚本",
    r"openai\.yaml": "Codex 代理清单",
}
for name in NAMES:
    hits = []
    for p in (DST / name).rglob("*"):
        if not p.is_file() or p.suffix.lower() in {".pyc", ".png", ".jpg", ".docx", ".pdf"}:
            continue
        if "algorithm_library" in str(p):
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pat, label in patterns.items():
            for mm in re.finditer(pat, text):
                ln = text[:mm.start()].count("\n") + 1
                line_text = text.splitlines()[ln - 1] if ln - 1 < len(text.splitlines()) else ""
                rel = str(p.relative_to(DST / name))
                kind = classify(rel, line_text)
                hits.append((kind, f"{rel}:{ln} {label}"))
    real = [h for k, h in hits if k == "real"]
    exp = [t for t in hits if t[0] != "real"]
    if real:
        fail.extend(real)
    for h in real:
        print(f"  ✗ {name}: 真依赖 {h}")
    for k, h in exp:
        print(f"  · {name}: {h}　— {k.split(':')[1]}")
    if not real:
        print(f"  ✓ {name}: 无真依赖残留（有意保留 {len(exp)} 处）")

print("\n═══ 2b) 宿主错称（正文里把宿主写成 Codex 的残留）═══")
# 有意保留：上游归档件、上游对各 Agent 的行文举例、历史机器路径、运行时缓存目录、CLI 的兼容分支。
HOST_ALLOW_SUBSTR = [
    "综合处理", "CodexRuntime", "codex-runtimes", "CodexResearch/1.0",
    "CODEX_HOME", "codex_root", "上游 Codex", "旧 Codex", "Codex 版", "兼容旧安装",
    "移植说明",
]
HOST_SKIP_PATH = ("_上游", "风格来源.md")
host_hits: list[str] = []
for name in NAMES:
    for p2 in (DST / name).rglob("*"):
        if not p2.is_file() or p2.suffix.lower() in {".pyc", ".png", ".jpg", ".docx", ".pdf"}:
            continue
        rel = str(p2.relative_to(DST / name))
        if "algorithm_library" in rel or any(s in rel for s in HOST_SKIP_PATH):
            continue
        try:
            text = p2.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for m3 in re.finditer(r"[Cc]odex", text):
            ln = text[:m3.start()].count("\n") + 1
            line = text.splitlines()[ln - 1]
            if any(s in line for s in HOST_ALLOW_SUBSTR):
                continue
            host_hits.append(f"{rel}:{ln} {line.strip()[:90]}")
if host_hits:
    fail.extend("宿主错称：" + h for h in host_hits)
    print(f"  ✗ 残留 {len(host_hits)} 处")
    for h in host_hits:
        print(f"      {h}")
else:
    print("  ✓ 无宿主错称（历史机器路径/缓存目录/上游归档不算）")

print("\n═══ 3) 兄弟技能引用一致性 ═══")
for name in NAMES:
    stale = []
    for p in (DST / name).rglob("*.md"):
        try:
            text = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        lines = text.splitlines()
        for m2 in re.finditer(r"数学模型建立|数学模型评价|代码编写评价", text):
            ln = text[:m2.start()].count("\n") + 1
            line_text = lines[ln - 1] if ln - 1 < len(lines) else ""
            if "移植说明（Hermes 版）" in line_text or "本技能原为 Codex 技能" in line_text:
                continue  # 移植说明里保留原名，是文档而非引用
            if line_text.lstrip().startswith("#"):
                continue  # 标题（含中文原名+ASCII 名），有意保留
            if "文件夹" in line_text or "创建 `数学模型评价`" in line_text:
                continue  # 运行期产物文件夹名，必须保持
            before = text[max(0, m2.start() - 30):m2.start()]
            after = text[m2.end():m2.end() + 30]
            stale.append(f"{p.relative_to(DST / name)}:{ln} …{before}【{m2.group()}】{after}…")
    tag = "✓" if not stale else "✗"
    if stale:
        fail.extend("旧名引用未更新：" + s for s in stale)
    print(f"  {tag} {name}: 中文旧名残留 {len(stale)} 处")
    for s in stale:
        print(f"      {s}")

print("\n═══ 4) 运行期产物名是否被误改 ═══")
for rel, needle in [("cumcm-model-review/scripts/review.py", '"数学模型评价"'),
                    ("cumcm-model-review/SKILL.md", "名为 `数学模型评价` 的文件夹")]:
    p = DST / rel
    ok = p.is_file() and needle in p.read_text(encoding="utf-8")
    print(f"  {'✓' if ok else '✗'} {rel} 保留 {needle}")
    if not ok:
        fail.append(f"{rel} 丢失运行期产物名 {needle}")

print("\n═══ 结果 ═══")
print(f"fail={len(fail)} warn={len(warn)}")
for w in warn:
    print("  ⚠ " + w)
for f in fail:
    print("  ✗ " + f)
sys.exit(1 if fail else 0)