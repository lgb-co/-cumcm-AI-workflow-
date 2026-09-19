"""总运行入口：按小问顺序执行，产出 tables/ 与 figures/。

用法：
    python run_all.py                # 全部小问
    python run_all.py --seed 7       # 指定随机种子（第三轮自测使用）
    python run_all.py --verify       # 校验模式：与基准结果比对（第二轮自测使用）
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import FIGURE_DIR, SEED, TABLE_DIR  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--verify", action="store_true", help="只做数值校验，不重画图")
    args = parser.parse_args()

    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    started = time.time()
    print(f"[运行] seed={args.seed} verify={args.verify}")

    # 示例：按小问顺序调用
    # from q1_model import run
    # run(seed=args.seed)
    # from q2_model import run as run_q2
    # run_q2(seed=args.seed)

    print(f"[完成] 用时 {time.time() - started:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
