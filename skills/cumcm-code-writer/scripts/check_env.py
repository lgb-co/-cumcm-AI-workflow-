"""环境与工具检查（门禁 G2）。

用法：
    python check_env.py                                  # 只报默认核心环境
    python check_env.py --need numpy,scipy,matplotlib    # 额外检查答题所需包
    python check_env.py --need pulp --matlab-toolbox optim,stats --project demo

输出：Markdown 报告（默认打印，可 --md 落盘）+ JSON（--json），任一必需项缺失时退出码为 1。
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import subprocess
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _paths import CODE_ENV_PYTHON, OCR_ENV_PYTHON, WORKSPACE_DIR, project_work, rel  # noqa: E402

CORE_PACKAGES = ["numpy", "scipy", "pandas", "matplotlib"]
OPTIONAL_PACKAGES = [
    "sklearn",
    "statsmodels",
    "seaborn",
    "openpyxl",
    "networkx",
    "sympy",
    "pulp",
    "docx",
    "yaml",
    "imageio",
    "tqdm",
    "joblib",
]
CHINESE_FONTS = ["SimHei", "Microsoft YaHei", "SimSun", "KaiTi", "FangSong"]
MATLAB_CANDIDATES = [r"D:\matlab\bin\matlab.exe", r"C:\Program Files\MATLAB"]
MATLAB_TOOLBOX_DIRS = {
    "optim": "optim",
    "optimization": "optim",
    "stats": "stats",
    "statistics": "stats",
    "symbolic": "symbolic",
    "econ": "econ",
    "econometrics": "econ",
    "simulink": "simulink",
    "control": "control",
    "fuzzy": "fuzzy",
    "globaloptim": "gads",
    "deeplearning": "nnet",
}


PLOT_PYTHON_DOWNLOAD = "https://www.python.org/downloads/"


def plot_env_status() -> dict:
    """交付图件必须由 Python 生成，因此单独探测绘图解释器。"""
    python = CODE_ENV_PYTHON
    if not Path(python).exists():
        return {"ok": False, "python": str(python), "detail": "未找到可用的 Python 解释器"}
    proc = subprocess.run([str(python), "-c", "import numpy, matplotlib"],
                          capture_output=True, text=True, check=False)
    if proc.returncode == 0:
        return {"ok": True, "python": str(python), "detail": "numpy 与 matplotlib 可用"}
    return {"ok": False, "python": str(python),
            "detail": (proc.stderr.strip().splitlines() or ["导入 numpy/matplotlib 失败"])[-1][:120]}


def _package_status(name: str) -> dict:
    spec = importlib.util.find_spec(name)
    if spec is None:
        return {"name": name, "ok": False, "version": None}
    try:
        ver = version(name)
    except PackageNotFoundError:
        ver = "unknown"
    return {"name": name, "ok": True, "version": ver}


def _find_matlab() -> Path | None:
    found = shutil.which("matlab")
    if found:
        return Path(found)
    for cand in MATLAB_CANDIDATES:
        path = Path(cand)
        if path.is_file():
            return path
        if path.is_dir():
            for exe in sorted(path.glob("**/bin/matlab.exe")):
                return exe
    return None


def _matlab_toolboxes(matlab_exe: Path, wanted: list[str]) -> list[dict]:
    root = matlab_exe.parent.parent / "toolbox"
    results = []
    for name in wanted:
        folder = MATLAB_TOOLBOX_DIRS.get(name.strip().lower(), name.strip().lower())
        results.append({"name": name, "ok": (root / folder).is_dir(), "path": str(root / folder)})
    return results


def _fonts_status() -> list[dict]:
    try:
        from matplotlib import font_manager
    except Exception as exc:  # matplotlib 不可用时无法判断
        return [{"name": "matplotlib", "ok": False, "version": f"import failed: {exc}"}]
    installed = {f.name for f in font_manager.fontManager.ttflist}
    return [{"name": f, "ok": f in installed, "version": None} for f in CHINESE_FONTS]


def _disk_status() -> dict:
    usage = shutil.disk_usage(str(WORKSPACE_DIR))
    return {
        "free_gb": round(usage.free / 1024**3, 1),
        "total_gb": round(usage.total / 1024**3, 1),
        "ok": usage.free / 1024**3 >= 5,
    }


def build_report(payload: dict) -> str:
    lines = ["# 环境与工具检查", ""]
    py = payload["python"]
    lines += [
        "## Python",
        "",
        f"- 当前解释器：`{py['executable']}`",
        f"- 版本：{py['version']}（要求 ≥3.10）",
        f"- 工作区虚拟环境：{'可用' if py['code_env'] else '未创建'} `{rel(CODE_ENV_PYTHON)}`",
        "",
        "## Python 包",
        "",
        "| 包 | 状态 | 版本 |",
        "|---|---|---|",
    ]
    for pkg in payload["packages"]:
        lines.append(f"| {pkg['name']} | {'可用' if pkg['ok'] else '缺失'} | {pkg['version'] or '-'} |")
    plot_env = payload["plot_env"]
    lines += [
        "",
        "## 绘图环境（交付图件必须由 Python 生成）",
        "",
        f"- 出图解释器：`{plot_env['python']}`",
        f"- 状态：{'可用' if plot_env['ok'] else '不可用'}（{plot_env['detail']}）",
        "- 规则：所有交付图件由 Python（matplotlib）绘制，MATLAB 只负责计算，不用 MATLAB 出图。",
        f"- 缺失时的处理：安装 Python 3.10+（{PLOT_PYTHON_DOWNLOAD}），"
        "再运行 `python scripts/bootstrap_env.py --install-optional`。",
        "",
        "## MATLAB",
        "",
    ]
    matlab = payload["matlab"]
    if matlab["executable"]:
        lines += [f"- 可执行文件：`{matlab['executable']}`", f"- 版本：{matlab['version'] or '未探测'}", ""]
        if matlab["toolboxes"]:
            lines += ["| 工具箱 | 状态 |", "|---|---|"]
            for box in matlab["toolboxes"]:
                lines.append(f"| {box['name']} | {'可用' if box['ok'] else '缺失'} |")
            lines.append("")
    else:
        lines += ["未找到 MATLAB；若本题需要 MATLAB，请先安装或在 `--need` 中改为 Python 依赖。", ""]
    lines += ["## 中文字体", "", "| 字体 | 状态 |", "|---|---|"]
    for font in payload["fonts"]:
        lines.append(f"| {font['name']} | {'可用' if font['ok'] else '缺失'} |")
    disk = payload["disk"]
    lines += [
        "",
        "## 磁盘",
        "",
        f"- 工作区所在盘剩余 {disk['free_gb']} GB / 共 {disk['total_gb']} GB（要求 ≥5 GB）",
        "",
        "## 结论",
        "",
    ]
    missing = payload["missing"]
    lines.append("环境齐备，可继续到 G3 与写码阶段。" if not missing else "存在缺失项，先补齐再写码：")
    for item in missing:
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="检查写码所需的环境与工具")
    parser.add_argument("--need", default="", help="逗号分隔的额外 Python 包（如 pulp,cvxpy）")
    parser.add_argument("--matlab-toolbox", default="", help="逗号分隔的 MATLAB 工具箱名")
    parser.add_argument("--project", default="", help="写入 work/<项目名>/环境快照.md")
    parser.add_argument("--md", default="", help="Markdown 输出路径")
    parser.add_argument("--json", default="", help="JSON 输出路径")
    args = parser.parse_args()

    extra = [p.strip() for p in args.need.split(",") if p.strip()]
    packages = [_package_status(p) for p in dict.fromkeys(CORE_PACKAGES + OPTIONAL_PACKAGES + extra)]

    matlab_exe = _find_matlab()
    wanted_boxes = [b.strip() for b in args.matlab_toolbox.split(",") if b.strip()]
    matlab = {
        "executable": str(matlab_exe) if matlab_exe else None,
        "version": None,
        "toolboxes": _matlab_toolboxes(matlab_exe, wanted_boxes) if matlab_exe else [],
    }

    payload = {
        "python": {
            "executable": sys.executable,
            "version": sys.version.split()[0],
            "code_env": CODE_ENV_PYTHON.exists(),
            "ocr_env": OCR_ENV_PYTHON.exists(),
        },
        "packages": packages,
        "matlab": matlab,
        "plot_env": plot_env_status(),
        "fonts": _fonts_status(),
        "disk": _disk_status(),
    }

    missing: list[str] = []
    if not payload["plot_env"]["ok"]:
        missing.append(
            "缺少绘图环境（Python + numpy + matplotlib）：交付图件必须由 Python 生成。"
            f"请安装 Python 3.10+（{PLOT_PYTHON_DOWNLOAD}）后运行 "
            "bootstrap_env.py --install-optional"
        )
    if tuple(map(int, sys.version.split()[0].split(".")[:2])) < (3, 10):
        missing.append(f"Python 版本过低：{payload['python']['version']}")
    for pkg in packages:
        if not pkg["ok"] and pkg["name"] in extra:
            missing.append(f"缺少 Python 包 {pkg['name']}：运行 bootstrap_env.py --install {pkg['name']}")
    for box in matlab["toolboxes"]:
        if not box["ok"]:
            missing.append(f"MATLAB 缺少工具箱 {box['name']}：请安装或改用 Python 实现")
    if not any(f["name"] == "SimHei" and f["ok"] for f in payload["fonts"]) and not any(
        f["name"] == "Microsoft YaHei" and f["ok"] for f in payload["fonts"]
    ):
        missing.append("未找到 SimHei / Microsoft YaHei：绘图前需确认中文字体")
    if not payload["disk"]["ok"]:
        missing.append(f"磁盘剩余空间不足：{payload['disk']['free_gb']} GB")
    payload["missing"] = missing

    report = build_report(payload)
    print(report)

    targets = [Path(args.md)] if args.md else []
    if args.project:
        targets.append(project_work(args.project) / "环境快照.md")
    for target in targets:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(report, encoding="utf-8")
        print(f"[写出] {rel(target)}")
    if args.json:
        Path(args.json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[写出] {args.json}")

    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
