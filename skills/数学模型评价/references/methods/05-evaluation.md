# 综合评价：方案审查卡

核查来源状态见 [登记表](../sources-methods.json)。以下“误用”是风险检查点，发现相关证据后才能认定缺陷，不能仅凭使用了某方法扣分。

## AHP
- 前提与数据：层级与专家成对判断有依据；正互反矩阵。
- 常见误用：将互反说成对称；为过CR随意改专家判断。
- 求解设计：特征向量或几何均值法注明；RI与矩阵阶数匹配。
- 验证计划：CR阈值及适用惯例要说明，0.1不是普适事实正确性证明。
- 来源线索：[pymcdm Subjective weights](https://pymcdm.readthedocs.io/en/master/modules/subjective_weights.html)；定位：2.2.1 AHP; displayed reciprocal matrix；具体主张运行时复核。

## TOPSIS
- 前提与数据：指标方向、尺度、权重与距离有解释。
- 常见误用：理想点接近度当真实效用；排名不稳定不检查。
- 求解设计：规范化、正负理想点和接近度。
- 验证计划：权重/规范化/候选集合变动敏感性。
- 来源线索：[pymcdm API](https://pymcdm.readthedocs.io/en/master/pymcdm.methods.html)；定位：TOPSIS；具体主张运行时复核。

## 熵权
- 前提与数据：非负规范化比例及常量列处理明确。
- 常见误用：差异大等于业务重要，噪声被高权重放大。
- 求解设计：按熵和差异度归一；处理0log0、零分母。
- 验证计划：异常点、常量指标、业务权重对照。
- 来源线索：[pymcdm Objective weights](https://pymcdm.readthedocs.io/en/master/modules/objective_weights.html)；定位：2.1.2 Entropy / CRITIC；具体主张运行时复核。

## CRITIC
- 前提与数据：标准化与相关度定义一致。
- 常见误用：负相关必应强化，重复指标仍重复加权。
- 求解设计：标准差与冲突信息组合，检查退化分母。
- 验证计划：相关结构扰动、重复列和尺度敏感性。
- 来源线索：[pymcdm Objective weights](https://pymcdm.readthedocs.io/en/master/modules/objective_weights.html)；定位：2.1.2 Entropy / CRITIC；具体主张运行时复核。

## DEA CCR/BCC
- 前提与数据：决策单元同质；投入产出与规模假设明确。
- 常见误用：效率为1当绝对优秀；投入产出过多弱区分。
- 求解设计：包络LP；说明投入/产出导向和规模报酬。
- 验证计划：异常值、同质性、前沿稳定性与松弛量。
- 来源线索：[Charnes Cooper Rhodes 1978](https://doi.org/10.1016/0377-2217(78)90138-8)；定位：Measuring the efficiency of decision making units；具体主张运行时复核。

## 灰色关联分析
- 前提与数据：参考序列、量纲化、分辨系数明确。
- 常见误用：关联度解释为因果或统计显著性。
- 求解设计：按明确变体算关联系数与聚合。
- 验证计划：参考序列、分辨系数和尺度敏感性。
- 来源线索：[Deng 1982](https://doi.org/10.1016/S0167-6911(82)80025-X)；定位：Control problems of grey systems；具体主张运行时复核。
