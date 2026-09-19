"""卡方检验（Python 最小可运行模板）

内容：列联表独立性检验 + 拟合优度检验；同时给出期望频数是否满足 ≥5 的适用性判断。
接口：solve(table) -> (卡方值, p 值, 自由度, 期望频数)；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_table  # noqa: E402


def build_demo() -> dict:
    observed = np.array([[42, 30, 18], [28, 45, 37]])
    return {"table": observed, "rows": ["低风险", "高风险"], "cols": ["方案A", "方案B", "方案C"]}


def solve(table):
    table = np.asarray(table, float)
    chi2, p, dof, expected = stats.chi2_contingency(table)
    ratio = float((expected < 5).mean())
    return float(chi2), float(p), int(dof), expected, ratio


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    chi2, p, dof, expected, ratio = solve(data["table"])
    report("卡方检验", 卡方值=round(chi2, 4), p值=f"{p:.4f}", 自由度=dof,
           结论="独立（无关）" if p >= 0.05 else "不独立（相关）",
           期望频数不足5的比例=f"{ratio:.0%}")
    save_table(__file__, "期望频数", {"行": np.repeat(data["rows"], len(data["cols"])),
                                      "列": np.tile(data["cols"], len(data["rows"])),
                                      "期望频数": np.round(expected.ravel(), 4)})
