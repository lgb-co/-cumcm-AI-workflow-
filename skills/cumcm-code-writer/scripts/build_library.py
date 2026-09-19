"""生成算法参考库的元数据、索引与清单，并可对 Python 模板做烟测。

用法：
    python build_library.py                 # 生成 meta.yaml + index.md + manifest.csv
    python build_library.py --smoke         # 再跑一遍全部 Python 模板并记录结果
    python build_library.py --smoke --matlab  # 若本机有 MATLAB，连 .m 模板一起跑（慢）

注册表 `registry.csv` 是元数据唯一来源；模板的依赖由脚本扫描源码自动识别。
"""
from __future__ import annotations

import argparse
import csv
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _paths import CODE_ENV_PYTHON, LIBRARY_DIR, WORKSPACE_DIR, rel  # noqa: E402

REGISTRY = LIBRARY_DIR / "registry.csv"
STDLIB = set(getattr(sys, "stdlib_module_names", set()))
SKIP_IMPORTS = {"__future__", "mmlib", "typing", "warnings", "collections"}

ML_TOOLBOX_HINTS = {
    "stats": ["fitlm", "fitcnb", "fitctree", "fitcknn", "fitcsvm", "fitglm", "fitgmdist", "fitcdiscr",
              "treebagger", "fitensemble", "sequentialfs", "tsne", "factoran", "anova1", "multcompare",
              "kfoldloss", "crossval", "perfcurve", "vartestn", "jbtest", "canoncorr", "ridge", "pca"],
    "optim": ["linprog", "intlinprog", "fmincon", "lsqcurvefit"],
    "econ": ["arima", "estimate", "forecast"],
    "base": ["graph", "digraph", "shortestpath", "maxflow", "minspantree", "toposort", "dbscan", "kmeans",
             "linkage", "cluster", "silhouette", "ode45", "spline", "polyfit", "fillmissing", "zscore",
             "pdist", "squareform", "findedge", "imagesc", "histogram", "exportgraphics", "writetable"],
}


def read_registry() -> dict[str, dict]:
    with REGISTRY.open(encoding="utf-8-sig", newline="") as handle:
        return {row["id"]: row for row in csv.DictReader(handle)}


def scan_python_libs(path: Path) -> list[str]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8", errors="ignore")
    modules = set()
    for match in re.finditer(r"^\s*(?:from|import)\s+([A-Za-z_][\w\.]*)", text, re.M):
        root = match.group(1).split(".")[0]
        if root in STDLIB or root in SKIP_IMPORTS or root.startswith("_"):
            continue
        modules.add(root)
    return sorted(modules)


def scan_matlab_tools(path: Path) -> list[str]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8", errors="ignore").lower()
    found = []
    for toolbox, functions in ML_TOOLBOX_HINTS.items():
        if any(re.search(rf"\b{fn}\s*\(", text) for fn in functions):
            found.append(toolbox)
    return sorted(found)


def collect_algorithms() -> list[dict]:
    items = []
    for category_dir in sorted(p for p in LIBRARY_DIR.iterdir() if p.is_dir() and not p.name.startswith("_")):
        for algo_dir in sorted(p for p in category_dir.iterdir() if p.is_dir()):
            items.append({
                "id": algo_dir.name,
                "category": category_dir.name,
                "dir": algo_dir,
                "python": algo_dir / "python" / "main.py",
                "matlab": algo_dir / "matlab" / "main.m",
            })
    return items


def write_meta(item: dict, row: dict, py_libs: list[str], ml_tools: list[str]) -> Path:
    meta = item["dir"] / "meta.yaml"
    lines = [
        f"id: {item['id']}",
        f"name_zh: {row.get('name_zh', item['id'])}",
        f"category: {item['category']}",
        f"problem_types: {row.get('problem_types', '')}",
        f"family: {row.get('family', '')}",
        "language:",
        f"  python: {'python/main.py' if item['python'].exists() else 'missing'}",
        f"  matlab: {'matlab/main.m' if item['matlab'].exists() else 'missing'}",
        "python_libs: [" + ", ".join(py_libs) + "]",
        "matlab_toolboxes: [" + ", ".join(ml_tools) + "]",
        f"assumptions: {row.get('assumptions', '')}",
        f"pitfalls: {row.get('pitfalls', '')}",
        f"source: {row.get('source', '')}",
        f"license: {row.get('license', 'unknown')}",
        "interface:",
        "  input: 见脚本 build_demo() 中的演示数据与 solve() 形参",
        "  output: out/ 下的 CSV 结果表与（如涉及）PNG/PDF 图",
    ]
    meta.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return meta


