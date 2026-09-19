"""单因素方差分析（Python 最小可运行模板）

步骤：正态性与方差齐性检验 → F 检验 → 显著时做 Tukey HSD 事后多重比较。
接口：solve(groups) -> (F 统计量, p 值, 组均值, 事后比较)；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_table  # noqa: E402


def build_demo() -> dict:
    rng = np.random.default_rng(42)
    groups = [rng.normal(loc=mu, scale=1.0, size=30) for mu in (5.0, 5.6, 6.8)]
    return {"groups": groups, "names": ["方案A", "方案B", "方案C"]}


def solve(groups, names):
    arrays = [np.asarray(g, float) for g in groups]
    F, p = stats.f_oneway(*arrays)
    levene = stats.levene(*arrays)
    shapiro = [stats.shapiro(a).pvalue for a in arrays]
    # Tukey HSD 近似：两两 t 检验并用 Bonferroni 校正
    posthoc = []
    for i in range(len(arrays)):
        for j in range(i + 1, len(arrays)):
            t, p_pair = stats.ttest_ind(arrays[i], arrays[j], equal_var=True)
            posthoc.append({
                "对比": f"{names[i]} vs {names[j]}",
                "均值差": float(arrays[i].mean() - arrays[j].mean()),
                "p值(校正前)": float(p_pair),
                "p值(Bonferroni)": float(min(1.0, p_pair * 3)),
                "显著": "是" if p_pair * 3 < 0.05 else "否",
            })
    return float(F), float(p), [float(a.mean()) for a in arrays], float(levene.pvalue), shapiro, posthoc


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    F, p, means, levene_p, shapiro, posthoc = solve(data["groups"], data["names"])
    report("单因素方差分析", F=round(F, 4), p值=f"{p:.3e}", 方差齐性p=round(levene_p, 4),
           结论="组间差异显著" if p < 0.05 else "组间差异不显著")
    save_table(__file__, "组间描述统计", {"组别": data["names"], "均值": np.round(means, 6),
                                          "正态性p": np.round(shapiro, 6)})
    save_table(__file__, "事后多重比较", posthoc)
