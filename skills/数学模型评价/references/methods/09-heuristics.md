# 启发式与多目标：方案审查卡

核查来源状态见 [登记表](../sources-methods.json)。以下“误用”是风险检查点，发现相关证据后才能认定缺陷，不能仅凭使用了某方法扣分。

## GA遗传算法
- 前提与数据：编码、可行修复和适应度对应原问题。
- 常见误用：罚函数优秀值当可行最优；未控制预算。
- 求解设计：选择交叉变异与精英；说明参数。
- 验证计划：独立种子、同预算基线和可行性复查。
- 来源线索：[pymoo GA](https://pymoo.org/algorithms/soo/ga.html)；定位：Genetic Algorithm；具体主张运行时复核。

## PSO粒子群
- 前提与数据：连续编码适用或离散映射有依据。
- 常见误用：越界修复改变含义；一次收敛宣称全局最优。
- 求解设计：速度位置更新、边界与停止规则。
- 验证计划：种子分布、约束残差、预算公平。
- 来源线索：[pymoo PSO](https://pymoo.org/algorithms/soo/pso.html)；定位：Particle Swarm Optimization；具体主张运行时复核。

## SA模拟退火
- 前提与数据：邻域连通与目标定义合理。
- 常见误用：有限退火运行援引渐近定理作最优证明。
- 求解设计：温度、接受概率、降温与重启。
- 验证计划：多次运行、温度敏感性和小例最优差距。
- 来源线索：[SciPy optimization](https://docs.scipy.org/doc/scipy/reference/optimize.html)；定位：Optimization / Linear programming / MILP；具体主张运行时复核。

## NSGA-II
- 前提与数据：多目标冲突有意义，目标量纲与约束清楚。
- 常见误用：Pareto解集等于唯一最佳；忽略不可行支配。
- 求解设计：非支配排序与拥挤度；后续偏好选择透明。
- 验证计划：可行性、重复种子、参考点一致的指标。
- 来源线索：[pymoo NSGA-II](https://pymoo.org/algorithms/moo/nsga2.html)；定位：Rank and crowding selection；具体主张运行时复核。

## 差分进化 DE
- 前提与数据：连续变量及边界合理。
- 常见误用：把求解器global文字当有限运行证书。
- 求解设计：变异交叉与选择；约束方式明确。
- 验证计划：多种子、评价次数、最优界或小例差距。
- 来源线索：[SciPy optimization](https://docs.scipy.org/doc/scipy/reference/optimize.html)；定位：Optimization / Linear programming / MILP；具体主张运行时复核。
