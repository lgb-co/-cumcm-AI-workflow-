# -*- coding: utf-8 -*-
"""CUMCM 工作流的统一命令行入口（stdlib only）。

这个入口只做工程操作：环境体检、运行目录骨架、密封清单、回执校验和
状态读取。它不建模、不写代码、不评审，也不替代 cumcm-fullflow 总指挥。

示例：
    python cumcm_flow.py doctor
    python cumcm_flow.py init "D:\\工作区\\运行\\2026A-题目"
    python cumcm_flow.py seal S1 --run-dir "D:\\工作区\\运行\\2026A-题目"
    python cumcm_flow.py verify S1 --run-dir "D:\\工作区\\运行\\2026A-题目"
    python cumcm_flow.py status "D:\\工作区\\运行\\2026A-题目"
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


VERSION = "1.1.0"
PROTOCOL_VERSION = "1.4"
KNOWN_STAGES = ("S1", "S2", "S2R", "S3", "S4", "S4B", "S4R", "S5a", "S5b", "S5c")
CORE_SKILLS = ("数学模型建立", "数学模型评价", "cumcm-code-writer", "cumcm-code-reviewer")
ALL_SKILLS = CORE_SKILLS + ("cumcm-paper-writer", "cumcm-fullflow")
STAGE_ORDER = ("S1", "S2", "S3", "S4", "S4R", "S5a", "S5b", "S5c")


class CliError(RuntimeError):
    pass


@dataclass
class Check:
    name: str
    status: str  # ok / warn / fail / info
    message: str
    detail: Any = None


def _here() -> Path:
    return Path(__file__).resolve().parent


def _install_root() -> Path:
    """Return the directory that owns an installed ``工具`` folder.

    In a real installation this is ``<skills-root>``.  The source tree also
    contains this CLI, but its skills are split between the local Codex skill
    directory and ``发布/cumcm-pipeline``.  Keeping the installed-root notion
    separate from skill discovery lets ``doctor`` work both before and after
    packaging, without making source-tree paths part of the product.
    """
    return _here().parent


def _skill_candidates(name: str) -> list[Path]:
    """Return possible locations for one skill, in preference order."""
    workspace = _install_root()
    candidates = [workspace / name]
    # Installed/source Codex skills (the four protected execution skills).
    codex_root = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")) / "skills"
    candidates.append(codex_root / name)
    # The published pipeline contains the orchestrator and paper skill.
    candidates.append(workspace / "发布" / "cumcm-pipeline" / "skills" / name)
    # Published standalone copies are useful when running the builder from a
    # clean checkout without first installing the skills into CODEX_HOME.
    aliases = {
        "数学模型建立": workspace / "发布" / "数学模型建立skill" / "数学模型建立",
        "数学模型评价": workspace / "发布" / "数学模型评价skill" / "数学模型评价",
    }
    if name in aliases:
        candidates.append(aliases[name])
    unique: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate.resolve(strict=False)).casefold()
        if key not in seen:
            seen.add(key)
            unique.append(candidate)
    return unique


def _skill_path(name: str) -> Path | None:
    for candidate in _skill_candidates(name):
        if candidate.is_dir() and (candidate / "SKILL.md").is_file():
            return candidate
    return None


def _scripts() -> Path:
    # 开发树布局：总指挥脚本位于发布/cumcm-pipeline/...；安装包布局则把
    # 它们复制进 tools 根目录。优先 sibling，便于安装后 stdlib-only 运行。
    sibling = _here()
    if (sibling / "build_handoff.py").is_file():
        return sibling
    source = _here().parent / "发布" / "cumcm-pipeline" / "skills" / "cumcm-fullflow" / "scripts"
    return source


def _metadata_candidates() -> list[Path]:
    return [
        _here() / "BUILD_METADATA.json",
        _here().parent / "BUILD_METADATA.json",
        _here().parent / "发布" / "cumcm-pipeline" / "BUILD_METADATA.json",
    ]


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _python_candidates() -> list[Path]:
    values: list[str] = []
    for key in ("CUMCM_CODE_ENV", "CUMCM_PYTHON", "MODELING_PY"):
        value = os.environ.get(key)
        if value:
            values.append(value)
    values.append(sys.executable)
    result: list[Path] = []
    for raw in values:
        path = Path(raw).expanduser()
        if path.is_dir():
            for candidate in (path / "Scripts" / "python.exe", path / "bin" / "python", path / "python.exe"):
                if candidate.is_file():
                    result.append(candidate)
        elif path.is_file():
            result.append(path)
    for command in ("python.exe", "python3", "python"):
        found = shutil.which(command)
        if found:
            result.append(Path(found))
    unique: list[Path] = []
    seen: set[str] = set()
    for item in result:
        key = str(item.resolve(strict=False)).casefold()
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique


def _module_available(name: str) -> tuple[bool, str]:
    try:
        spec = importlib.util.find_spec(name)
    except (ImportError, ModuleNotFoundError, ValueError):
        spec = None
    return spec is not None, (getattr(spec, "origin", "") if spec else "")


def _check_python() -> Check:
    version = platform.python_version()
    current = tuple(sys.version_info[:3])
    if current >= (3, 11):
        return Check("python", "ok", f"Python {version}", {"executable": sys.executable})
    return Check("python", "fail", f"Python {version}；本工作流要求 Python 3.11+", {"executable": sys.executable})


def _check_skills() -> list[Check]:
    result: list[Check] = []
    for name in ALL_SKILLS:
        path = _skill_path(name)
        skill = path / "SKILL.md" if path else _install_root() / name / "SKILL.md"
        if path and skill.is_file() and not skill.is_symlink():
            result.append(Check(f"skill:{name}", "ok", "SKILL.md 已就位", str(skill)))
        elif name in CORE_SKILLS:
            result.append(Check(f"skill:{name}", "fail", "核心 Skill 缺少 SKILL.md", str(skill)))
        else:
            result.append(Check(f"skill:{name}", "warn", "可选 Skill 缺少 SKILL.md", str(skill)))
    return result


def _check_tools() -> list[Check]:
    scripts = _scripts()
    required = (("build_handoff.py", scripts), ("verify_receipt.py", scripts),
                ("make_run_dir.py", scripts), ("cumcm_flow.py", _here()))
    result = []
    for name, parent in required:
        path = parent / name
        result.append(Check(f"tool:{name}", "ok" if path.is_file() else "fail",
                            "工具已就位" if path.is_file() else "工具缺失", str(path)))
    return result


def _check_metadata() -> Check:
    metadata_path = next((p for p in _metadata_candidates() if p.is_file()), None)
    if not metadata_path:
        return Check("metadata", "warn", "未找到 BUILD_METADATA.json；可能是开发目录或旧版安装")
    metadata = _read_json(metadata_path)
    if not metadata:
        return Check("metadata", "fail", "BUILD_METADATA.json 不是有效 JSON", str(metadata_path))
    declared = metadata.get("version")
    if not isinstance(declared, str):
        return Check("metadata", "fail", "BUILD_METADATA.json 缺少 version", str(metadata_path))
    if declared != VERSION:
        return Check("metadata", "warn", f"元数据版本 {declared}，当前 CLI {VERSION}（开发目录/旧安装可正常诊断）",
                     str(metadata_path))
    mismatches: list[str] = []
    for entry in metadata.get("skills", []):
        if not isinstance(entry, dict) or not isinstance(entry.get("name"), str):
            continue
        skill_root = _skill_path(entry["name"])
        skill = skill_root / "SKILL.md" if skill_root else _install_root() / entry["name"] / "SKILL.md"
        expected = entry.get("skill_sha256")
        if skill.is_file() and isinstance(expected, str) and _sha256(skill).lower() != expected.lower():
            mismatches.append(entry["name"])
    if mismatches:
        return Check("metadata", "fail", "Skill 哈希与安装包元数据不一致", mismatches)
    return Check("metadata", "ok", f"包版本 {declared}，协议 {metadata.get('protocol_version', '?')}", str(metadata_path))


def _check_modules(strict: bool = False) -> list[Check]:
    required = ("json", "pathlib", "hashlib", "argparse")
    optional_groups = {
        "compute": ("numpy", "pandas", "scipy", "matplotlib", "sklearn", "openpyxl"),
        "document": ("docx", "pypandoc", "lxml"),
    }
    result: list[Check] = []
    for name in required:
        ok, _ = _module_available(name)
        result.append(Check(f"stdlib:{name}", "ok" if ok else "fail", "可导入" if ok else "不可导入"))
    for group, names in optional_groups.items():
        missing = [name for name in names if not _module_available(name)[0]]
        if missing:
            result.append(Check(f"python:{group}", "fail" if strict else "warn",
                                "可选依赖缺少：" + ", ".join(missing), missing))
        else:
            result.append(Check(f"python:{group}", "ok", "常用依赖齐全"))
    return result


def _check_commands() -> list[Check]:
    result: list[Check] = []
    for name, label, severity in (
        ("pandoc", "Pandoc（DOCX/PDF 辅助）", "warn"),
        ("git", "Git（版本追踪，可选）", "warn"),
    ):
        found = shutil.which(name)
        result.append(Check(f"command:{name}", "ok" if found else severity,
                            f"{label}：{found}" if found else f"{label}未找到", found))
    return result


def _check_legacy_paths() -> Check:
    """提示核心 Skill 中仍保留的历史机器路径；核心 Skill 按用户要求不改。"""
    hits: list[str] = []
    patterns = ("D:\\综合处理\\", "D:\\CodexRuntime\\", "C:\\AIplay\\", "C:/", "D:/")
    for name in CORE_SKILLS:
        skill = _skill_path(name)
        if not skill:
            continue
        for path in skill.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in {".py", ".md", ".ps1", ".json"}:
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if any(pattern in text for pattern in patterns):
                try:
                    label = str(path.relative_to(skill.parent))
                except ValueError:
                    label = str(path)
                hits.append(f"{name}/{label}")
    if hits:
        return Check("legacy-paths", "warn", "核心 Skill 保留历史机器路径示例；运行时请以环境配置/doctor 为准", hits[:20])
    return Check("legacy-paths", "ok", "未发现常见历史机器路径")


def _check_runtime_env(strict: bool = False) -> list[Check]:
    result: list[Check] = []
    for rel, label in (("code_env", "代码计算环境"), ("ocr_env", "OCR/PDF 环境")):
        path = _here() / rel
        if path.is_dir():
            result.append(Check(f"env:{label}", "ok", f"{label}已发现", str(path)))
        else:
            result.append(Check(f"env:{label}", "fail" if strict else "warn",
                                f"{label}未安装；相关阶段首次运行可能需补依赖", str(path)))
    return result


def _check_environment_config(strict: bool = False) -> list[Check]:
    """Detect stale absolute interpreter paths written by an older machine."""
    result: list[Check] = []
    candidates = (
        (_here() / "环境配置.json", "工具环境配置", ("python",)),
        (_install_root() / "cumcm-code-writer" / "环境配置.json", "代码 Skill 环境配置", ("python", "code_env")),
    )
    for path, label, keys in candidates:
        if not path.is_file():
            result.append(Check(f"config:{label}", "info", f"未发现{label}（可由安装器在本机生成）", str(path)))
            continue
        data = _read_json(path)
        configured = next((data.get(key) for key in keys if data and isinstance(data.get(key), str)), None)
        if not isinstance(configured, str) or not configured.strip():
            result.append(Check(f"config:{label}", "warn" if strict else "info",
                                f"{label}未记录 Python 路径", str(path)))
            continue
        python_path = Path(configured).expanduser()
        if python_path.is_file():
            result.append(Check(f"config:{label}", "ok", f"{label}中的 Python 路径存在", str(python_path)))
        else:
            result.append(Check(f"config:{label}", "fail" if strict else "warn",
                                f"{label}中的 Python 路径已失效；请重跑安装器或设置 CUMCM_PYTHON", str(python_path)))
    return result


def _check_write() -> Check:
    parent = _install_root()
    try:
        with tempfile.NamedTemporaryFile(prefix=".cumcm-doctor-", dir=str(parent), delete=True):
            pass
    except OSError as exc:
        return Check("write", "fail", f"安装根目录不可写：{exc}", str(parent))
    return Check("write", "ok", "安装根目录可写", str(parent))


def _check_network() -> Check:
    request = urllib.request.Request("https://pypi.org/", method="HEAD", headers={"User-Agent": "cumcm-flow-doctor"})
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return Check("network", "ok", f"网络可达（HTTP {response.status}）")
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return Check("network", "warn", f"网络不可达；联网查证/首次依赖安装可能受限：{exc}")


def run_doctor(strict: bool = False, network: bool = False) -> list[Check]:
    checks: list[Check] = [_check_python()]
    checks.extend(_check_skills())
    checks.extend(_check_tools())
    checks.append(_check_metadata())
    checks.extend(_check_modules(strict))
    checks.extend(_check_commands())
    checks.append(_check_legacy_paths())
    checks.extend(_check_runtime_env(strict))
    checks.extend(_check_environment_config(strict))
    checks.append(_check_write())
    checks.append(Check("host", "info", "独立任务/子代理能力由 Codex 宿主提供，CLI 不替宿主做能力承诺"))
    if network:
        checks.append(_check_network())
    return checks


def _print_checks(checks: Iterable[Check], as_json: bool = False) -> int:
    items = [asdict(item) for item in checks]
    failures = sum(item["status"] == "fail" for item in items)
    if as_json:
        print(json.dumps({"version": VERSION, "protocol_version": PROTOCOL_VERSION,
                          "ok": failures == 0, "checks": items}, ensure_ascii=False, indent=2))
    else:
        print(f"cumcm-flow {VERSION} · 环境体检")
        for item in items:
            mark = {"ok": "OK", "warn": "WARN", "fail": "FAIL", "info": "INFO"}[item["status"]]
            print(f"[{mark:<4}] {item['name']}: {item['message']}")
        print("结果：" + ("通过" if failures == 0 else f"有 {failures} 项硬失败"))
    return 1 if failures else 0


def _load_script(name: str):
    path = _scripts() / name
    if not path.is_file():
        raise CliError(f"找不到工具脚本：{path}")
    spec = importlib.util.spec_from_file_location(f"cumcm_flow_{name[:-3]}", path)
    if not spec or not spec.loader:
        raise CliError(f"无法加载工具脚本：{path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run_script(name: str, args: list[str]) -> int:
    path = _scripts() / name
    if not path.is_file():
        raise CliError(f"找不到工具脚本：{path}")
    env = os.environ.copy()
    env.setdefault("PYTHONUTF8", "1")
    completed = subprocess.run([sys.executable, str(path), *args], env=env)
    return int(completed.returncode)


def _stage(value: str) -> str:
    upper = value.upper()
    if upper not in KNOWN_STAGES:
        raise CliError(f"未知阶段 {value!r}；可选：{', '.join(KNOWN_STAGES)}")
    return upper


def command_init(args: argparse.Namespace) -> int:
    command = [args.run_dir]
    if args.reset:
        command.append("--reset")
    return _run_script("make_run_dir.py", command)


def command_seal(args: argparse.Namespace) -> int:
    command = ["--stage", _stage(args.stage), "--run-dir", args.run_dir]
    if args.extra:
        command.extend(["--extra", *args.extra])
    if args.out:
        command.extend(["--out", args.out])
    return _run_script("build_handoff.py", command)


def command_verify(args: argparse.Namespace) -> int:
    stage = _stage(args.stage)
    run = Path(args.run_dir).expanduser()
    manifest = args.manifest or str(run / "_handoff" / f"{stage}_manifest.json")
    receipt = args.receipt or str(run / "_handoff" / f"{stage}_receipt.json")
    return _run_script("verify_receipt.py", ["--manifest", manifest, "--receipt", receipt, "--base", str(run)])


def _status(run: Path) -> dict[str, Any]:
    handoff = run / "_handoff"
    receipts: list[dict[str, Any]] = []
    if handoff.is_dir():
        for path in sorted(handoff.glob("*_receipt.json")):
            data = _read_json(path)
            if data:
                receipts.append({"stage": data.get("stage", path.stem.replace("_receipt", "")),
                                 "status": data.get("status", "未知"),
                                 "unresolved": data.get("unresolved", []),
                                 "path": str(path)})
    by_stage = {str(item["stage"]): item for item in receipts}
    completed = [stage for stage in STAGE_ORDER if str(by_stage.get(stage, {}).get("status", "")).startswith("完成")]
    next_stage = next((stage for stage in STAGE_ORDER if stage not in completed), None)
    return {"run_dir": str(run), "exists": run.is_dir(), "completed": completed,
            "next_stage": next_stage, "receipts": receipts,
            "handoff_dir": str(handoff), "updated_at": datetime.now(timezone.utc).isoformat()}


def command_status(args: argparse.Namespace) -> int:
    run = Path(args.run_dir).expanduser().resolve()
    data = _status(run)
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(f"运行目录：{data['run_dir']}")
        print("已完成：" + ("、".join(data["completed"]) or "无"))
        print("建议下一阶段：" + (data["next_stage"] or "无（请检查回执或流程日志）"))
        for item in data["receipts"]:
            unresolved = item.get("unresolved") or []
            suffix = f"；未决 {len(unresolved)} 项" if isinstance(unresolved, list) and unresolved else ""
            print(f"  {item['stage']}: {item['status']}{suffix}")
    return 0 if data["exists"] else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cumcm-flow", description="CUMCM 工作流工程命令行入口（不产出专业内容）")
    parser.add_argument("--version", action="version", version=f"cumcm-flow {VERSION} (protocol {PROTOCOL_VERSION})")
    sub = parser.add_subparsers(dest="command", required=True)

    doctor = sub.add_parser("doctor", help="检查陌生机器上的 Python、Skill、工具和可选依赖")
    doctor.add_argument("--json", action="store_true", help="以 JSON 输出")
    doctor.add_argument("--strict", action="store_true", help="严格模式（可选计算/文档/OCR 依赖缺失也算失败）")
    doctor.add_argument("--network", action="store_true", help="额外测试 pypi.org 网络连通性")

    init = sub.add_parser("init", help="建立运行目录骨架")
    init.add_argument("run_dir")
    init.add_argument("--reset", action="store_true")

    seal = sub.add_parser("seal", help="生成阶段密封交接清单")
    seal.add_argument("stage", help="阶段，例如 S1、S2R、S5c")
    seal.add_argument("--run-dir", required=True)
    seal.add_argument("--extra", nargs="*", default=[])
    seal.add_argument("--out")

    verify = sub.add_parser("verify", help="校验阶段回执")
    verify.add_argument("stage", help="阶段，例如 S1、S2R、S5c")
    verify.add_argument("--run-dir", required=True)
    verify.add_argument("--manifest")
    verify.add_argument("--receipt")

    status = sub.add_parser("status", help="读取运行目录的结构化阶段状态")
    status.add_argument("run_dir")
    status.add_argument("--json", action="store_true")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "doctor":
            return _print_checks(run_doctor(args.strict, args.network), args.json)
        if args.command == "init":
            return command_init(args)
        if args.command == "seal":
            return command_seal(args)
        if args.command == "verify":
            return command_verify(args)
        if args.command == "status":
            return command_status(args)
        parser.error(f"未知命令：{args.command}")
    except (CliError, OSError, subprocess.SubprocessError) as exc:
        print(f"cumcm-flow：{exc}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
