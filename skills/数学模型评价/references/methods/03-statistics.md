# 回归与统计：方案审查卡

核查来源状态见 [登记表](../sources-methods.json)。以下“误用”是风险检查点，发现相关证据后才能认定缺陷，不能仅凭使用了某方法扣分。

## OLS/WLS/GLS
- 前提与数据：明确条件均值、误差相关及方差结构。
- 常见误用：要求因变量本身正态；把相关系数当因果。
- 求解设计：最小二乘；异方差时考虑稳健标准误/WLS。
- 验证计划：残差、杠杆点、共线性与留出误差；正态主要关乎特定有限样本推断。
- 来源线索：[statsmodels Linear Regression](https://www.statsmodels.org/stable/regression.html)；定位：Model classes / Examples；具体主张运行时复核。

## Logistic/Poisson GLM
- 前提与数据：响应分布与连接函数匹配；计数需暴露量。
- 常见误用：连续值硬做分类；过度离散不检查。
- 求解设计：极大似然；分离或离散问题另作处理。
- 验证计划：校准/离差/残差，按任务选指标。
- 来源线索：[statsmodels Generalized Linear Models](https://www.statsmodels.org/stable/glm.html)；定位：Technical Documentation; conditional mean and family；具体主张运行时复核。

## Ridge/Lasso
- 前提与数据：高相关或多变量；正则强度在训练内选。
- 常见误用：全数据标准化或用测试集调参。
- 求解设计：交叉验证管道；特征尺度统一。
- 验证计划：嵌套验证、系数稳定性和朴素基线。
- 来源线索：[scikit-learn Common pitfalls](https://scikit-learn.org/stable/common_pitfalls.html)；定位：Data leakage / Inconsistent preprocessing；具体主张运行时复核。

## 假设检验/ANOVA
- 前提与数据：抽样独立性、配对和检验目标明确。
- 常见误用：p大等于证明无差异，多次检验不控制。
- 求解设计：根据设计选参数/非参数/置换检验。
- 验证计划：效应量与区间、多重比较和功效局限。
- 来源线索：[statsmodels Linear Regression](https://www.statsmodels.org/stable/regression.html)；定位：Model classes / Examples；具体主张运行时复核。

## 成分数据 ALR/CLR/ILR
- 前提与数据：比例闭合与零值机制明确。
- 常见误用：原始比例相关直接解释机制；宣称CLR唯一合法。
- 求解设计：按问题选对数比、组成模型或适当约束模型。
- 验证计划：零替换敏感性、子组成及坐标解释；CLR协方差奇异。
- 来源线索：[scikit-bio Composition Statistics](https://scikit.bio/docs/dev/generated/skbio.stats.composition.html)；定位：clr / ilr / alr and zero replacement；具体主张运行时复核。
