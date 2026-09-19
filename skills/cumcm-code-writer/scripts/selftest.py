"""三轮自测驱动：跑通 → 数值/算法正确性 → 多种子稳定性与口径一致。

用法：
    python selftest.py --project 2026A
    python selftest.py --project 2026A --code-dir output/2026A/code --entry run_all.py --seeds 42,7,2026
    python selftest.py --project 2026A --rounds 1

约定：
    - 项目入口脚本支持 `--seed <int>` 时，第三轮会自动传入不同种子；
    - 项目提供 code/tests/round2_numeric.py 时，第二轮运行它（退出码 0 视为通过）；
    - 未提供专项校验脚本时，第二轮标注"未自动验证"，不假装通过。
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _paths import CODE_ENV_PYTHON, OUTPUT_DIR, WORKSPACE_DIR, project_work, rel  # noqa: E402

DEFAULT_SEEDS = [42, 7, 2026]
IGNORE_DIRS = {"__pycache__", ".git", ".ipynb_checkpoints", "figures"}


def python_exe() -> str:
    return str(CODE_ENV_PYTHON) if CODE_ENV_PYTHON.exists() else sys.executable


def snapshot(root: Path) -> dict[str, float]:
    if not root.exists():
        return {}
    return {
        str(p.relative_to(root)).replace("\\", "/"): p.stat().st_mtime
        for p in root.rglob("*")
        if p.is_file()
    }


def run_script(script: Path, cwd: Path, args: list[str], timeout: int, env_extra: dict | None = None) -> dict:
    env = os.environ.copy()
    env.update(env_extra or {})
    started = time.time()
    try:
        proc = subprocess.run(
            [python_exe(), str(script), *args],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
            check=False,
        )
        return {
            "cmd": f"{Path(python_exe()).name} {script.name} {' '.join(args)}".strip(),
            "code": proc.returncode,
            "seconds": round(time.time() - started, 1),
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        }
    except subprocess.TimeoutExpired:
        return {
            "cmd": f"{Path(python_exe()).name} {script.name} {' '.join(args)}".strip(),
            "code": 124,
            "seconds": round(time.time() - started, 1),
            "stdout": "",
            "stderr": f"超时（>{timeout}s）",
        }


def collect_python_files(code_dir: Path) -> list[Path]:
    return [
        p
        for p in code_dir.rglob("*.py")
        if not any(part in IGNORE_DIRS for part in p.parts) and "tests" not in p.parts
    ]


def round1(code_dir: Path, entry: Path, timeout: int) -> tuple[dict, list[str]]:
    notes: list[str] = []
    syntax_errors: list[str] = []
    for path in collect_python_files(code_dir):
        try:
            compile(path.read_text(encoding="utf-8", errors="ignore"), str(path), "exec")
        except SyntaxError as exc:
            syntax_errors.append(f"{rel(path)}: {exc.msg}（第 {exc.lineno} 行）")
    if syntax_errors:
        notes.extend(f"语法错误：{item}" for item in syntax_errors)
        return {"ok": False, "details": "语法检查未通过", "run": None}, notes

    before = snapshot(code_dir)
    result = run_script(entry, code_dir, [], timeout)
    after = snapshot(code_dir)
    produced = sorted(set(after) - set(before))
    ok = result["code"] == 0
    detail = (
        f"入口脚本退出码 {result['code']}，耗时 {result['seconds']}s，"
        f"新生成/更新文件 {len(produced)} 个"
    )
    if not ok:
        notes.append("第一轮未跑通：" + (result["stderr"].strip().splitlines() or ["无错误输出"])[-1])
    return {"ok": ok, "details": detail, "run": result, "produced": produced}, notes


CHECK_SUMMARY_RE = re.compile(r"CHECK-SUMMARY\s+total=(\d+)\s+passed=(\d+)\s+baselines=(\d+)")
MIN_CHECKS = 3
MIN_BASELINES = 1


def parse_check_summary(text: str) -> dict | None:
    match = CHECK_SUMMARY_RE.search(text or "")
    if not match:
        return None
    total, passed, baselines = (int(value) for value in match.groups())
    return {"total": total, "passed": passed, "baselines": baselines}


def round2(code_dir: Path, entry: Path, timeout: int, allow_missing: bool = False) -> tuple[dict, list[str]]:
    """第二轮：数值与算法正确性对照。

    阻塞规则：缺校验机制、缺 CHECK-SUMMARY 汇总行、校验强度不足（检查项<3 或独立基准<1）都判未通过；
    只有用户显式 --allow-missing-verify 才放行，并在记录中标注豁免。
    """
    checker = code_dir / "tests" / "round2_numeric.py"
    if checker.exists():
        result = run_script(checker, code_dir, [], timeout)
        summary = parse_check_summary(result["stdout"])
        if summary is None:
            return (
                {"ok": False, "details": "校验脚本未输出 CHECK-SUMMARY 汇总行，无法确认校验强度", "run": result},
                ["第二轮缺少 CHECK-SUMMARY 汇总行：按模板约定输出 `CHECK-SUMMARY total=.. passed=.. baselines=..`。"],
            )
        weak = summary["total"] < MIN_CHECKS or summary["baselines"] < MIN_BASELINES
        notes = []
        if result["code"] != 0:
            notes.append("第二轮专项校验未通过，见自测记录输出。")
        if weak:
            notes.append(
                f"第二轮校验强度不足：检查项 {summary['total']}（需≥{MIN_CHECKS}），"
                f"独立基准 {summary['baselines']}（需≥{MIN_BASELINES}）。"
            )
        details = (f"专项校验退出码 {result['code']}；检查项 {summary['total']}，"
                   f"通过 {summary['passed']}，独立基准 {summary['baselines']}")
        return {"ok": result["code"] == 0 and not weak, "details": details, "run": result, "summary": summary}, notes

    text = entry.read_text(encoding="utf-8", errors="ignore") if entry.exists() else ""
    if "--verify" in text:
        result = run_script(entry, code_dir, ["--verify"], timeout)
        ok = result["code"] == 0
        details = f"入口 --verify 退出码 {result['code']}（未提供独立基准，仅作口径复核）"
        notes = [] if ok else ["入口脚本 --verify 模式未通过。"]
        return {"ok": ok, "details": details, "run": result, "summary": None}, notes

    if allow_missing:
        return (
            {"ok": True, "details": "未找到校验机制：按用户明示豁免，结果文档必须写明该限制", "run": None},
            ["第二轮已豁免：结果文档的限制说明中必须写明未做数值对照。"],
        )
    return (
        {"ok": False, "details": "未自动验证（阻塞交付）：缺 code/tests/round2_numeric.py，入口也未实现 --verify"},
        ["第二轮无法校验：请补 code/tests/round2_numeric.py（含 CHECK-SUMMARY 汇总行），"
         "或在入口实现 --verify；确需跳过时用 --allow-missing-verify 并由用户确认。"],
    )


def _read_numeric(path: Path) -> pd.DataFrame | None:
    try:
        if path.suffix.lower() == ".csv":
            return pd.read_csv(path)
        if path.suffix.lower() in {".xlsx", ".xls"}:
            return pd.read_excel(path)
    except Exception:
        return None
    return None


def compare_frames(base: pd.DataFrame, other: pd.DataFrame) -> float:
    numeric_base = base.select_dtypes("number")
    numeric_other = other.select_dtypes("number")
    common = [c for c in numeric_base.columns if c in numeric_other.columns]
    if not common or numeric_base.shape[0] != numeric_other.shape[0]:
        return float("nan")
    worst = 0.0
    for col in common:
        a = numeric_base[col].to_numpy(dtype=float)
        b = numeric_other[col].to_numpy(dtype=float)
        denom = max(1e-12, float(pd.Series(a).abs().max()))
        worst = max(worst, float(abs(a - b).max() / denom))
    return worst


def round3(code_dir: Path, entry: Path, timeout: int, seeds: list[int], tolerance: float) -> tuple[dict, list[str]]:
    notes: list[str] = []
    text = entry.read_text(encoding="utf-8", errors="ignore") if entry.exists() else ""
    supports_seed = "--seed" in text
    tables_dir = code_dir.parent / "tables"
    if not tables_dir.exists():
        tables_dir = code_dir / "tables"

    runs = []
    reference: dict[str, pd.DataFrame] = {}
    deviations: dict[str, float] = {}
    for index, seed in enumerate(seeds):
        before = snapshot(tables_dir) if tables_dir.exists() else {}
        args = ["--seed", str(seed)] if supports_seed else []
        result = run_script(entry, code_dir, args, timeout, env_extra={"MM_SEED": str(seed)})
        runs.append({"seed": seed, **result})
        if result["code"] != 0:
            notes.append(f"种子 {seed} 运行失败（退出码 {result['code']}），第三轮不通过。")
            return {"ok": False, "details": f"种子 {seed} 运行失败", "runs": runs, "deviations": {}}, notes
        if tables_dir.exists():
            current: dict[str, pd.DataFrame] = {}
            for path in tables_dir.rglob("*"):
                if path.is_file() and path.suffix.lower() in {".csv", ".xlsx"}:
                    frame = _read_numeric(path)
                    if frame is not None:
                        current[str(path.relative_to(tables_dir))] = frame
            if index == 0:
                reference = current
            else:
                for name, frame in current.items():
                    if name in reference:
                        value = compare_frames(reference[name], frame)
                        if value == value:  # 非 NaN
                            deviations[name] = max(deviations.get(name, 0.0), value)
            del before

    if not supports_seed:
        notes.append("入口脚本未实现 --seed 参数：已通过环境变量 MM_SEED 传种子，随机性可能不受控。")

    worst = max(deviations.values()) if deviations else 0.0
    stable = worst <= tolerance
    if not stable:
        notes.append(f"跨种子结果最大相对偏差 {worst:.3g}，超过阈值 {tolerance:g}，需说明随机性影响。")
    detail = (
        f"种子 {', '.join(map(str, seeds))}；比对表格 {len(deviations)} 个；最大相对偏差 {worst:.3g}"
        if deviations
        else f"种子 {', '.join(map(str, seeds))}；未发现可比较的结果表，稳定性未量化"
    )
    return {"ok": stable, "details": detail, "runs": runs, "deviations": deviations}, notes


def build_markdown(project: str, results: dict, notes: list[str]) -> str:
    lines = [
        f"# 自测记录 · {project}",
        "",
        f"> 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"> 入口：`{results['entry']}`；解释器：`{results['python']}`",
        "",
        "## 总览",
        "",
        "| 轮次 | 检查内容 | 结论 | 说明 |",
        "|---|---|---|---|",
    ]
    labels = {
        "round1": ("第一轮", "语法/依赖/端到端跑通"),
        "round2": ("第二轮", "数值与算法正确性对照"),
        "round3": ("第三轮", "多种子稳定性与口径一致"),
    }
    for key, (name, focus) in labels.items():
        item = results.get(key)
        if item is None:
            continue
        verdict = "通过" if item.get("ok") else ("未自动验证" if item.get("ok") is None else "未通过")
        lines.append(f"| {name} | {focus} | {verdict} | {item.get('details', '')} |")

    for key, (name, _) in labels.items():
        item = results.get(key)
        if not item or not item.get("run"):
            continue
        run = item["run"]
        lines += [
            "",
            f"## {name} · 运行输出",
            "",
            f"- 命令：`{run['cmd']}`",
            f"- 退出码：{run['code']}；耗时：{run['seconds']}s",
            "",
            "```text",
            (run["stdout"].strip()[-3000:] or "(无标准输出)"),
            "```",
        ]
        if run["stderr"].strip():
            lines += ["", "```text", run["stderr"].strip()[-1500:], "```"]

    if results.get("round3", {}).get("deviations"):
        lines += ["", "## 第三轮 · 跨种子偏差", "", "| 结果表 | 最大相对偏差 |", "|---|---|"]
        for name, value in sorted(results["round3"]["deviations"].items()):
            lines.append(f"| {name} | {value:.3g} |")

    if notes:
        lines += ["", "## 待处理", "", *[f"- {item}" for item in notes]]

    lines += [
        "",
        "## 结论",
        "",
        "三轮全部通过后才能进入交付阶段；未通过或未自动验证的轮次必须在结果文档的限制说明中如实写出。",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="三轮自测")
    parser.add_argument("--project", required=True, help="项目名，用于定位 output/<项目名> 与 work/<项目名>")
    parser.add_argument("--code-dir", default="", help="代码目录，默认 output/<项目名>/code")
    parser.add_argument("--entry", default="run_all.py", help="入口脚本名，默认 run_all.py")
    parser.add_argument("--seeds", default=",".join(map(str, DEFAULT_SEEDS)), help="第三轮种子列表")
    parser.add_argument("--rounds", default="1,2,3", help="要跑的轮次，如 1 或 1,2")
    parser.add_argument("--allow-missing-verify", action="store_true",
                        help="用户显式豁免第二轮数值校验（会在记录中标注，需写入结果文档限制）")
    parser.add_argument("--tolerance", type=float, default=1e-3, help="跨种子结果的相对偏差阈值")
    parser.add_argument("--timeout", type=int, default=1800, help="单次运行超时秒数")
    parser.add_argument("--out", default="", help="自测记录输出路径")
    args = parser.parse_args()

    code_dir = Path(args.code_dir) if args.code_dir else OUTPUT_DIR / args.project / "code"
    if not code_dir.is_absolute():
        code_dir = WORKSPACE_DIR / code_dir
    entry = code_dir / args.entry

    result: dict = {
        "entry": rel(entry),
        "python": python_exe(),
    }
    notes: list[str] = []

    if not code_dir.exists():
        print(f"[失败] 代码目录不存在：{rel(code_dir)}")
        return 2
    if not entry.exists():
        print(f"[失败] 入口脚本不存在：{rel(entry)}")
        return 2

    rounds = {r.strip() for r in args.rounds.split(",") if r.strip()}
    if "1" in rounds:
        item, new_notes = round1(code_dir, entry, args.timeout)
        result["round1"] = item
        notes += new_notes
    if "2" in rounds and result.get("round1", {}).get("ok", True):
        item, new_notes = round2(code_dir, entry, args.timeout, allow_missing=args.allow_missing_verify)
        result["round2"] = item
        notes += new_notes
    if "3" in rounds and result.get("round1", {}).get("ok", True):
        seeds = [int(s) for s in args.seeds.split(",") if s.strip()]
        item, new_notes = round3(code_dir, entry, args.timeout, seeds, args.tolerance)
        result["round3"] = item
        notes += new_notes

        declared = project_work(args.project) / "论文口径.md"
        script = Path(__file__).resolve().parent / "check_paper_consistency.py"
        if declared.exists() and script.exists():
            proc = subprocess.run([python_exe(), str(script), "--project", args.project],
                                  capture_output=True, text=True, check=False)
            paper_ok = proc.returncode == 0
            item["paper_consistency"] = "通过" if paper_ok else "未通过"
            if paper_ok:
                item["details"] += "；论文口径与代码结果一致"
            else:
                item["ok"] = False
                item["details"] += "；论文口径与代码结果不一致"
                notes.append("论文口径与代码结果不一致：见 work/<项目名>/论文口径核对.md，"
                             "资格红线要求两者一致，交付前必须处理。")

    markdown = build_markdown(args.project, result, notes)
    target = Path(args.out) if args.out else project_work(args.project) / "自测记录.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(markdown, encoding="utf-8")
    print(markdown)
    print(f"[写出] {rel(target)}")

    failed = any(item.get("ok") is False for item in result.values() if isinstance(item, dict))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
