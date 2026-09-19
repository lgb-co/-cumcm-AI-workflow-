import numpy as np

# 定义输入参数
p1 = 0.2  # 零配件1的次品率
p2 = 0.2  # 零配件2的次品率
pf = 0.2  # 成品的次品率

cb1 = 4  # 零配件1的采购单价
cb2 = 18  # 零配件2的采购单价
cd1 = 1  # 零配件1的检测成本
cd2 = 1  # 零配件2的检测成本

ca = 6  # 成品的装配成本
cdf = 2  # 成品的检测成本
cd = 30  # 成品的调换损失
cr = 5  # 不合格成品的拆解费用

s = 56  # 成品的市场售价
Q = 100  # 假设生产的成品数量

# 初始化DP表和决策路径表
dp = {}
decision_path = {}

# 阶段3：不合格成品拆解与市场流转决策
# z=0: 不拆解，直接废弃；z=1: 拆解处理
dp[(3, 0)] = cd * Q
dp[(3, 1)] = cr * Q

# 阶段2：成品组装和检测决策
# y=0: 不检测成品；y=1: 检测成品
dp[(2, 0)] = (1 - pf) * s * Q + pf * dp[(3, 0)]
dp[(2, 1)] = -(cdf * Q) + (1 - pf) * s * Q + pf * dp[(3, 1)]

# 阶段1：零配件采购和检测决策
# x1, x2分别表示是否检测零配件1和2
dp[(1, 1, 1)] = -(cd1 * Q + cb1 * Q + cd2 * Q + cb2 * Q) + dp[(2, 1)]
dp[(1, 1, 0)] = -(cd1 * Q + cb1 * Q + cb2 * Q + p2 * cd * Q) + dp[(2, 1)]
dp[(1, 0, 1)] = -(cb1 * Q + cd2 * Q + cb2 * Q + p1 * cd * Q) + dp[(2, 1)]
dp[(1, 0, 0)] = -(cb1 * Q + cb2 * Q + p1 * cd * Q + p2 * cd * Q) + dp[(2, 1)]

# 输出所有决策方案及其对应的总成本
for state, cost in dp.items():
    print(f"状态: {state}, 总成本: {cost}")

optimal_value = max(dp.values())

# 输出最优结果
print("\n最小总成本:", optimal_value)

