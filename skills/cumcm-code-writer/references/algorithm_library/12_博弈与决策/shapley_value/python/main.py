"""Shapley 值 · 合作博弈收益分配（Python 最小可运行模板）

公式：φ_i = Σ_{S ⊆ N\{i}} |S|!(n-|S|-1)!/n! · [v(S ∪ {i}) - v(S)]
用于成本分摊/收益分配/贡献度量；本模板对小规模联盟（n ≤ 12）枚举全部子集。
接口：solve(n, value_fn) -> (Shapley 值, 贡献明细)；运行：python main.py
"""
from __future__ import annotations

import itertools
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_fig, save_table, set_style  # noqa: E402


def build_demo() -> dict:
    """三人成本分摊：合并建设费用低于单独建设之和（规模效应）。"""
    return {
        "n": 3,
        "costs": {(1,): 100.0, (2,): 120.0, (3,): 90.0,
                  (1, 2): 170.0, (1, 3): 150.0, (2, 3): 165.0,
                  (1, 2, 3): 200.0},
        "names": ["城市A", "城市B", "城市C"],
    }


def solve(n: int, costs: dict):
    players = list(range(1, n + 1))

    def value(subset):
        key = tuple(sorted(subset))
        return costs.get(key, 0.0)

    shapley = {player: 0.0 for player in players}
    details = []
    for player in players:
        others = [p for p in players if p != player]
        for size in range(len(others) + 1):
            for subset in itertools.combinations(others, size):
                weight = math.factorial(size) * math.factorial(n - size - 1) / math.factorial(n)
                marginal = value(tuple(subset) + (player,)) - value(subset)
                shapley[player] += weight * marginal
                details.append({"成员": player, "联盟S": str(tuple(sorted(subset))),
                                "|S|": size, "权重": round(weight, 6), "边际贡献": round(marginal, 4)})
    return shapley, details


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    shapley, details = solve(int(data["n"]), data["costs"])
    total = sum(shapley.values())
    report("Shapley 值", 分配=np.round([shapley[p] for p in sorted(shapley)], 4).tolist(),
           分配合计=round(total, 4), 大联盟成本=data["costs"][(1, 2, 3)],
           合理性="合计等于大联盟成本" if abs(total - data["costs"][(1, 2, 3)]) < 1e-6 else "需检查")
    save_table(__file__, "分配结果", {f"成员{i + 1}（{data['names'][i]}）": [round(shapley[i + 1], 6)]
                                      for i in range(int(data["n"]))})
    save_table(__file__, "边际贡献明细", details)
    weights = [shapley[p] for p in sorted(shapley)]
    plt = set_style()
    fig, ax = plt.subplots()
    ax.bar(data["names"], weights, color="#0072B2")
    for index, value in enumerate(weights):
        ax.text(index, value, f"{value:.1f}", ha="center", va="bottom", fontsize=9)
    ax.set_ylabel("分摊成本")
    ax.set_title("Shapley 值分配结果")
    save_fig(__file__, fig, "shapley_value")
