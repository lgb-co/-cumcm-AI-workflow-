# 规划优化：方案审查卡

核查来源状态见 [登记表](../sources-methods.json)。以下“误用”是风险检查点，发现相关证据后才能认定缺陷，不能仅凭使用了某方法扣分。

## 线性规划 LP
- 前提与数据：目标及约束线性，连续变量；需完整系数、方向和边界。
- 常见误用：用整数含义变量求连续解后直接四舍五入。
- 求解设计：HiGHS等LP求解器；核对可行性、状态和对偶界。
- 验证计划：逐约束残差、小实例手算、对偶或灵敏度。
- 来源线索：[SciPy optimization](https://docs.scipy.org/doc/scipy/reference/optimize.html)；定位：Optimization / Linear programming / MILP；具体主张运行时复核。

## 混合整数规划 MILP
- 前提与数据：线性结构且部分变量离散；需逻辑约束、上下界。
- 常见误用：Big-M任意极大、遗漏互斥或容量。
- 求解设计：分支定界/割平面；报告限时、incumbent和gap。
- 验证计划：枚举小例，复核整数性与约束；有解不等于已证最优。
- 来源线索：[SciPy optimization](https://docs.scipy.org/doc/scipy/reference/optimize.html)；定位：Optimization / Linear programming / MILP；具体主张运行时复核。

## 非线性/凸规划
- 前提与数据：识别凸性、可微性和约束；需函数定义域。
- 常见误用：局部解冒称全局，忽视尺度和不可行初值。
- 求解设计：按结构选SLSQP、trust-constr或凸求解器。
- 验证计划：梯度检验、KKT条件与多初值；KKT充分性需条件。
- 来源线索：[SciPy optimization](https://docs.scipy.org/doc/scipy/reference/optimize.html)；定位：Optimization / Linear programming / MILP；具体主张运行时复核。

## 动态规划
- 前提与数据：状态具有所需充分信息、转移和边界明确。
- 常见误用：状态遗漏历史依赖，状态空间爆炸未估算。
- 求解设计：Bellman递推、记忆化；说明阶段与终止。
- 验证计划：小状态穷举、边界状态与策略可行性。
- 来源线索：[Sutton Barto Reinforcement Learning](http://incompleteideas.net/book/the-book-2nd.html)；定位：Dynamic programming and Markov decision processes；具体主张运行时复核。

## 随机规划
- 前提与数据：概率/场景有依据；决策时序明确。
- 常见误用：提前使用未来信息，场景权重任意。
- 求解设计：样本平均近似/场景树；非预见性约束。
- 验证计划：独立场景验证与样本量收敛。
- 来源线索：[Pyomo PyROS](https://pyomo.readthedocs.io/en/stable/explanation/solvers/pyros.html)；定位：Two-stage robust optimization；具体主张运行时复核。

## 鲁棒优化
- 前提与数据：不确定集有解释、预算及决策可调性明确。
- 常见误用：任意扩大不确定集造成不可行或过保守。
- 求解设计：鲁棒对应/约束生成；区分两阶段和静态。
- 验证计划：极端情景、保守性与名义方案成本比较。
- 来源线索：[Pyomo PyROS](https://pyomo.readthedocs.io/en/stable/explanation/solvers/pyros.html)；定位：Two-stage robust optimization；具体主张运行时复核。
