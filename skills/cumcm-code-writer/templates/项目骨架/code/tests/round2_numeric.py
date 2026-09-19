"""第二轮自测：数值与算法正确性对照。

约定（selftest.py 会强制校验）：
    1. 退出码 0 视为通过；
    2. 必须打印一行机器可读汇总：
       `CHECK-SUMMARY total=<检查项数> passed=<通过数> baselines=<独立基准数>`
       要求 total ≥ 3、baselines ≥ 1，否则第二轮判"未通过（校验强度不足）"，阻塞交付；
    3. baseline 指由**另一条代码路径**算出的基准值：暴力枚举、解析解、成熟库实现或手算值。
       不允许把被测代码自己的输出当基准，否则等于没校验。
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

TOLERANCE = 1e-6
stats = {"total": 0, "passed": 0, "baselines": 0}


def check(name: str, actual: float, expected: float, tolerance: float = TOLERANCE,
          baseline: bool = True) -> bool:
    ok = abs(actual - expected) <= tolerance * max(1.0, abs(expected))
    print(f"[{'通过' if ok else '失败'}] {name}: 计算值={actual:.10g} 基准值={expected:.10g}")
    stats["total"] += 1
    stats["passed"] += int(ok)
    stats["baselines"] += int(baseline)
    return ok


def main() -> int:
    results: list[bool] = []

    # 示例：基准值取另一条路径的结果，而不是被测函数的返回值。
    # results.append(check("Q1 总面积", assemble_summary()["面积"].sum(), brute_force_total(), 1e-9))
    # results.append(check("Q2 最优值上界", lp_value, worst_random_feasible_value, 1e-6))
    # results.append(check("约束满足", float(plan.sum()), total_area, 1e-9, baseline=False))

    if not results:
        print("CHECK-SUMMARY total=0 passed=0 baselines=0")
        print("尚未编写校验项：请补充与解析解/暴力枚举/成熟库实现的对照，并保证 total≥3、baselines≥1。")
        return 1

    ok = all(results)
    print(f"CHECK-SUMMARY total={stats['total']} passed={stats['passed']} baselines={stats['baselines']}")
    print(f"[结论] {stats['passed']}/{stats['total']} 项通过，独立基准 {stats['baselines']} 项")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())