"""机械检查生成代码的"AI 味"与工程卫生，产出可执行的整改清单。

用法：
    python lint_code.py --project 2026A
    python lint_code.py --code-dir output/2026A/code --out work/2026A/代码体检.md

检查项（P1 阻塞交付，P2 仅提示）：
    L1  吞异常：`except: pass`、裸 `except:`、`except Exception: pass`
    L2  绝对路径：代码里写死 `D:\\...` / `C:\\Users\\...`
    L3  随机性未固定：用了随机过程却没有固定种子
    L4  空话输出：`print("完成")`、`disp('Successfully ...')`、纯分隔线
    L5  命名气味：`tmp`、`data2`、`final`、`aaa`、`result` 之类的占位名
    L6  重复注释：同一句注释在文件里出现 3 次以上
    L7  注释比例过高：注释行 / 代码行 > 0.45
    L8  遗留标记：TODO / FIXME / XXX / 待补 / 待改
    L9  未使用导入：导入后全文再未出现
"""
from __future__ import annotations

import argparse
import ast
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _paths import OUTPUT_DIR, WORKSPACE_DIR, project_work, rel  # noqa: E402

PY_SUFFIXES = {".py"}
ML_SUFFIXES = {".m"}
SKIP_DIRS = {"__pycache__", ".git", ".ipynb_checkpoints", "tests"}

BOILERPLATE = [
    r"print\s*\(\s*[\"'][^\"']*(开始|完成|成功|结束|正在)[^\"']*[\"']\s*\)",
    r"disp\s*\(\s*['\"][^'\"]*(Successfully|completed|开始|完成|成功)[^'\"]*['\"]\s*\)",
    r"print\s*\(\s*[\"']=+[\"']\s*\)",
    r"print\s*\(\s*[\"']-+[\"']\s*\)",
]
NAMING_SMELLS = ["tmp", "temp1", "data2", "data3", "aaa", "bbb", "result_final", "final_result"]
RANDOM_MARKERS = ["np.random.", "random.", "numpy.random", "train_test_split(", "rand(", "randn(", "randi(", "datasample("]
SEED_MARKERS = ["default_rng(", "seed(", "random_state=", "rng(", "RandStream"]
LEFTVERS = ["TODO", "FIXME", "XXX", "待补", "待改", "暂未实现"]
SMELL_CODE = re.compile(r"\b(" + "|".join(NAMING_SMELLS) + r")\b", re.I)
MATLAB_PLOT = re.compile(r"exportgraphics\s*\(|saveas\s*\(|print\s*\([^)]*-(dpng|djpeg|depsc|dpdf)")
ABS_PATH = re.compile(r"[A-Za-z]:\\\\?[\\/](?:Users|综合处理|matlab|data|桌面)")


def iter_sources(root: Path):
    if root.is_file():
        if root.suffix.lower() in PY_SUFFIXES | ML_SUFFIXES:
            yield root
        return
    for path in sorted(root.rglob("*")):
        if not path.is_file() or any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in PY_SUFFIXES | ML_SUFFIXES:
            yield path


def comment_ratio(text: str) -> float:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return 0.0
    comments = [line for line in lines if line.startswith("#") or line.startswith("%")]
    return len(comments) / len(lines)


def duplicate_comments(text: str) -> list[str]:
    counter: dict[str, int] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#") or stripped.startswith("%"):
            body = stripped.lstrip("#%").strip()
            if len(body) >= 4:
                counter[body] = counter.get(body, 0) + 1
    return [body for body, count in counter.items() if count >= 3]


