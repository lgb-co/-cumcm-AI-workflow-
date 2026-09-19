"""生成阶段密封交接清单（逐文件 SHA-256），供子代理作为唯一输入依据。

用法：
    python build_handoff.py --stage S4 --run-dir "<运行目录>" [--extra 相对路径 …]
输出：<运行目录>/_handoff/<阶段>_manifest.json

脚本只登记 ``run_dir`` 内的普通文件。所有路径都按“相对、无 ``..``、无
符号链接”处理，避免交接清单意外引用运行目录外的内容。
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path, PurePosixPath, PureWindowsPath


# 每阶段的输入规格：glob 模式 + 角色（evidence / lead）。
# ``_handoff/<stage>_preread.md`` 是有意列出的控制产物，不能被一般的
# _handoff 排除规则吞掉。
SPEC: dict[str, list[tuple[str, str]]] = {
    "S1": [("00_题目/**", "evidence"), ("_handoff/S1_preread.md", "evidence")],
    "S2": [("00_题目/**", "evidence"), ("01_建模方案/**", "evidence"),
           ("_handoff/S2_preread.md", "evidence"), ("00_流程日志.md", "lead")],
    "S2R": [("00_题目/**", "evidence"), ("01_建模方案/**", "evidence"),
            ("_handoff/S2R_preread.md", "evidence"), ("00_流程日志.md", "lead")],
    "S3": [("00_题目/**", "evidence"), ("01_建模方案/**", "evidence")],
    "S4": [("00_题目/**", "evidence"), ("01_建模方案/**", "evidence"),
           ("03_代码/output/**", "evidence"), ("03_代码/work/**", "lead")],
    # S4B 是历史流程中的第二轮代码检测名，保留以兼容已有运行目录。
    "S4B": [("00_题目/**", "evidence"), ("01_建模方案/**", "evidence"),
            ("03_代码/output/**", "evidence"), ("03_代码/work/**", "lead")],
    "S4R": [("00_题目/**", "evidence"), ("01_建模方案/**", "evidence"),
            ("_handoff/S4R_preread.md", "evidence"),
            ("03_代码/output/**", "evidence"), ("04_代码检测/**", "evidence"),
            ("03_代码/work/**", "lead")],
    "S5a": [("00_题目/**", "evidence"), ("01_建模方案/**", "evidence"),
            ("02_方案评审/**", "evidence"), ("04_代码检测/**", "evidence"),
            ("03_代码/output/**/results/**", "evidence"),
            ("03_代码/output/**/tables/**", "evidence"),
            ("03_代码/output/**/figures/**", "evidence"),
            ("03_代码/work/**", "lead")],
    "S5b": [("05_论文/论文正文.md", "evidence")],
    "S5c": [("05_论文/**", "evidence"), ("00_题目/**", "evidence"),
            ("03_代码/output/**/tables/**", "evidence")],
}

STAGES = frozenset(SPEC)
MANIFEST_VERSION = 2
PROTOCOL_VERSION = "1.4"
TOOL_META = {"name": "cumcm-fullflow.build_handoff", "version": "2"}
PREREAD_PATHS = {
    "S1": "_handoff/S1_preread.md",
    "S2": "_handoff/S2_preread.md",
    "S2R": "_handoff/S2R_preread.md",
    "S4R": "_handoff/S4R_preread.md",
}
STAGE_EXCLUDE_PREFIXES = {
    "S4R": (
        "04_代码检测/模型复盘与优化报告",
    ),
    "S5c": (
        "05_论文/_s5c_",
        "05_论文/格式自检表",
        "05_论文/风格体检报告",
        "05_论文/数字一致性报告",
        "05_论文/赛题要求对照_独立复核",
    ),
}

# 每阶段至少要有一组真正的输入。每个内层 tuple 是“前缀候选”集合，
# 外层 tuple 表示必须同时满足的组；例如 S5a 只要求 results/tables/figures
# 三类输出中至少有一类文件。
REQUIRED_GROUPS: dict[str, tuple[tuple[str, ...], ...]] = {
    "S1": (("00_题目/",), ("_handoff/S1_preread.md",)),
    "S2": (("00_题目/",), ("01_建模方案/",), ("_handoff/S2_preread.md",)),
    "S2R": (("00_题目/",), ("01_建模方案/",), ("_handoff/S2R_preread.md",)),
    "S3": (("00_题目/",), ("01_建模方案/",)),
    "S4": (("00_题目/",), ("01_建模方案/",), ("03_代码/output/",)),
    "S4B": (("00_题目/",), ("01_建模方案/",), ("03_代码/output/",)),
    "S4R": (("00_题目/",), ("01_建模方案/",), ("03_代码/output/",),
            ("04_代码检测/",), ("_handoff/S4R_preread.md",)),
    "S5a": (("00_题目/",), ("01_建模方案/",), ("02_方案评审/",),
             ("04_代码检测/",), ("03_代码/output/",)),
    "S5b": (("05_论文/论文正文.md",),),
    "S5c": (("05_论文/",), ("00_题目/",), ("03_代码/output/",)),
}

EXCLUDE_DIRS = frozenset({"__pycache__", ".ipynb_checkpoints", "_stage"})
EXCLUDE_PREFIXES = ("备份_",)


class HandoffError(ValueError):
    """用户输入或运行目录不满足交接契约。"""


def _is_link(path: Path) -> bool:
    """同时识别符号链接与 Windows junction。"""
    return path.is_symlink() or bool(getattr(path, "is_junction", lambda: False)())


def _normalise_rel(value: str, *, label: str = "路径") -> str:
    """返回安全的 POSIX 相对路径/模式；拒绝绝对路径与目录穿越。"""
    if not isinstance(value, str) or not value.strip():
        raise HandoffError(f"{label}不能为空")
    raw = value.replace("\\", "/")
    if "\x00" in raw:
        raise HandoffError(f"{label}含 NUL 字符")
    # PureWindowsPath 能识别 C:\、\\server\share 等 Windows 绝对形式。
    if raw.startswith("/") or PureWindowsPath(raw).is_absolute() or PureWindowsPath(raw).drive:
        raise HandoffError(f"{label}必须是 run_dir 内的相对路径：{value}")
    parts = raw.split("/")
    if any(part in ("..", "") for part in parts):
        raise HandoffError(f"{label}含非法目录组件：{value}")
    parts = [part for part in parts if part != "."]
    if not parts:
        raise HandoffError(f"{label}不能为空")
    return "/".join(parts)


def _normalise_pattern(value: str, *, label: str = "模式") -> str:
    return _normalise_rel(value, label=label)


def _path_has_symlink(path: Path, base: Path) -> bool:
    """检查 base 到 path 的现有组件是否有符号链接。"""
    try:
        rel = path.absolute().relative_to(base.absolute())
    except ValueError:
        return True
    cur = base
    for part in rel.parts:
        cur = cur / part
        try:
            if _is_link(cur):
                return True
        except OSError:
            return True
    return False


def safe_join(base: Path, rel: str, *, must_exist: bool = False) -> Path:
    """把相对路径安全地拼到 base，并拒绝越界/符号链接。"""
    normal = _normalise_rel(rel)
    base = base.resolve()
    candidate = base / Path(*normal.split("/"))
    try:
        resolved = candidate.resolve(strict=False)
        resolved.relative_to(base)
    except (OSError, ValueError) as exc:
        raise HandoffError(f"路径越出 run_dir：{rel}") from exc
    if _path_has_symlink(candidate, base):
        raise HandoffError(f"路径含符号链接，不允许封存：{rel}")
    if must_exist and not candidate.is_file():
        raise HandoffError(f"文件不存在：{rel}")
    return candidate


def _atomic_write(path: Path, data: str) -> None:
    """在同一目录写临时文件并原子替换，避免半截 manifest。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    if _is_link(path):
        raise HandoffError(f"输出文件是符号链接，拒绝覆盖：{path}")
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    finally:
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _excluded(rel: str) -> bool:
    parts = PurePosixPath(rel).parts
    return any(part in EXCLUDE_DIRS or part.startswith(EXCLUDE_PREFIXES) for part in parts)


