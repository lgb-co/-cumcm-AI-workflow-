"""在工作区内创建/补全 Python 虚拟环境 工具/code_env（门禁 G2 的补齐手段）。

用法：
    python bootstrap_env.py --status                 # 只看现状
    python bootstrap_env.py --install                # 装核心包
    python bootstrap_env.py --install scipy,pulp     # 装指定包
    python bootstrap_env.py --install-optional       # 装常用扩展包
    python bootstrap_env.py --run "code/q1.py"       # 用该环境运行脚本

约束：只写工作区内的 工具/code_env，不修改系统 Python。
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _paths import CODE_ENV_PYTHON, OCR_ENV_PYTHON, TOOLS_DIR, WORKSPACE_DIR, rel  # noqa: E402

CORE = ["numpy", "scipy", "pandas", "matplotlib"]
OPTIONAL = [
    "scikit-learn",
    "statsmodels",
    "seaborn",
    "openpyxl",
    "networkx",
    "sympy",
    "pulp",
    "python-docx",
    "pyyaml",
    "imageio",
    "tqdm",
    "joblib",
]
ALIASES = {
    "sklearn": "scikit-learn",
    "scikit_learn": "scikit-learn",
    "docx": "python-docx",
    "yaml": "pyyaml",
    "pillow": "pillow",
    "PIL": "pillow",
}


def venv_python() -> Path:
    return CODE_ENV_PYTHON


def base_python() -> Path:
    if OCR_ENV_PYTHON.exists():
        return OCR_ENV_PYTHON
    return Path(sys.executable)


def ensure_venv(verbose: bool = True) -> Path:
    target = TOOLS_DIR / "code_env"
    python = venv_python()
    if python.exists():
        return python
    base = base_python()
    if verbose:
        print(f"[创建] 用 {rel(base)} 生成虚拟环境 {rel(target)}")
    target.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([str(base), "-m", "venv", str(target)], check=True)
    subprocess.run([str(python), "-m", "pip", "install", "--upgrade", "pip", "-q"], check=False)
    return python


def normalize(packages: list[str]) -> list[str]:
    out: list[str] = []
    for name in packages:
        cleaned = name.strip()
        if not cleaned:
            continue
        out.append(ALIASES.get(cleaned, cleaned))
    return list(dict.fromkeys(out))


def status() -> int:
    python = venv_python()
    if not python.exists():
        print(f"虚拟环境未创建：{rel(python)}")
        print(f"创建命令：python {Path(__file__).name} --install")
        return 1
    result = subprocess.run(
        [str(python), "-c", "import sys;print(sys.version.split()[0])"],
        capture_output=True,
        text=True,
        check=False,
    )
    print(f"虚拟环境：{rel(python)}  Python {result.stdout.strip() or '未知'}")
    from importlib.metadata import distributions

    listed = subprocess.run(
        [str(python), "-m", "pip", "list", "--format=freeze"],
        capture_output=True,
        text=True,
        check=False,
    )
    names = {line.split("==")[0].lower() for line in listed.stdout.splitlines() if "==" in line}
    missing = [p for p in CORE + OPTIONAL if p.lower() not in names and p.replace("-", "_").lower() not in names]
    print("缺失（核心+常用）：" + (", ".join(missing) if missing else "无"))
    del distributions
    return 0


def install(packages: list[str], upgrade: bool = False) -> int:
    python = ensure_venv()
    if not packages:
        print("没有指定要安装的包。")
        return 2
    cmd = [str(python), "-m", "pip", "install", "--disable-pip-version-check", "--no-input"]
    if upgrade:
        cmd.append("--upgrade")
    cmd += packages
    print("[安装] " + " ".join(packages))
    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        print("[失败] 安装未完成，检查网络或包名；命令：" + " ".join(cmd))
    return result.returncode


def run(script: str, extra: list[str]) -> int:
    python = ensure_venv()
    target = Path(script)
    if not target.is_absolute():
        target = WORKSPACE_DIR / target
    if not target.exists():
        print(f"[失败] 找不到脚本 {target}")
        return 2
    print(f"[运行] {rel(python)} {rel(target)}")
    return subprocess.run([str(python), str(target), *extra], cwd=str(target.parent), check=False).returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="工作区 Python 环境引导")
    parser.add_argument("--status", action="store_true", help="查看虚拟环境与包状态")
    parser.add_argument("--install", nargs="*", default=None, help="安装核心包或指定包")
    parser.add_argument("--install-optional", action="store_true", help="安装常用扩展包")
    parser.add_argument("--upgrade", action="store_true", help="升级已装包")
    parser.add_argument("--run", default="", help="用工作区环境运行脚本")
    parser.add_argument("extra", nargs="*", help="传给 --run 脚本的参数")
    args = parser.parse_args()

    if args.status:
        return status()
    if args.install_optional:
        return install(normalize(CORE + OPTIONAL), args.upgrade)
    if args.install is not None:
        packages = normalize(args.install) or list(CORE)
        return install(packages, args.upgrade)
    if args.run:
        return run(args.run, args.extra)
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
