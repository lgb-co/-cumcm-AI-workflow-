# 机理方程与数值计算：方案审查卡

核查来源状态见 [登记表](../sources-methods.json)。以下“误用”是风险检查点，发现相关证据后才能认定缺陷，不能仅凭使用了某方法扣分。

## ODE/传染病SIR/种群模型
- 前提与数据：状态、单位、初值和守恒关系完整。
- 常见误用：数据拟合好就证明参数唯一可识别。
- 求解设计：按刚性选显式RK或隐式Radau/BDF。
- 验证计划：非负性/守恒、步长容差与参数可辨识。
- 来源线索：[SciPy solve_ivp](https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.solve_ivp.html)；定位：Parameters method / rtol / atol；具体主张运行时复核。

## PDE/有限差分
- 前提与数据：边界初值、域和离散格式明确。
- 常见误用：网格结果不做收敛或稳定性分析。
- 求解设计：时空离散后求解；说明稳定条件。
- 验证计划：网格加密、制造解/解析例、边界残差。
- 来源线索：[SciPy solve_ivp](https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.solve_ivp.html)；定位：Parameters method / rtol / atol；具体主张运行时复核。

## 插值/样条/数值积分
- 前提与数据：观测误差、区间和光滑性合理。
- 常见误用：插值当外推预测；高阶振荡忽略。
- 求解设计：按结构选分段样条、积分求积。
- 验证计划：节点留出、边界振荡和精度收敛。
- 来源线索：[SciPy Interpolation](https://docs.scipy.org/doc/scipy/reference/interpolate.html)；定位：Univariate interpolation / splines；具体主张运行时复核。

## 参数估计/反问题
- 前提与数据：可辨识性、误差模型与参数界明确。
- 常见误用：参数多于有效信息仍报唯一精确值。
- 求解设计：约束最小二乘/似然与正则。
- 验证计划：剖面或重抽样区间、多初值与合成恢复。
- 来源线索：[SciPy optimization](https://docs.scipy.org/doc/scipy/reference/optimize.html)；定位：Optimization / Linear programming / MILP；具体主张运行时复核。