def _matches_required(rel: str, candidate: str) -> bool:
    return rel == candidate or (candidate.endswith("/") and rel.startswith(candidate))


def _check_required(stage: str, entries: list[dict[str, object]]) -> None:
    rels = [str(e["path"]) for e in entries if e.get("role") == "evidence"]
    missing: list[str] = []
    for group in REQUIRED_GROUPS[stage]:
        if not any(_matches_required(rel, candidate) for rel in rels for candidate in group):
            missing.append(" 或 ".join(group))
    if missing:
        raise HandoffError(f"阶段 {stage} 缺少必需输入：" + "；".join(missing))


def _collect(run: Path, stage: str, extras: list[str]) -> list[dict[str, object]]:
    entries_by_path: dict[str, dict[str, object]] = {}
    specs = list(SPEC[stage])
    extra_patterns: set[str] = set()
    for extra in extras:
        normal_extra = _normalise_pattern(extra, label="--extra")
        extra_patterns.add(normal_extra)
        specs.append((normal_extra, "evidence"))

    for pattern, role in specs:
        pattern = _normalise_pattern(pattern)
        if role not in {"evidence", "lead"}:
            raise HandoffError(f"内部角色非法：{role}")
        if pattern.startswith("_handoff/"):
            allowed = PREREAD_PATHS.get(stage)
            if pattern != allowed:
                raise HandoffError(f"阶段 {stage} 仅允许封存指定 preread：{allowed or '无'}")
        pat = pattern[:-3] + "/**/*" if pattern.endswith("/**") else pattern
        try:
            candidates = sorted(run.glob(pat))
        except (OSError, NotImplementedError) as exc:
            raise HandoffError(f"无法遍历模式 {pattern}：{exc}") from exc
        matched_files = 0
        for candidate in candidates:
            try:
                rel = candidate.relative_to(run).as_posix()
            except ValueError as exc:
                raise HandoffError(f"glob 结果越出 run_dir：{candidate}") from exc
            # 只允许显式列出的 _handoff 文件（尤其是 preread）；普通 glob
            # 或宽泛 --extra 不得把控制清单/回执混入输入。
            if rel.startswith("_handoff/") and not pattern.startswith("_handoff/"):
                continue
            if _excluded(rel) or any(rel.startswith(prefix) for prefix in STAGE_EXCLUDE_PREFIXES.get(stage, ())):
                continue
            if not candidate.is_file():
                continue
            matched_files += 1
            file_path = safe_join(run, rel, must_exist=True)
            item = {"path": rel, "role": role, "bytes": file_path.stat().st_size,
                    "sha256": sha256(file_path)}
            old = entries_by_path.get(rel)
            # evidence 优先于 lead，避免重叠模式把证据降级成线索。
            if old is None or (old.get("role") == "lead" and role == "evidence"):
                entries_by_path[rel] = item

        # --extra 表示调用方明确要求封存的文件；拼写错误不应静默生成
        # 一个看似成功但缺证据的清单。内置 SPEC 的宽泛 glob 则允许为空，
        # 由阶段必需输入组统一判定。
        if pattern in extra_patterns and not matched_files:
            raise HandoffError(f"--extra 未匹配到文件：{pattern}")

    entries = [entries_by_path[key] for key in sorted(entries_by_path)]
    _check_required(stage, entries)
    return entries


