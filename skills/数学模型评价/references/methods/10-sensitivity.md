# 敏感性与稳健性：方案审查卡

核查来源状态见 [登记表](../sources-methods.json)。以下“误用”是风险检查点，发现相关证据后才能认定缺陷，不能仅凭使用了某方法扣分。

## 局部敏感性/有限差分
- 前提与数据：考察点和扰动单位明确。
- 常见误用：单变量局部结果冒称全局稳健。
- 求解设计：解析导数或中心差分；步长有量纲。
- 验证计划：步长变化和不同基点，报告相对/绝对定义。
- 来源线索：[SALib Basics](https://salib.readthedocs.io/en/latest/user_guide/basics.html)；定位：Sampling / Run model / Analyze；具体主张运行时复核。

## Sobol全局敏感性
- 前提与数据：输入分布及经典独立性前提明确。
- 常见误用：相关输入直接套经典独立分解。
- 求解设计：匹配采样设计与分析器；足够样本。
- 验证计划：置信区间、样本收敛和一阶/总阶解释。
- 来源线索：[SALib Basics](https://salib.readthedocs.io/en/latest/user_guide/basics.html)；定位：Sampling / Run model / Analyze；具体主张运行时复核。

## Morris筛选
- 前提与数据：参数范围和尺度有意义。
- 常见误用：筛选排名当精确方差贡献。
- 求解设计：轨迹采样并分析均值绝对效应/离散度。
- 验证计划：轨迹数稳定性、非线性与交互线索。
- 来源线索：[SALib Basics](https://salib.readthedocs.io/en/latest/user_guide/basics.html)；定位：Sampling / Run model / Analyze；具体主张运行时复核。

## 情景/消融/稳健性比较
- 前提与数据：情景涵盖关键变化，消融只改变目标组件。
- 常见误用：任意小扰动证明所有情形；不公平预算。
- 求解设计：固定评测条件，分别改变假设或步骤。
- 验证计划：最坏/常态情景、差异区间、失效边界。
- 来源线索：[scikit-learn Common pitfalls](https://scikit-learn.org/stable/common_pitfalls.html)；定位：Data leakage / Inconsistent preprocessing；具体主张运行时复核。