def smoke(item: dict, use_matlab: bool, timeout: int) -> dict:
    python = str(CODE_ENV_PYTHON) if CODE_ENV_PYTHON.exists() else sys.executable
    results = {}
    for lang, command in (
        ("python", [python, str(item["python"])]),
        ("matlab", ["matlab", "-batch", f"run('{item['matlab'].as_posix()}')"] if use_matlab else None),
    ):
        path = item[lang]
        if command is None or not path.exists():
            results[lang] = {"status": "skipped", "seconds": 0.0, "note": "未运行"}
            continue
        started = time.time()
        proc = subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)
        results[lang] = {
            "status": "pass" if proc.returncode == 0 else "fail",
            "seconds": round(time.time() - started, 1),
            "note": (proc.stderr.strip().splitlines() or [""])[-1][:160],
        }
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="构建算法库索引与清单")
    parser.add_argument("--smoke", action="store_true", help="运行 Python 模板做烟测")
    parser.add_argument("--matlab", action="store_true", help="烟测时一并运行 MATLAB 模板")
    parser.add_argument("--timeout", type=int, default=600, help="单个模板超时秒数")
    args = parser.parse_args()

    registry = read_registry()
    items = collect_algorithms()
    manifest_rows, problems = [], []
    for item in items:
        row = registry.get(item["id"], {})
        if not row:
            problems.append(f"{item['id']} 未在 registry.csv 登记")
        py_libs = scan_python_libs(item["python"])
        ml_tools = scan_matlab_tools(item["matlab"])
        write_meta(item, row, py_libs, ml_tools)
        result = smoke(item, args.matlab, args.timeout) if args.smoke else {
            "python": {"status": "ready" if item["python"].exists() else "missing", "seconds": 0.0, "note": ""},
            "matlab": {"status": "ready" if item["matlab"].exists() else "missing", "seconds": 0.0, "note": ""},
        }
        manifest_rows.append({
            "id": item["id"],
            "name_zh": row.get("name_zh", ""),
            "category": item["category"],
            "python": rel(item["python"]),
            "matlab": rel(item["matlab"]),
            "python_libs": ";".join(py_libs),
            "matlab_toolboxes": ";".join(ml_tools),
            "license": row.get("license", ""),
            "source": row.get("source", ""),
            "python_status": result["python"]["status"],
            "python_seconds": result["python"]["seconds"],
            "matlab_status": result["matlab"]["status"],
            "matlab_seconds": result["matlab"]["seconds"],
            "note": result["python"]["note"] or result["matlab"]["note"],
        })

    for algo_id in sorted(set(registry) - {item["id"] for item in items}):
        problems.append(f"registry.csv 中的 {algo_id} 没有对应模板目录")

    with (LIBRARY_DIR / "manifest.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(manifest_rows[0].keys()))
        writer.writeheader()
        writer.writerows(manifest_rows)

    index_lines = [
        "# 算法参考库索引",
        "",
        f"> 模板总数：{len(manifest_rows)} 个；每个模板含 Python 与 MATLAB 最小可运行实现、演示数据与 `meta.yaml`。",
        f"> 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}；明细见 `manifest.csv`。",
        "",
        "用法：命中算法 → 读该目录的 `meta.yaml`（成立条件与常见坑）与 `python/main.py`（接口与数据约定）→ 按用户题目重写，而不是整段复制。",
        "",
    ]
    categories = {}
    for row in manifest_rows:
        categories.setdefault(row["category"], []).append(row)
    for category, rows in categories.items():
        index_lines += [f"## {category}（{len(rows)}）", "",
                        "| 算法 | 适用题型 | Python 依赖 | MATLAB 工具箱 | 状态 |", "|---|---|---|---|---|"]
        for row in rows:
            status = f"py={row['python_status']}/ml={row['matlab_status']}"
            index_lines.append(
                f"| `{row['id']}` {row['name_zh']} | {registry.get(row['id'], {}).get('problem_types', '')} | "
                f"{row['python_libs'] or '-'} | {row['matlab_toolboxes'] or '-'} | {status} |"
            )
        index_lines.append("")
    (LIBRARY_DIR / "index.md").write_text("\n".join(index_lines), encoding="utf-8")

    print(f"[完成] 模板 {len(manifest_rows)} 个；写出 manifest.csv 与 index.md")
    for item in problems:
        print(f"[注意] {item}")
    if args.smoke:
        failed = [row["id"] for row in manifest_rows if "fail" in {row["python_status"], row["matlab_status"]}]
        print(f"[烟测] 失败 {len(failed)} 个" + (f"：{', '.join(failed)}" if failed else ""))
        return 1 if failed else 0
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