def unused_imports(text: str) -> list[str]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    imported = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported += [alias.asname or alias.name.split(".")[0] for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            imported += [alias.asname or alias.name for alias in node.names if alias.name != "*"]
    body = text
    unused = []
    for name in imported:
        if name in {"annotations"}:
            continue
        hits = len(re.findall(rf"\b{re.escape(name)}\b", body))
        if hits <= 1:
            unused.append(name)
    return unused


def lint_file(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    findings: list[dict] = []

    for index, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if re.search(r"except\s*(Exception)?\s*:\s*(pass|continue)?\s*$", stripped) or stripped == "except:":
            findings.append({"rule": "L1", "level": "P1", "line": index, "detail": "吞异常：except: pass"})
        if ABS_PATH.search(line):
            findings.append({"rule": "L2", "level": "P1", "line": index, "detail": "写死本机绝对路径"})
        for pattern in BOILERPLATE:
            if re.search(pattern, line, re.I):
                findings.append({"rule": "L4", "level": "P2", "line": index, "detail": "空话输出"})
                break
        smell = SMELL_CODE.search(line)
        if smell and not line.strip().startswith(("#", "%")):
            start, end = smell.start(), smell.end()
            is_method_call = start > 0 and line[start - 1] == "." and line[end:end + 1] == "("
            if not is_method_call:
                findings.append({"rule": "L5", "level": "P2", "line": index,
                                 "detail": f"占位命名：{smell.group(0)}"})
        if path.suffix.lower() == ".m" and MATLAB_PLOT.search(line):
            findings.append({"rule": "L10", "level": "P1", "line": index,
                             "detail": "MATLAB 出图：交付图件必须由 Python 生成"})
        for marker in LEFTVERS:
            if marker in line:
                findings.append({"rule": "L8", "level": "P1", "line": index, "detail": f"遗留标记：{marker}"})
                break

    uses_random = any(marker in text for marker in RANDOM_MARKERS)
    has_seed = any(marker in text for marker in SEED_MARKERS)
    if uses_random and not has_seed:
        findings.append({"rule": "L3", "level": "P1", "line": 0, "detail": "使用随机过程但未固定随机种子"})

    for body in duplicate_comments(text):
        findings.append({"rule": "L6", "level": "P2", "line": 0, "detail": f"重复注释出现 3 次以上：{body[:30]}"})

    ratio = comment_ratio(text)
    if ratio > 0.45:
        findings.append({"rule": "L7", "level": "P2", "line": 0, "detail": f"注释占比偏高：{ratio:.0%}"})

    if path.suffix.lower() == ".py":
        for name in unused_imports(text):
            findings.append({"rule": "L9", "level": "P2", "line": 0, "detail": f"疑似未使用导入：{name}"})
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="生成代码的机械体检")
    parser.add_argument("--project", default="", help="项目名（默认定位 output/<项目名>/code）")
    parser.add_argument("--code-dir", default="", help="直接指定代码目录")
    parser.add_argument("--out", default="", help="报告输出路径")
    args = parser.parse_args()

    if args.code_dir:
        code_dir = Path(args.code_dir)
        if not code_dir.is_absolute():
            candidate = Path.cwd() / code_dir
            code_dir = candidate if candidate.exists() else WORKSPACE_DIR / code_dir
    elif args.project:
        code_dir = OUTPUT_DIR / args.project / "code"
    else:
        parser.error("需要 --project 或 --code-dir")
        return 2

    if not code_dir.exists():
        print(f"[失败] 代码目录不存在：{rel(code_dir)}")
        return 2

    results = []
    for path in iter_sources(code_dir):
        findings = lint_file(path)
        if findings:
            results.append((path, findings))

    lines = [
        f"# 代码体检 · {args.project or code_dir.name}",
        "",
        f"> 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}；检查目录：`{rel(code_dir)}`",
        "> 说明：这是机械检查，只覆盖可自动判定的部分（异常处理、路径、种子、命名、注释、导入）；",
        "> 算法正确性与 AI 文风仍需人工或第二轮/第三轮自测把关。",
        "",
    ]
    p1_total = sum(1 for _, items in results for item in items if item["level"] == "P1")
    p2_total = sum(1 for _, items in results for item in items if item["level"] == "P2")
    lines += [f"共 {len(results)} 个文件命中问题：P1 {p1_total} 项，P2 {p2_total} 项。", ""]

    if results:
        lines += ["| 文件 | 级别 | 规则 | 位置 | 说明 |", "|---|---|---|---|---|"]
        for path, findings in results:
            for item in findings:
                location = f"第 {item['line']} 行" if item["line"] else "整文件"
                lines.append(f"| `{path.name}` | {item['level']} | {item['rule']} | {location} | {item['detail']} |")
        lines += [
            "",
            "## 处理建议",
            "",
            "- L1/L2/L3/L8 属交付阻塞项：吞异常、写死本机路径、随机不可复现、遗留待办都要在交付前清掉。",
            "- L4/L5/L6/L7/L9 属观感与整洁度问题，按需修；L6/L7 是最典型的\"AI 味\"特征。",
        ]
    else:
        lines.append("未发现机械性可判定的问题。")

    report = "\n".join(lines) + "\n"
    print(report)
    target = Path(args.out) if args.out else (project_work(args.project) / "代码体检.md" if args.project
                                             else code_dir / "代码体检.md")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(report, encoding="utf-8")
    print(f"[写出] {rel(target)}")
    return 1 if p1_total else 0


if __name__ == "__main__":
    raise SystemExit(main())
