"""技能内的路径解析：所有脚本共用，避免各自拼绝对路径。"""
from __future__ import annotations

import os
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
WORKSPACE_DIR = SKILL_DIR.parent
SCRIPTS_DIR = SKILL_DIR / "scripts"
TEMPLATES_DIR = SKILL_DIR / "templates"
REFERENCES_DIR = SKILL_DIR / "references"
LIBRARY_DIR = REFERENCES_DIR / "algorithm_library"
TOOLS_DIR = WORKSPACE_DIR / "工具"
def _config_code_env() -> Path | None:
    """读取安装时写入的 环境配置.json：技能被复制到别处后仍能找到可用运行环境。"""
    config = SKILL_DIR / "环境配置.json"
    if not config.exists():
        return None
    try:
        import json

        payload = json.loads(config.read_text(encoding="utf-8"))
    except Exception:
        return None
    candidate = str(payload.get("code_env", "")).strip()
    if not candidate:
        return None
    path = Path(candidate)
    return path if path.exists() else None


def _resolve_code_env() -> Path:
    """定位 Python 解释器：CUMCM_CODE_ENV → 环境配置.json → 工作区 工具/code_env → 当前解释器。"""
    override = os.environ.get("CUMCM_CODE_ENV", "").strip()
    if override:
        candidate = Path(override)
        python = candidate / "Scripts" / "python.exe" if candidate.is_dir() else candidate
        if python.exists():
            return python
    from_config = _config_code_env()
    if from_config:
        return from_config
    default = TOOLS_DIR / "code_env" / "Scripts" / "python.exe"
    return default if default.exists() else Path(os.sys.executable)


CODE_ENV_PYTHON = _resolve_code_env()
OCR_ENV_PYTHON = TOOLS_DIR / "ocr_env" / "Scripts" / "python.exe"
_PROJECT_OVERRIDE = os.environ.get("CUMCM_CODE_PROJECT", "").strip()
PROJECT_ROOT = Path(_PROJECT_OVERRIDE) if _PROJECT_OVERRIDE else SKILL_DIR

WORK_DIR = PROJECT_ROOT / "work"
OUTPUT_DIR = PROJECT_ROOT / "output"


def project_work(name: str) -> Path:
    """返回项目中间产物目录（自动创建）。"""
    path = WORK_DIR / name
    path.mkdir(parents=True, exist_ok=True)
    return path


def project_output(name: str) -> Path:
    """返回项目交付目录（自动创建）。"""
    path = OUTPUT_DIR / name
    path.mkdir(parents=True, exist_ok=True)
    return path


def rel(path: Path) -> str:
    """尽量给出相对工作区的可读路径。"""
    try:
        return str(path.resolve().relative_to(WORKSPACE_DIR)).replace("\\", "/")
    except ValueError:
        return str(path.resolve()).replace("\\", "/")
