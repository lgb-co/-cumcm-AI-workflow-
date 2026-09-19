# -*- coding: utf-8 -*-
"""导出 Word 之前的环境检测：找齐可用工具，并给出推荐做法或“需要询问用户”的结论。

用法：
    python check_docx_toolchain.py
    python check_docx_toolchain.py --json
    python check_docx_toolchain.py --strict   # 导出链路不完整时退出码非 0

检测内容：解释器与包（python-docx/Pillow/matplotlib）、版式校验工具（LibreOffice/WPS/Word）、
在线兜底（latex.codecogs.com、mermaid.ink、kroki.io），并用一个试探公式实测本地渲染链路。
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

UA = {"User-Agent": "Mozilla/5.0 research-modeling-skill/1.0"}


def which(name: str) -> str | None:
    found = shutil.which(name)
    if found:
        return found
    roots = [os.environ.get("ProgramFiles", r"C:\Program Files"),
             os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")]
    for base in roots:
        if not base:
            continue
        root = Path(base)
        if not root.exists():
            continue
        for hit in root.glob(f"*/{name}"):
            return str(hit)
    return None


def detect_soffice() -> str | None:
    env = os.environ.get("MODELING_SOFFICE")
    if env and Path(env).exists():
        return env
    found = which("soffice.exe") or which("soffice")
    if found:
        return found
    for cand in (r"C:\Program Files\LibreOffice\program\soffice.exe",
                 r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
                 r"D:\LibreOffice\program\soffice.exe"):
        if Path(cand).exists():
            return cand
    return None


def detect_wps() -> dict:
    exes: list[str] = []
    for base in (r"D:\WPS Office", r"C:\Program Files\WPS Office",
                 r"C:\Program Files (x86)\Kingsoft", r"C:\Users\Public\Kingsoft"):
        root = Path(base)
        if root.exists():
            exes += [str(x) for x in list(root.glob("**/wps.exe"))[:3]]
    com = False
    try:
        import winreg
        for root in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
            for path in (r"SOFTWARE\Classes\KWPS.Application\CLSID",
                         r"SOFTWARE\Classes\CLSID\{000209FF-0000-4B30-A977-D214852036FF}\LocalServer32"):
                try:
                    with winreg.OpenKey(root, path) as key:
                        winreg.QueryValueEx(key, "")
                        com = True
                except OSError:
                    pass
    except Exception:
        pass
    return {"exe": exes, "com_registered": com}


def try_com(prog_id: str, timeout: int = 60) -> str:
    """真正实例化一次 COM 对象；只看注册表会误判（键存在但类未注册）。"""
    script = ("try { $a = New-Object -ComObject " + prog_id + "; try { $a.Quit() } catch {}; " + chr(39) + "OK" + chr(39) + " } "
              "catch { " + chr(39) + "FAIL: " + chr(39) + " + $_.Exception.Message }")
    try:
        out = subprocess.run(["powershell", "-NoProfile", "-Command", script],
                             capture_output=True, text=True, timeout=timeout)
        return (out.stdout or out.stderr).strip()[:160] or "无输出"
    except subprocess.TimeoutExpired:
        return "TIMEOUT"
    except Exception as exc:
        return "ERROR: " + str(exc)[:80]


def detect_word_com() -> bool:
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, r"Word.Application\CLSID"):
            return True
    except Exception:
        return False


def probe_url(url: str, timeout: int = 12) -> bool:
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return 200 <= getattr(resp, "status", 200) < 400
    except Exception:
        return False


def probe_mathtext() -> tuple[bool, str]:
    try:
        import matplotlib
        matplotlib.use("Agg")
        from matplotlib import mathtext
        target = Path(tempfile.gettempdir()) / "modeling_mathtext_probe.png"
        mathtext.math_to_image("$T_1=1$", str(target), dpi=120, format="png")
        ok = target.exists() and target.stat().st_size > 200
        return ok, "" if ok else "渲染结果为空"
    except Exception as exc:
        return False, str(exc)[:120]


def _config_interpreter_paths() -> list[str]:
    """读取安装时写入的环境配置（技能目录、同级 工具 目录），不写死机器路径。"""
    skill_dir = Path(__file__).resolve().parents[1]
    out: list[str] = []
    for f in (skill_dir / "环境配置.json", skill_dir.parent / "工具" / "环境配置.json"):
        if not f.exists():
            continue
        try:
            payload = json.loads(f.read_text(encoding="utf-8-sig"))
        except Exception:
            continue
        if not isinstance(payload, dict):
            continue
        for key in ("python", "modeling_py", "code_env", "python_path"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                out.append(value.strip())
    return out


def _toolkit_python_candidates() -> list[str]:
    """技能同级 工具/ 目录下的常见虚拟环境解释器（相对定位，不写盘符）。"""
    tools = Path(__file__).resolve().parents[1].parent / "工具"
    return [str(tools / "code_env" / "Scripts" / "python.exe"),
            str(tools / "ocr_env" / "Scripts" / "python.exe"),
            str(tools / "md2docx_env" / "Scripts" / "python.exe"),
            str(tools / "code_env" / "bin" / "python"),
            str(tools / "ocr_env" / "bin" / "python")]


def scan_interpreters() -> list[dict]:
    """候选解释器：环境变量 → 安装时写入的配置 → 工具虚拟环境 → 当前解释器 → PATH。"""
    import subprocess
    cands = [os.environ.get("MODELING_PY"), os.environ.get("CUMCM_PYTHON"),
             os.environ.get("CUMCM_CODE_ENV"), *_config_interpreter_paths(),
             *_toolkit_python_candidates(), sys.executable,
             shutil.which("python"), shutil.which("python3")]
    probe = ("import importlib.util as u;"
             "print(chr(44).join(m + chr(58) + (chr(49) if u.find_spec(m) else chr(48)) for m in [chr(100)+chr(111)+chr(99)+chr(120), m2, m3]))")
    probe = probe.replace("m2", repr("PIL")).replace("m3", repr("matplotlib"))
    seen, out = set(), []
    for c in cands:
        if not c:
            continue
        c = str(Path(c))
        if c in seen or not Path(c).exists():
            continue
        seen.add(c)
        try:
            r = subprocess.run([c, "-c", probe], capture_output=True, text=True, timeout=60)
            flags = dict(kv.split(":") for kv in (r.stdout or "").strip().split(",") if ":" in kv)
            out.append({"解释器": c, "python-docx": flags.get("docx") == "1",
                        "Pillow": flags.get("PIL") == "1", "matplotlib": flags.get("matplotlib") == "1"})
        except Exception as exc:
            out.append({"解释器": c, "错误": str(exc)[:60]})
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="DOCX 导出环境检测")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args()

    packages = {}
    for name in ("docx", "PIL", "matplotlib", "numpy"):
        try:
            __import__(name)
            packages[name] = True
        except Exception:
            packages[name] = False

    math_ok, math_err = probe_mathtext() if packages.get("matplotlib") else (False, "未安装 matplotlib")
    soffice = detect_soffice()
    wps = detect_wps()
    wps_probe = try_com("KWPS.Application") if wps["exe"] else "未安装 WPS"
    word_probe = try_com("Word.Application")
    wps["com_probe"] = wps_probe
    word = word_probe.startswith("OK")
    online = {
        "latex.codecogs.com": probe_url("https://latex.codecogs.com/png.latex?x%5E2"),
        "mermaid.ink": probe_url("https://mermaid.ink/"),
        "kroki.io": probe_url("https://kroki.io/"),
    }

    export_ready = bool(packages.get("docx") and packages.get("PIL")
                        and (math_ok or online["latex.codecogs.com"]))
    qa_ready = bool(soffice or wps_probe.startswith("OK") or word)

    print("=" * 66)
    print("DOCX 导出环境检测")
    print("=" * 66)
    print(f"解释器：{sys.executable} (Python {sys.version.split()[0]})")
    print("包：" + "、".join(f"{k}={'有' if v else '缺'}" for k, v in packages.items()))
    print("本地公式渲染(mathtext)：" + ("可用" if math_ok else f"不可用 {math_err}"))
    print(f"版式校验：LibreOffice={'有' if soffice else '无'}；"
          f"WPS={'有' if wps['exe'] else '无'}(实例化={wps_probe[:28]})；Word={word}(实例化={word_probe[:28]})")
    print("在线兜底：" + "、".join(f"{k}={'可达' if v else '不可达'}" for k, v in online.items()))
    print("-" * 66)
    print(f"能否写 DOCX：{'可以' if export_ready else '不可以'}")
    print(f"能否做页面级版式校验：{'可以' if qa_ready else '不可以（只能结构校验，请用户预览）'}")
    print("-" * 66)
    if export_ready:
        print("推荐做法：用本解释器运行 scripts/export_docx.py 生成 DOCX。")
    else:
        print("推荐做法：补齐 python-docx / Pillow / matplotlib，或用 MODELING_PY 指定带这些包的解释器；"
              "两者都不可行时询问用户。")
    if not qa_ready:
        print("提示：无版式校验工具时不要声称做过视觉检查，应报告“结构校验通过、版式请用户预览”。")

    print("-" * 66)
    print("候选解释器扫描（找齐 python-docx + Pillow + matplotlib 的即可用于导出）：")
    found = scan_interpreters()
    best = None
    for row in found:
        if "错误" in row:
            print(f"  - {row['解释器']} → 探测失败：{row['错误']}")
            continue
        mark = "✔" if (row["python-docx"] and row["Pillow"] and row["matplotlib"]) else " "
        print(f"  - [{mark}] {row['解释器']} docx={row['python-docx']} Pillow={row['Pillow']} matplotlib={row['matplotlib']}")
        if mark == "✔" and best is None:
            best = row["解释器"]
    if best and best != sys.executable:
        print(f"  建议：设置 MODELING_PY={best} 后再导出，可离线渲染公式。")
    elif best:
        print("  建议：当前解释器即可，无需切换。")
    else:
        print("  没有找到同时具备三个包的解释器：可先补装依赖，或改用在线公式兜底；仍不可行则询问用户。")
    if args.json:
        print(json.dumps({"解释器": sys.executable, "包": packages, "mathtext": math_ok,
                          "LibreOffice": soffice, "WPS": wps, "Word": word, "在线": online,
                          "可导出": export_ready, "可校验版式": qa_ready},
                         ensure_ascii=False, indent=2))
    if args.strict and not export_ready:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
