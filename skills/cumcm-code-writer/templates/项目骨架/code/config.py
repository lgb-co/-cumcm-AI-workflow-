"""项目参数集中管理：路径、随机种子、模型参数。

修改参数时同步更新注释中的公式编号与来源，便于写进论文与结果文档。
"""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "code" / "data"
TABLE_DIR = PROJECT_ROOT / "tables"
FIGURE_DIR = PROJECT_ROOT / "figures"
WORK_DIR = PROJECT_ROOT / "work"

SEED = 42  # 随机种子：随机算法必须固定，第三轮自测会换种子重跑

# 例：ALPHA = 0.5  # 式(3-4) 平滑系数，按 5.2 节敏感性分析取 0.5