def main() -> int:
    ap = argparse.ArgumentParser(description="生成阶段密封交接清单")
    ap.add_argument("--stage", required=True, choices=sorted(STAGES))
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--extra", nargs="*", default=[])
    ap.add_argument("--out")
    args = ap.parse_args()

    try:
        raw_run = Path(args.run_dir).expanduser()
        if _is_link(raw_run):
            raise HandoffError(f"run_dir 不能是符号链接：{raw_run}")
        run = raw_run.resolve()
        if not run.exists() or not run.is_dir():
            raise HandoffError(f"run_dir 不存在或不是目录：{run}")
        if _path_has_symlink(raw_run.absolute(), raw_run.anchor and Path(raw_run.anchor) or raw_run.parent):
            raise HandoffError(f"run_dir 或其现有父路径含符号链接：{run}")
        entries = _collect(run, args.stage, list(args.extra))
        manifest = {
            "manifest_version": MANIFEST_VERSION,
            "protocol_version": PROTOCOL_VERSION,
            "tool": TOOL_META,
            "stage": args.stage,
            "run_dir": str(run),
            "created": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "entries": entries,
            "total_bytes": sum(int(e["bytes"]) for e in entries),
        }
        raw_out = args.out or str(run / "_handoff" / f"{args.stage}_manifest.json")
        raw_out_path = Path(raw_out).expanduser()
        if _is_link(raw_out_path):
            raise HandoffError(f"--out 不能是符号链接：{raw_out_path}")
        out_abs = raw_out_path if raw_out_path.is_absolute() else run / raw_out_path
        if _path_has_symlink(out_abs.absolute(), Path(out_abs.anchor)):
            raise HandoffError(f"--out 路径含符号链接：{raw_out_path}")
        out_abs = out_abs.resolve(strict=False)
        try:
            out_abs.relative_to(run)
        except ValueError as exc:
            raise HandoffError("--out 必须位于 run_dir 内") from exc
        if _path_has_symlink(out_abs.parent, run):
            raise HandoffError(f"输出目录含符号链接：{out_abs.parent}")
        _atomic_write(out_abs, json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    except (HandoffError, OSError) as exc:
        print(f"[交接清单] 不通过：{exc}")
        return 1

    print(f"[交接清单] {args.stage}：{len(entries)} 个文件，{manifest['total_bytes'] / 1024:.0f} KB → {out_abs}")
    for entry in entries[:5]:
        print(f"  - {entry['path'][:60]} ({entry['role']})")
    if len(entries) > 5:
        print(f"  … 其余 {len(entries) - 5} 个文件")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
