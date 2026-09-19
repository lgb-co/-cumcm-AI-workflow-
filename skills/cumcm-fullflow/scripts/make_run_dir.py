#!/usr/bin/env python3
"""建立（或重置）一次数模全流程运行目录。

用法:
    python make_run_dir.py "D:\\工作区\\运行\\2026A-药材的烘干问题"
    python make_run_dir.py "<运行目录>" --reset      # 旧目录整体移入 _回收站

``--reset`` 不会删除文件：旧运行目录被移动到 ``<工作区>\\_回收站``，
并且所有目录/日志写入都拒绝符号链接与不安全路径。
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path

SUBDIRS = [
    "00_题目",
    "01_建模方案",
    "02_方案评审",
    "03_代码",
    "04_代码检测",
    "05_论文",
    "交付",
    "_handoff",
]

LOG_NAME = "00_流程日志.md"
LOG_HEADER = (
    "# 流程日志\n\n"
    "> 由 cumcm-fullflow 维护：每阶段结束追加一行，重跑时先看本文件判断上游产物能否复用。\n\n"
    "| 时间 | 阶段 | 产物路径 | 结论 | 未决项 |\n"
    "|---|---|---|---|---|\n"
)
RESERVED_NAMES = {"运行", "_回收站"}


class RunDirError(ValueError):
    pass


def _is_link(path: Path) -> bool:
    """同时识别符号链接与 Windows junction。"""
    return path.is_symlink() or bool(getattr(path, "is_junction", lambda: False)())


def _path_has_symlink(path: Path) -> bool:
    """检查 path 的现有组件是否为符号链接（不跟随链接）。"""
    absolute = path.absolute()
    try:
        cur = Path(absolute.anchor)
        rel = absolute.relative_to(cur)
    except (ValueError, OSError):
        return True
    for part in rel.parts:
        cur = cur / part
        try:
            if _is_link(cur):
                return True
        except OSError:
            return True
    return False


def _resolve_run_dir(raw: str) -> Path:
    if not isinstance(raw, str) or not raw.strip():
        raise RunDirError("运行目录不能为空")
    original = Path(raw).expanduser()
    if _is_link(original):
        raise RunDirError(f"运行目录不能是符号链接：{original}")
    absolute = original.absolute()
    if absolute == Path(absolute.anchor):
        raise RunDirError("拒绝把文件系统根目录作为运行目录")
    if absolute.name in RESERVED_NAMES:
        raise RunDirError(f"拒绝把保留目录作为运行目录：{absolute}")
    if _path_has_symlink(absolute):
        raise RunDirError(f"运行目录路径含符号链接：{absolute}")
    resolved = absolute.resolve(strict=False)
    if resolved == Path(resolved.anchor) or resolved.name in RESERVED_NAMES:
        raise RunDirError(f"运行目录解析后不安全：{resolved}")
    return resolved


def trash_root(run_dir: Path) -> Path:
    """运行目录通常是 <工作区>/运行/<项目>，回收站放在 <工作区>/_回收站。"""
    run_dir = run_dir.resolve()
    root = run_dir.parent.parent / "_回收站" if run_dir.parent.name == "运行" else run_dir.parent / "_回收站"
    if root.name in RESERVED_NAMES and root == run_dir:
        raise RunDirError("回收站不能与运行目录相同")
    if _path_has_symlink(root):
        raise RunDirError(f"回收站路径含符号链接：{root}")
    return root


def reset(run_dir: Path) -> Path | None:
    if run_dir.parent.name != "运行":
        raise RunDirError("--reset 只允许作用于 <工作区>\\运行\\<项目> 目录")
    if not run_dir.exists():
        return None
    if _is_link(run_dir) or not run_dir.is_dir():
        raise RunDirError(f"待重置路径不是普通目录：{run_dir}")
    if _path_has_symlink(run_dir):
        raise RunDirError(f"待重置目录路径含符号链接：{run_dir}")
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    root = trash_root(run_dir)
    target_parent = root.resolve(strict=False)
    target_parent.mkdir(parents=True, exist_ok=True)
    if _path_has_symlink(target_parent):
        raise RunDirError(f"回收站目录含符号链接：{target_parent}")
    target = target_parent / f"{run_dir.name}_{stamp}"
    if target.exists() or _is_link(target):
        print(f"ABORT: 回收站目标已存在 {target}", file=sys.stderr)
        raise RunDirError(f"回收站目标已存在：{target}")
    try:
        target.resolve(strict=False).relative_to(target_parent)
    except ValueError as exc:
        raise RunDirError("回收站目标越出回收站目录") from exc
    shutil.move(str(run_dir), str(target))
    print(f"MOVED  {run_dir}  ->  {target}")
    return target


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if _is_link(path):
        raise RunDirError(f"拒绝覆盖符号链接：{path}")
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    finally:
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass


def _ensure_dir(path: Path) -> None:
    if _is_link(path):
        raise RunDirError(f"目录不能是符号链接：{path}")
    path.mkdir(parents=True, exist_ok=True)
    if not path.is_dir() or _is_link(path):
        raise RunDirError(f"无法建立普通目录：{path}")
    if _path_has_symlink(path):
        raise RunDirError(f"目录路径含符号链接：{path}")


def main() -> int:
    ap = argparse.ArgumentParser(description="建立或重置数模全流程运行目录")
    ap.add_argument("run_dir", help="运行目录，例如 <工作区>\\运行\\2026A-药材的烘干问题")
    ap.add_argument("--reset", action="store_true", help="把已存在的运行目录整体移入 _回收站 后重建")
    args = ap.parse_args()

    try:
        run_dir = _resolve_run_dir(args.run_dir)
        if args.reset:
            reset(run_dir)
        elif run_dir.exists():
            if not run_dir.is_dir():
                raise RunDirError(f"路径已存在但不是目录：{run_dir}")
            print(f"NOTE: 目录已存在，保留原内容，只补齐缺失骨架: {run_dir}")

        _ensure_dir(run_dir)
        for name in SUBDIRS:
            _ensure_dir(run_dir / name)

        log = run_dir / LOG_NAME
        if _is_link(log):
            raise RunDirError(f"流程日志不能是符号链接：{log}")
        if not log.exists():
            _atomic_write(log, LOG_HEADER)
    except (RunDirError, OSError, shutil.Error) as exc:
        print(f"ABORT: {exc}", file=sys.stderr)
        return 1

    print(f"RUN_DIR {run_dir}")
    for name in SUBDIRS:
        print(f"  - {name}")
    print(f"  - {LOG_NAME}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
