# -*- coding: utf-8 -*-
"""把已建好的 Python 运行环境接到 Hermes 版技能上。

为什么需要单独一步：技能里的 `_paths.py` 用 `WORKSPACE_DIR = SKILL_DIR.parent` 定位 `工具/code_env`，
那是 Codex 安装布局（技能与 `工具/` 同级）；在 Hermes 布局下技能装在 `<hermes>/skills/<分类>/`，
所以必须用技能自带的 `环境配置.json` 机制把解释器指过去。

**每次重跑 port_to_hermes.py 之后都要再跑一次本脚本**（移植会重建技能目录，接线文件随之丢失）。

用法：
    python wire_code_env.py                          # 默认取 ./工具/code_env
    python wire_code_env.py "D:/somewhere/工具/code_env"
    python wire_code_env.py "D:/somewhere/工具/code_env/Scripts/python.exe"
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

SKILLS_ROOT = Path(os.environ.get(
    "HERMES_SKILLS_ROOT",
    str(Path.home() / "AppData" / "Local" / "hermes" / "skills"),
))


def resolve_python(raw: str) -> Path:
    path = Path(raw).expanduser()
    if path.is_file():
        return path
    for candidate in (path / "Scripts" / "python.exe", path / "bin" / "python", path / "python.exe"):
        if candidate.is_file():
            return candidate
    raise SystemExit(f"在 {path} 下找不到 python 解释器（给目录或直接给 python.exe 路径）")


def find_skill(name: str) -> Path | None:
    """技能装在哪个分类下都能找到。"""
    for hit in sorted(SKILLS_ROOT.glob(f"*/{name}")):
        if hit.is_dir():
            return hit
    direct = SKILLS_ROOT / name
    return direct if direct.is_dir() else None


def main() -> int:
    raw = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("CUMCM_CODE_ENV", "")
    if not raw:
        default = Path.cwd() / "工具" / "code_env"
        if (default / "Scripts" / "python.exe").is_file() or (default / "bin" / "python").is_file():
            raw = str(default)
        else:
            raise SystemExit(
                "没给解释器路径，也没找到 ./工具/code_env。用法：\n"
                '  python wire_code_env.py "D:/somewhere/工具/code_env"\n'
                '  python wire_code_env.py "D:/somewhere/工具/code_env/Scripts/python.exe"'
            )

    python = resolve_python(raw)
    env_dir = python.parent.parent
    payload = {"python": str(python), "code_env": str(env_dir)}

    # 总指挥 CLI 读 <技能>/scripts/tools/环境配置.json（键 python）
    # 代码技能读 <技能>/环境配置.json（键 code_env / python）
    targets = []
    for skill_name, rel in (("cumcm-code-writer", "环境配置.json"),
                            ("cumcm-fullflow", "scripts/tools/环境配置.json")):
        skill = find_skill(skill_name)
        if skill is None:
            print(f"[跳过] 找不到技能 {skill_name}（技能名与分类可能被改过）")
            continue
        targets.append(skill / rel)

    if not targets:
        raise SystemExit("没有可写入的目标：先确认技能已安装且名字为 cumcm-code-writer / cumcm-fullflow")

    print(f"解释器：{python}")
    print(f"环境根：{env_dir}")
    for target in targets:
        target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"[写入] {target}")

    # 立即回读校验：让脚本自己证明接上了，而不是靠人相信
    ok = True
    for target in targets:
        data = json.loads(target.read_text(encoding="utf-8"))
        hit = Path(data.get("code_env", "")).is_dir() and Path(data.get("python", "")).is_file()
        print(f"[校验] {target.name} → {'可用' if hit else '不可用'}")
        ok = ok and hit
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())