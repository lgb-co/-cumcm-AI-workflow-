"""校验阶段回执：产物、输入哈希、路径安全与阶段契约。

用法：
    python verify_receipt.py --manifest _handoff/S4_manifest.json \
        --receipt _handoff/S4_receipt.json --base <运行目录>

退出码 0 = 通过；1 = 不通过（原因打印在标准输出）。旧版 manifest（没有
``manifest_version``）仍按兼容模式读取，但路径穿越、符号链接和未知阶段始终
拒绝。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from pathlib import Path, PurePosixPath, PureWindowsPath

# Windows 控制台默认 GBK，回执里的 −、≈ 等字符会导致打印崩溃。
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # pragma: no cover
    pass


REQUIRED = ("stage", "status", "artifacts", "unresolved")
NEED_REPRO = {"S2", "S2R", "S4", "S4B", "S4R", "S5c"}
KNOWN_STAGES = {"S1", "S2", "S2R", "S3", "S4", "S4B", "S4R", "S5a", "S5b", "S5c"}
REREAD_STAGES = {"S1", "S2", "S2R", "S4", "S4B", "S4R", "S5c"}
HEX64 = re.compile(r"^[0-9a-fA-F]{64}$")
CURRENT_PROTOCOL = (1, 4)
PREREAD_REQUIRED_STAGES = {"S1", "S2", "S2R", "S4R"}
PREREQUISITES: dict[str, tuple[tuple[str, ...], ...]] = {
    "S1": (),
    "S2": (("S1",),),
    "S2R": (("S1",), ("S2",)),
    "S3": (("S2", "S2R"),),
    "S4": (("S3",),),
    "S4B": (("S4",),),
    "S4R": (("S4", "S4B"),),
    "S5a": (("S4R",),),
    "S5b": (("S5a",),),
    "S5c": (("S5b",),),
}

# 与 build_handoff.py 保持同一套阶段输入门槛。旧 manifest 只跳过包含 preread
# 的组，以免破坏 1.0.1 已封存的运行；新 manifest（version=2）全部强制。
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


class ReceiptError(ValueError):
    pass


def _is_link(path: Path) -> bool:
    """同时识别符号链接与 Windows junction。"""
    return path.is_symlink() or bool(getattr(path, "is_junction", lambda: False)())


def _normalise_rel(value: object, *, label: str = "路径") -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReceiptError(f"{label}不能为空")
    raw = value.replace("\\", "/")
    if "\x00" in raw:
        raise ReceiptError(f"{label}含 NUL 字符")
    if raw.startswith("/") or PureWindowsPath(raw).is_absolute() or PureWindowsPath(raw).drive:
        raise ReceiptError(f"{label}必须是 run_dir 内的相对路径：{value}")
    parts = raw.split("/")
    if any(part in ("", "..") for part in parts):
        raise ReceiptError(f"{label}含非法目录组件：{value}")
    parts = [part for part in parts if part != "."]
    if not parts:
        raise ReceiptError(f"{label}不能为空")
    return "/".join(parts)


def _path_has_symlink(path: Path, base: Path) -> bool:
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


def safe_join(base: Path, rel: object, *, must_exist: bool = False) -> Path:
    """安全拼接相对路径，拒绝越界、符号链接和非普通文件。"""
    normal = _normalise_rel(rel)
    base = base.resolve()
    if _is_link(base):
        raise ReceiptError("base/run_dir 不能是符号链接")
    candidate = base / Path(*normal.split("/"))
    try:
        candidate.resolve(strict=False).relative_to(base)
    except (OSError, ValueError) as exc:
        raise ReceiptError(f"路径越出 run_dir：{rel}") from exc
    if _path_has_symlink(candidate, base):
        raise ReceiptError(f"路径含符号链接：{rel}")
    if must_exist and (not candidate.is_file() or _is_link(candidate)):
        raise ReceiptError(f"文件不存在或不是普通文件：{rel}")
    return candidate


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _version(value: object) -> tuple[int, ...] | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        value = str(value)
    if not isinstance(value, str):
        return None
    try:
        parts = tuple(int(x) for x in value.strip().split("."))
    except ValueError:
        return None
    return parts if parts else None


def _is_blocking_unresolved(value: str) -> bool:
    """协议 1.4 下，完成回执不允许把阻塞级问题藏在 unresolved。"""
    text = value.casefold()
    return any(token in text for token in (
        "p0", "p1", "critical", "阻塞", "需返工", "未通过", "不通过", "待修复",
    ))


def _pass_value(value: object) -> bool:
    if value is True:
        return True
    if isinstance(value, str):
        return value.strip().casefold() in {
            "pass", "passed", "ok", "true", "通过", "已通过", "合格", "完成",
        }
    return False


def _validate_gate(stage: str, receipt: dict[str, object], strict14: bool,
                   problems: list[str]) -> None:
    """检查新协议的阶段门禁；兼容 gate/gates 两种历史写法。"""
    if not strict14:
        return
    raw = receipt.get("gate")
    if raw is None:
        raw = receipt.get("gates")
    if not isinstance(raw, dict):
        problems.append("protocol 1.4 回执必须提供 gate（或 gates）对象")
        return
    status = raw.get("status", raw.get("result", raw.get("decision", raw.get("passed"))))
    if not _pass_value(status):
        problems.append(f"阶段 {stage} 的 gate 未通过：{status!r}")
    for key in ("p0", "p1", "open_p1", "blocking"):
        if key not in raw:
            continue
        value = raw[key]
        if key in {"p0", "p1", "open_p1"}:
            if not _is_int(value) or value != 0:
                problems.append(f"gate.{key} 必须为 0（实际 {value!r}）")
        elif value not in (False, 0, None, "0", "无"):
            problems.append(f"gate.{key} 仍表示有阻塞项：{value!r}")
    if stage in {"S4", "S4B", "S4R"}:
        for key in ("p0", "open_p1"):
            if key not in raw:
                problems.append(f"阶段 {stage} 的 gate.{key} 必填（代码合格门禁）")


def _read_json(path: Path, label: str) -> dict[str, object]:
    if not path.is_file() or _is_link(path):
        raise ReceiptError(f"{label}不存在或是符号链接：{path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ReceiptError(f"{label}不是有效 UTF-8 JSON：{exc}") from exc
    if not isinstance(value, dict):
        raise ReceiptError(f"{label}顶层必须是 JSON 对象")
    return value


def _input_path(base: Path, value: str, label: str) -> Path:
    """CLI 路径可为绝对路径，或以 run_dir 为基准的相对路径。"""
    raw = Path(value).expanduser()
    candidate = raw if raw.is_absolute() else base / raw
    if _path_has_symlink(candidate.absolute(), Path(candidate.anchor)):
        raise ReceiptError(f"{label} 路径含符号链接：{candidate}")
    try:
        candidate.resolve(strict=False).relative_to(base)
    except (ValueError, OSError) as exc:
        raise ReceiptError(f"{label} 必须位于 base/run_dir 内：{candidate}") from exc
    return candidate


def _match(rel: str, candidate: str) -> bool:
    return rel == candidate or (candidate.endswith("/") and rel.startswith(candidate))


def _validate_manifest(manifest: dict[str, object], base: Path, problems: list[str], notes: list[str]) -> tuple[int, list[dict[str, object]]]:
    stage = manifest.get("stage")
    stage_known = isinstance(stage, str) and stage in KNOWN_STAGES
    if not stage_known:
        problems.append(f"清单阶段未知或缺失：{stage!r}")
    version_raw = manifest.get("manifest_version", 1)
    if not _is_int(version_raw) or version_raw < 1 or version_raw > 2:
        problems.append(f"不支持的 manifest_version：{version_raw!r}")
        version = 1
    else:
        version = int(version_raw)

    manifest_protocol = _version(manifest.get("protocol_version"))
    if version >= 2:
        if manifest_protocol is None or manifest_protocol < CURRENT_PROTOCOL:
            problems.append("v2 manifest 必须声明 protocol_version >= 1.4")
        tool = manifest.get("tool")
        if not isinstance(tool, dict) or not isinstance(tool.get("name"), str) or not tool.get("name"):
            problems.append("v2 manifest 缺少 tool.name 元数据")
        if not isinstance(tool, dict) or not isinstance(tool.get("version"), str) or not tool.get("version"):
            problems.append("v2 manifest 缺少 tool.version 元数据")

    declared_run = manifest.get("run_dir")
    if version >= 2 and not declared_run:
        problems.append("v2 manifest 必须声明 run_dir")
    if declared_run:
        try:
            if Path(str(declared_run)).expanduser().resolve() != base:
                problems.append("manifest.run_dir 与 --base 不一致")
        except OSError:
            problems.append("manifest.run_dir 无法解析")

    raw_entries = manifest.get("entries")
    if not isinstance(raw_entries, list) or not raw_entries:
        problems.append("manifest.entries 必须是非空数组")
        return version, []

    entries: list[dict[str, object]] = []
    seen: set[str] = set()
    total = 0
    lead_changed = False
    for i, raw in enumerate(raw_entries):
        if not isinstance(raw, dict):
            problems.append(f"manifest.entries[{i}] 必须是对象")
            continue
        try:
            rel = _normalise_rel(raw.get("path"), label=f"manifest.entries[{i}].path")
            path = safe_join(base, rel, must_exist=False)
        except ReceiptError as exc:
            problems.append(str(exc))
            continue
        if rel in seen:
            problems.append(f"manifest.entries 重复路径：{rel}")
            continue
        seen.add(rel)
        if version >= 2 and rel.startswith("_handoff/") and not rel.endswith("_preread.md"):
            problems.append(f"v2 manifest 不得封存非 preread 的控制文件：{rel}")
        role = raw.get("role", "evidence")
        if role not in {"evidence", "lead"}:
            problems.append(f"manifest.entries[{i}].role 非法：{role!r}")
        if not path.is_file():
            if role == "lead":
                lead_changed = True
                notes.append(f"线索文件缺失（不阻断）：{rel}")
                item = dict(raw)
                item["path"] = rel
                item["role"] = role
                entries.append(item)
                continue
            problems.append(f"上游输入缺失：{rel}")
            continue
        size = raw.get("bytes")
        if version >= 2 and (not _is_int(size) or size < 0):
            problems.append(f"v2 manifest.entries[{i}].bytes 必填且为非负整数：{rel}")
        if size is not None and (not _is_int(size) or size < 0):
            problems.append(f"manifest.entries[{i}].bytes 必须是非负整数")
        elif _is_int(size) and size != path.stat().st_size:
            if role == "lead":
                lead_changed = True
                notes.append(f"线索文件字节数已更新（不阻断）：{rel}")
            else:
                problems.append(f"清单字节数不符：{rel}（登记 {size}，实际 {path.stat().st_size}）")
        digest = raw.get("sha256")
        if version >= 2 and (not isinstance(digest, str) or not HEX64.fullmatch(digest)):
            problems.append(f"v2 manifest.entries[{i}].sha256 必填：{rel}")
        if digest is not None and (not isinstance(digest, str) or not HEX64.fullmatch(digest)):
            problems.append(f"manifest.entries[{i}].sha256 格式非法：{rel}")
        elif isinstance(digest, str) and sha256(path).lower() != digest.lower():
            if role == "lead":
                lead_changed = True
                notes.append(f"线索文件已更新（不阻断）：{rel}")
            else:
                problems.append(f"上游输入被改动：{rel}")
        total += path.stat().st_size
        item = dict(raw)
        item["path"] = rel
        item["role"] = role
        entries.append(item)

    declared_total = manifest.get("total_bytes")
    if declared_total is not None and (_is_int(declared_total) is False or declared_total != total):
        if version < 2 or lead_changed:
            notes.append(f"manifest.total_bytes 已变化（兼容/lead 更新）：登记 {declared_total!r}，实际 {total}")
        else:
            problems.append(f"manifest.total_bytes 不符（登记 {declared_total!r}，实际 {total}）")

    if stage_known:
        groups = REQUIRED_GROUPS[stage]
        if version < 2:
            groups = tuple(group for group in groups if not any(x.startswith("_handoff/") for x in group))
        rels = [str(e["path"]) for e in entries if e.get("role") == "evidence"]
        for group in groups:
            if not any(_match(rel, candidate) for rel in rels for candidate in group):
                problems.append(f"阶段 {stage} 的清单缺少必需输入：{' 或 '.join(group)}")
    if version < 2:
        notes.append("旧版 manifest（兼容模式）：未强制 preread 输入组与完整回执 schema")
    return version, entries


def _validate_reproduction(stage: str, receipt: dict[str, object], strict: bool, strict14: bool,
                           problems: list[str], notes: list[str]) -> None:
    if stage not in NEED_REPRO:
        return
    rep = receipt.get("reproduction")
    if not isinstance(rep, dict):
        problems.append(f"阶段 {stage} 必须提供 reproduction 对象")
        return
    commands = rep.get("commands")
    if not isinstance(commands, list) or not commands:
        problems.append("reproduction.commands 必须是非空数组")
    elif strict14:
        for i, command in enumerate(commands):
            if not isinstance(command, dict):
                problems.append(f"protocol 1.4 的 reproduction.commands[{i}] 必须是对象")
                continue
            text = command.get("command") or command.get("cmd")
            if not isinstance(text, str) or not text.strip():
                problems.append(f"reproduction.commands[{i}] 缺少 command")
            code = command.get("exit_code")
            if not _is_int(code) or code != 0:
                problems.append(f"reproduction.commands[{i}].exit_code 必须为 0（实际 {code!r}）")
    elif any(not isinstance(x, str) or not x.strip() for x in (commands or [])):
        problems.append("旧协议 reproduction.commands 必须是非空字符串数组")
    values = rep.get("values")
    if isinstance(values, dict):
        value_count = len(values)
    elif isinstance(values, list):
        value_count = len(values)
    else:
        value_count = 0
    if value_count < 3:
        problems.append("reproduction.values 至少 3 条独立复算值")
    if strict14:
        if not isinstance(values, list):
            problems.append("protocol 1.4 的 reproduction.values 必须是数组")
        else:
            for i, value in enumerate(values):
                if not isinstance(value, dict):
                    problems.append(f"reproduction.values[{i}] 必须是对象")
                    continue
                if not (value.get("name") or value.get("quantity")):
                    problems.append(f"reproduction.values[{i}] 缺少 name/quantity")
                if "value" not in value and "recomputed" not in value:
                    problems.append(f"reproduction.values[{i}] 缺少 value")
                if not value.get("source"):
                    problems.append(f"reproduction.values[{i}] 缺少 source")
    seconds = rep.get("seconds")
    if strict14 and seconds is None:
        problems.append("protocol 1.4 的 reproduction.seconds 必填")
    if seconds is not None:
        valid_seconds = _is_number(seconds) or (
            isinstance(seconds, dict) and all(_is_number(v) for v in seconds.values())
        )
        if valid_seconds:
            if isinstance(seconds, dict):
                valid_seconds = all(float(v) >= 0 for v in seconds.values())
            else:
                valid_seconds = float(seconds) >= 0
        if not valid_seconds:
            if strict:
                problems.append("reproduction.seconds 必须是有限数值或数值对象")
            else:
                notes.append("旧回执 reproduction.seconds 非数值，已兼容放行")


def _attachment_key(value: object) -> str:
    if isinstance(value, dict):
        value = value.get("file") or value.get("path") or value.get("name") or ""
    text = str(value).split("（", 1)[0].split("(", 1)[0].strip().replace("\\", "/")
    return PurePosixPath(text).name.strip()


def _validate_reread(stage: str, receipt: dict[str, object], entries: list[dict[str, object]],
                     strict: bool, strict13: bool, strict14: bool, base: Path,
                     problems: list[str], notes: list[str]) -> None:
    need_reread = stage in REREAD_STAGES and (strict or stage == "S4R")
    if not need_reread:
        return
    rr = receipt.get("inputs_reread") or {}
    raw_attachments: list[object] = []
    if stage != "S1":
        if not isinstance(rr, dict):
            problems.append("inputs_reread 必须是对象")
            return
        if rr.get("problem_text") is not True:
            problems.append("inputs_reread.problem_text 必须为 true")
        if rr.get("question_card_rebuilt") is not True:
            problems.append("inputs_reread.question_card_rebuilt 必须为 true")
        need = [str(e["path"]) for e in entries
                if str(e.get("path", "")).startswith("00_题目/")
                and (strict14 or not str(e["path"]).lower().endswith(".txt"))]
        raw_attachments = rr.get("attachments_verified") or []
        if not isinstance(raw_attachments, list):
            problems.append("inputs_reread.attachments_verified 必须是数组")
            raw_attachments = []
        got = {_attachment_key(x) for x in raw_attachments}
        # 旧协议按 basename 比较；这条仅用于兼容提示。严格协议下面会按完整
        # manifest 相对路径、字节数和 SHA-256 再验一次，防止同名冒充。
        need_names = [PurePosixPath(name).name for name in need]
        missing = [name for name in need_names if name not in got]
        if missing:
            problems.append("inputs_reread.attachments_verified 未覆盖附件：" + "、".join(missing))
        if strict14:
            expected = {str(e["path"]): e for e in entries
                        if str(e.get("path", "")).startswith("00_题目/")}
            expected_paths = set(expected)
            actual_paths: set[str] = set()
            bad_refs: list[str] = []
            for item in raw_attachments:
                if isinstance(item, dict):
                    raw_name = item.get("path") or item.get("file") or item.get("name") or ""
                else:
                    raw_name = item
                clean = str(raw_name).split("（", 1)[0].split("(", 1)[0].strip().replace("\\", "/")
                if clean not in expected_paths or not isinstance(item, dict):
                    bad_refs.append(clean or "<空>")
                    continue
                try:
                    target = safe_join(base, clean, must_exist=True)
                except ReceiptError as exc:
                    problems.append(str(exc))
                    continue
                digest = item.get("sha256")
                size = item.get("bytes")
                if not isinstance(digest, str) or not HEX64.fullmatch(digest):
                    problems.append(f"附件 {clean} 缺少合法 sha256")
                elif sha256(target).lower() != digest.lower():
                    problems.append(f"附件哈希与回执不符：{clean}")
                if not _is_int(size) or size != target.stat().st_size:
                    problems.append(f"附件字节数与回执不符：{clean}")
                actual_paths.add(clean)
            if bad_refs:
                problems.append("protocol 1.4 的 attachments_verified 必须使用 manifest 完整相对路径和对象：" + "、".join(bad_refs))
            if actual_paths != expected_paths:
                problems.append("protocol 1.4 的 attachments_verified 必须与清单附件集合完全一致")
        values = rr.get("recomputed_values") or []
        if not isinstance(values, list) or len(values) < 3:
            problems.append("inputs_reread.recomputed_values 至少 3 条")

    pqr = receipt.get("per_question_reread")
    if not isinstance(pqr, list) or not pqr:
        problems.append("缺少 per_question_reread（逐问复读记录）")
    else:
        min_rounds = 4 if (strict13 or strict14) else 3
        seen_questions: set[str] = set()
        for item in pqr:
            if not isinstance(item, dict):
                problems.append("per_question_reread 条目必须是对象")
                continue
            q = item.get("question") or "?"
            if strict14 and q in seen_questions:
                problems.append(f"per_question_reread 重复问题：{q}")
            seen_questions.add(str(q))
            if not item.get("source_quotes"):
                problems.append(f"per_question_reread[{q}] 缺少 source_quotes")
            elif strict14:
                quote_text = str(item.get("source_quotes"))
                if not re.search(r"(?:第\s*\d+\s*页|页码|page\s*\d+|p\.\s*\d+)", quote_text, re.I):
                    problems.append(f"per_question_reread[{q}] source_quotes 必须包含页码")
            rounds = item.get("rounds")
            if not _is_int(rounds) or rounds < min_rounds:
                problems.append(f"per_question_reread[{q}] 轮次不足 {min_rounds}")
            if strict14 and not item.get("conclusion"):
                problems.append(f"per_question_reread[{q}] 缺少 conclusion")

    pre = receipt.get("preread")
    # 只有协议明确要求无技能预读的阶段才把 preread 作为硬门槛；S4/S5c
    # 仍要求 inputs_reread，但历史流程没有单独的 preread 清单。
    if stage not in PREREAD_REQUIRED_STAGES and pre is None:
        return
    if not isinstance(pre, dict):
        problems.append("缺少 preread（无技能预读会话产物）")
        return
    if pre.get("no_skill") is not True:
        problems.append("preread.no_skill 必须为 true")
    try:
        pre_rel = _normalise_rel(pre.get("artifact"), label="preread.artifact")
        pre_path = safe_join(base, pre_rel, must_exist=True)
    except ReceiptError as exc:
        problems.append(str(exc))
        return
    manifest_item = next((e for e in entries if e.get("path") == pre_rel), None)
    if strict and manifest_item is None:
        problems.append(f"preread 产物未封存在 manifest：{pre_rel}")
    if strict14:
        expected_pre = f"_handoff/{stage}_preread.md"
        if pre_rel != expected_pre:
            problems.append(f"preread.artifact 必须为 {expected_pre}")
        if not isinstance(pre.get("session_id"), str) or not pre.get("session_id").strip():
            problems.append("protocol 1.4 的 preread.session_id 必填")
        rounds = pre.get("rounds")
        if not isinstance(rounds, list) or not {str(x) for x in rounds}.issuperset({"抄读", "自解"}):
            problems.append("protocol 1.4 的 preread.rounds 必须包含抄读和自解")
    expected = pre.get("sha256")
    if expected is None:
        if strict:
            problems.append("严格回执的 preread.sha256 不能为空")
        else:
            notes.append("旧回执 preread 未登记 sha256，已兼容放行")
    elif not isinstance(expected, str) or not HEX64.fullmatch(expected) or sha256(pre_path).lower() != expected.lower():
        problems.append(f"preread 产物哈希不符：{pre_rel}")
    if manifest_item and manifest_item.get("sha256") and str(manifest_item["sha256"]).lower() != sha256(pre_path).lower():
        problems.append(f"preread 与 manifest 哈希不一致：{pre_rel}")


def _validate_stage_specific(stage: str, receipt: dict[str, object], strict13: bool, strict14: bool,
                             base: Path, problems: list[str]) -> None:
    if stage == "S1" and strict13:
        sc = receipt.get("self_check")
        if not isinstance(sc, dict):
            problems.append("S1 缺少 self_check")
        else:
            for key in ("formula_implementable", "acceptance_criteria", "dimension_check",
                        "assumptions_with_evidence", "requirement_mapping", "data_traceable"):
                if sc.get(key) is not True:
                    problems.append(f"self_check.{key} 必须为 true")
            if not isinstance(sc.get("risk_list"), list) or len(sc["risk_list"]) < 3:
                problems.append("self_check.risk_list 至少 3 条")
    if stage in {"S2", "S2R"} and strict13:
        sr = receipt.get("strict_review")
        if not isinstance(sr, dict):
            problems.append("S2 缺少 strict_review")
        else:
            rc = sr.get("requirement_coverage") or {}
            if not isinstance(rc, dict) or not _is_int(rc.get("missing")):
                problems.append("strict_review.requirement_coverage.missing 必须为整数")
            elif rc["missing"] != 0 and sr.get("verdict") != "需返工":
                problems.append("requirement_coverage.missing>0 时 verdict 必须为需返工")
            if not isinstance(sr.get("counter_checks"), list) or len(sr["counter_checks"]) < 1:
                problems.append("strict_review.counter_checks 至少 1 条")
            if not isinstance(sr.get("evidence_table"), list) or len(sr["evidence_table"]) < 3:
                problems.append("strict_review.evidence_table 至少 3 条")
            if sr.get("verdict") not in ("通过", "有条件通过", "需返工"):
                problems.append("strict_review.verdict 必须是 通过/有条件通过/需返工")
            elif strict14 and sr.get("verdict") == "需返工":
                problems.append("protocol 1.4 的完成回执不能以『需返工』通过方案评审")
            if strict14 and isinstance(rc, dict) and _is_int(rc.get("missing")) and rc["missing"] != 0:
                problems.append("protocol 1.4 的方案评审要求 requirement_coverage.missing=0")
    if stage == "S4R":
        mc = receipt.get("model_change")
        if not isinstance(mc, dict):
            problems.append("S4R 必须提供 model_change")
        else:
            for key in ("changed", "requires_rerun"):
                if not isinstance(mc.get(key), bool):
                    problems.append(f"model_change.{key} 必须为布尔值")
            if mc.get("changed") and (not isinstance(mc.get("changes"), list) or not mc["changes"]):
                problems.append("model_change.changed=true 时必须列出 changes")
            if not mc.get("changed") and mc.get("changes") not in (None, [], ""):
                problems.append("model_change.changed=false 时 changes 必须为空")
            if mc.get("requires_rerun") and not mc.get("changed"):
                problems.append("model_change.requires_rerun=true 时 changed 不能为 false")
            if strict14 and not isinstance(mc.get("summary"), str):
                problems.append("protocol 1.4 的 S4R model_change.summary 必须是字符串")
            if strict14 and mc.get("changed"):
                for i, change in enumerate(mc.get("changes") or []):
                     if not isinstance(change, dict) or not all(change.get(k) for k in ("target", "why", "impact")):
                         problems.append(f"model_change.changes[{i}] 必须包含 target/why/impact")
        if strict14:
            gate = receipt.get("code_gate")
            if gate is not None:
                if not isinstance(gate, dict):
                    problems.append("S4R code_gate 必须是对象")
                else:
                    if not _pass_value(gate.get("status", gate.get("result", gate.get("passed")))):
                        problems.append("S4R code_gate 未通过")
                    for key in ("p0", "open_p1"):
                        if key in gate and (not _is_int(gate[key]) or gate[key] != 0):
                            problems.append(f"S4R code_gate.{key} 必须为 0")
    if stage == "S5c":
        rt = receipt.get("requirement_trace") or {}
        if not isinstance(rt, dict):
            problems.append("S5c requirement_trace 必须是对象")
        else:
            try:
                trace_rel = _normalise_rel(rt.get("file"), label="requirement_trace.file")
                safe_join(base, trace_rel, must_exist=True)
            except ReceiptError as exc:
                problems.append(str(exc))
            nums = [rt.get(k) for k in ("total", "satisfied", "partial", "missing")]
            if any(not _is_int(v) or v < 0 for v in nums):
                problems.append("requirement_trace 的 total/satisfied/partial/missing 必须为非负整数")
            elif nums[1] + nums[2] + nums[3] != nums[0]:
                problems.append("requirement_trace 三类计数之和必须等于 total")
            if _is_int(nums[3]) and nums[3] != 0:
                problems.append(f"赛题要求对照仍有 {nums[3]} 条未满足")
            if strict14 and _is_int(nums[2]) and nums[2] != 0:
                problems.append(f"protocol 1.4 的赛题要求对照仍有 {nums[2]} 条 partial")
        review = receipt.get("independent_trace_review")
        if isinstance(review, dict):
            review = review.get("file") or review.get("path")
        if isinstance(review, str):
            try:
                review_path = safe_join(base, review, must_exist=True)
            except ReceiptError as exc:
                problems.append(str(exc))
            else:
                if strict14:
                    listed = receipt.get("artifacts") or []
                    if not any(isinstance(x, dict) and x.get("path") == _normalise_rel(review)
                               for x in listed):
                        problems.append("protocol 1.4 的 independent_trace_review 必须登记在 artifacts")
        elif not review:
            problems.append("S5c 必须提供 independent_trace_review")


def _validate_prerequisites(stage: str, base: Path, strict14: bool,
                            problems: list[str], notes: list[str]) -> None:
    """新协议要求前置阶段有已完成回执；旧运行仅给提示。"""
    for alternatives in PREREQUISITES.get(stage, ()):
        found: list[str] = []
        # 复评/复检一旦存在，不得绕过它退回选择旧的 S2/S4 回执。
        candidates = alternatives
        if strict14 and len(alternatives) > 1:
            present = [name for name in alternatives
                       if (base / "_handoff" / f"{name}_receipt.json").exists()
                       or _is_link(base / "_handoff" / f"{name}_receipt.json")]
            if present:
                candidates = (present[-1],)
        for candidate in candidates:
            retry_input = (stage == "S2R" and candidate == "S2") or (
                stage == "S4B" and candidate == "S4"
            )
            try:
                path = safe_join(base, f"_handoff/{candidate}_receipt.json", must_exist=True)
            except ReceiptError:
                continue
            try:
                data = _read_json(path, f"前置回执 {candidate}")
            except ReceiptError:
                continue
            if data.get("stage") != candidate or not isinstance(data.get("status"), str):
                continue
            if (strict14 and data["status"] != "完成") or (not strict14 and not data["status"].startswith("完成")):
                continue
            unresolved = data.get("unresolved")
            if strict14 and (not isinstance(unresolved, list) or (not retry_input and any(
                isinstance(item, str) and _is_blocking_unresolved(item) for item in unresolved
            ))):
                continue
            if strict14:
                gate = data.get("gate", data.get("gates"))
                if not isinstance(gate, dict):
                    continue
                if not retry_input and not _pass_value(
                    gate.get("status", gate.get("result", gate.get("decision", gate.get("passed"))))
                ):
                    continue
                if not retry_input and candidate in {"S4", "S4B", "S4R"} and any(
                    not _is_int(gate.get(key)) or gate[key] != 0 for key in ("p0", "open_p1")
                ):
                    continue
                if not retry_input and candidate in {"S2", "S2R"}:
                    review = data.get("strict_review")
                    if not isinstance(review, dict) or review.get("verdict") == "需返工":
                        continue
                    coverage = review.get("requirement_coverage")
                    if not isinstance(coverage, dict) or coverage.get("missing") != 0:
                        continue
                if candidate == "S4R":
                    model_change = data.get("model_change")
                    if not isinstance(model_change, dict) or model_change.get("requires_rerun") is not False:
                        continue
                # 不能只信 status/gate：前置清单与产物必须仍存在且校验通过。
                try:
                    previous_manifest = _read_json(
                        safe_join(base, f"_handoff/{candidate}_manifest.json", must_exist=True),
                        f"前置清单 {candidate}",
                    )
                except ReceiptError:
                    continue
                prior_problems: list[str] = []
                prior_notes: list[str] = []
                prior_version, _prior_entries = _validate_manifest(previous_manifest, base, prior_problems, prior_notes)
                if previous_manifest.get("stage") != candidate or prior_version < 2:
                    continue
                _validate_artifacts(data, base, True, f"_handoff/{candidate}_receipt.json",
                                    prior_problems, prior_notes)
                if prior_problems:
                    continue
            found.append(candidate)
        if not found:
            message = "前置阶段回执缺失或未通过：" + " 或 ".join(candidates)
            if strict14:
                problems.append(message)
            else:
                notes.append(message + "（兼容模式，仅提示）")


def _validate_artifacts(receipt: dict[str, object], base: Path, strict: bool,
                        receipt_rel: str | None, problems: list[str], notes: list[str]) -> None:
    artifacts = receipt.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        problems.append("回执 artifacts 必须是非空数组")
        return
    seen: set[str] = set()
    for i, raw in enumerate(artifacts):
        if not isinstance(raw, dict):
            problems.append(f"artifacts[{i}] 必须是对象")
            continue
        try:
            rel = _normalise_rel(raw.get("path"), label=f"artifacts[{i}].path")
            path = safe_join(base, rel, must_exist=True)
        except ReceiptError as exc:
            problems.append(str(exc))
            continue
        if rel in seen:
            problems.append(f"回执 artifacts 重复路径：{rel}")
            continue
        seen.add(rel)
        digest = raw.get("sha256")
        if digest is None:
            if strict and rel != receipt_rel:
                problems.append(f"严格回执缺少 artifacts[{i}].sha256：{rel}")
            else:
                notes.append(f"artifact 未登记 sha256（兼容/自引用）：{rel}")
        elif not isinstance(digest, str) or not HEX64.fullmatch(digest):
            problems.append(f"artifacts[{i}].sha256 格式非法：{rel}")
        elif sha256(path).lower() != digest.lower():
            problems.append(f"产物哈希与回执不符：{rel}")
        size = raw.get("bytes")
        if size is None:
            if strict and rel != receipt_rel:
                problems.append(f"严格回执缺少 artifacts[{i}].bytes：{rel}")
        elif not _is_int(size) or size < 0:
            problems.append(f"artifacts[{i}].bytes 必须是非负整数：{rel}")
        elif size != path.stat().st_size:
            problems.append(f"产物字节数与回执不符：{rel}（登记 {size}，实际 {path.stat().st_size}）")


def main() -> int:
    ap = argparse.ArgumentParser(description="校验阶段回执")
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--receipt", required=True)
    ap.add_argument("--base", required=True)
    args = ap.parse_args()

    problems: list[str] = []
    notes: list[str] = []
    try:
        base_raw = Path(args.base).expanduser()
        if _path_has_symlink(base_raw.absolute(), Path(base_raw.absolute().anchor)):
            raise ReceiptError(f"base 或其父路径不能含符号链接：{base_raw}")
        base = base_raw.resolve()
        if not base.is_dir() or _is_link(base):
            raise ReceiptError(f"base 不存在、不是目录或是符号链接：{base}")
        manifest_path = _input_path(base, args.manifest, "manifest")
        receipt_path = _input_path(base, args.receipt, "receipt")
        manifest = _read_json(manifest_path, "manifest")
        receipt = _read_json(receipt_path, "receipt")
    except (ReceiptError, OSError) as exc:
        print(f"[回执校验] 不通过：{exc}")
        return 1

    manifest_version, entries = _validate_manifest(manifest, base, problems, notes)
    manifest_stage = manifest.get("stage")
    receipt_stage = receipt.get("stage")
    receipt_known = isinstance(receipt_stage, str) and receipt_stage in KNOWN_STAGES
    if not receipt_known:
        problems.append(f"回执阶段未知或缺失：{receipt_stage!r}")
    if manifest_stage != receipt_stage:
        problems.append(f"阶段不一致：清单 {manifest_stage} vs 回执 {receipt_stage}")
    for key in REQUIRED:
        if key not in receipt:
            problems.append(f"回执缺少字段：{key}")
    if not isinstance(receipt.get("status"), str) or not receipt.get("status", "").startswith("完成"):
        problems.append(f"阶段状态为「{receipt.get('status', '')}」，不得进入下一阶段")
    if not isinstance(receipt.get("unresolved"), list):
        problems.append("回执 unresolved 必须是数组")
    elif any(not isinstance(item, str) for item in receipt["unresolved"]):
        problems.append("回执 unresolved 只能包含字符串")

    pv = _version(receipt.get("protocol_version"))
    if receipt.get("protocol_version") is not None and pv is None:
        problems.append("protocol_version 格式非法")
    strict13 = manifest_version >= 2 or bool(pv and pv >= (1, 3))
    strict = manifest_version >= 2 or bool(pv and pv >= (1, 2))
    manifest_protocol = _version(manifest.get("protocol_version"))
    strict14 = bool((pv and pv >= CURRENT_PROTOCOL) or (manifest_protocol and manifest_protocol >= CURRENT_PROTOCOL))
    if manifest_version >= 2 and (pv is None or pv < CURRENT_PROTOCOL):
        problems.append("v2 manifest 的回执必须声明 protocol_version >= 1.4")

    if strict14 and isinstance(receipt.get("unresolved"), list):
        blockers = [item for item in receipt["unresolved"] if isinstance(item, str) and _is_blocking_unresolved(item)]
        if blockers:
            problems.append("protocol 1.4 的完成回执不得含 P0/P1/阻塞级 unresolved：" + "；".join(blockers))
    if strict14 and receipt.get("status") != "完成":
        problems.append("protocol 1.4 的通过状态必须精确为『完成』")

    _validate_reproduction(str(receipt_stage), receipt, strict, strict14, problems, notes)
    _validate_stage_specific(str(receipt_stage), receipt, strict13, strict14, base, problems)
    _validate_reread(str(receipt_stage), receipt, entries, strict, strict13, strict14, base, problems, notes)
    _validate_gate(str(receipt_stage), receipt, strict14, problems)
    if receipt_known:
        _validate_prerequisites(str(receipt_stage), base, strict14, problems, notes)

    try:
        receipt_rel = receipt_path.relative_to(base).as_posix()
    except ValueError:
        receipt_rel = None
    _validate_artifacts(receipt, base, strict, receipt_rel, problems, notes)

    # 再核验 manifest 输入（_validate_manifest 已做首次检查，但这里给出 lead
    # 的兼容性提示，并确保其路径没有被回执阶段改变）。
    for entry in entries:
        rel = str(entry["path"])
        try:
            path = safe_join(base, rel, must_exist=False)
        except ReceiptError as exc:
            problems.append(str(exc))
            continue
        if not path.is_file():
            if entry.get("role") == "lead":
                notes.append(f"线索文件缺失（不阻断）：{rel}")
            else:
                problems.append(f"上游输入缺失：{rel}")
            continue
        digest = entry.get("sha256")
        if entry.get("role") == "lead":
            if digest and isinstance(digest, str) and HEX64.fullmatch(digest) and sha256(path).lower() != digest.lower():
                notes.append(f"线索文件已更新（不阻断）：{rel}")
            continue
        if not digest:
            # 旧清单可能没有哈希；新清单已经在 manifest 校验阶段拒绝这种情况
            notes.append(f"旧清单未登记输入哈希：{rel}")

    if problems:
        print("[回执校验] 不通过：")
        for item in problems:
            print("  -", item)
        for item in notes:
            print("  ·", item)
        return 1

    print(f"[回执校验] 通过：阶段 {receipt_stage}，产物 {len(receipt.get('artifacts') or [])} 个，"
          f"清单输入 {len(entries)} 个已核验")
    for item in notes:
        print("  ·", item)
    rep = receipt.get("reproduction")
    if isinstance(rep, dict):
        commands = rep.get("commands") or []
        command_text = [str(c.get("command") or c.get("cmd")) if isinstance(c, dict) else str(c)
                        for c in commands]
        print(f"  复跑命令：{'; '.join(command_text)}（{rep.get('seconds', '?')} s）")
        values = rep.get("values") or []
        if isinstance(values, dict):
            values = [{"name": key, "value": value} for key, value in values.items()]
        for value in list(values)[:5]:
            if isinstance(value, dict):
                print(f"  独立复算 {value.get('name') or value.get('quantity')} = "
                      f"{value.get('value', value.get('recomputed', ''))}（{value.get('source', '')}）")
            else:
                print(f"  独立复算 {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
