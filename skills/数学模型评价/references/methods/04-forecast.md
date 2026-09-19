# 时序预测：方案审查卡

核查来源状态见 [登记表](../sources-methods.json)。以下“误用”是风险检查点，发现相关证据后才能认定缺陷，不能仅凭使用了某方法扣分。

## ARIMA/SARIMA
- 前提与数据：时间间隔、差分和季节周期明确。
- 常见误用：随机拆分未来样本；过度差分。
- 求解设计：训练窗口定阶和估参。
- 验证计划：滚动起点评价，残差自相关与预测区间。
- 来源线索：[Forecasting: Principles and Practice](https://otexts.com/fpp3/tscv.html)；定位：Time series cross-validation；具体主张运行时复核。

## ETS/指数平滑
- 前提与数据：趋势季节结构适合；乘法形式需合适取值。
- 常见误用：把拟合精度当外推精度。
- 求解设计：状态空间平滑；训练内选择结构。
- 验证计划：多步回测、朴素和季节朴素基线。
- 来源线索：[Forecasting: Principles and Practice](https://otexts.com/fpp3/tscv.html)；定位：Time series cross-validation；具体主张运行时复核。

## VAR
- 前提与数据：多变量时间序列，同步且样本支持参数量。
- 常见误用：高维短序列直接高阶VAR。
- 求解设计：定阶、平稳/协整检查及约束。
- 验证计划：滚动预测、稳定性与参数数量。
- 来源线索：[Forecasting: Principles and Practice](https://otexts.com/fpp3/tscv.html)；定位：Time series cross-validation；具体主张运行时复核。

## GM(1,1)
- 前提与数据：明确正值/趋势及所用灰色模型变体。
- 常见误用：少数据就必适用；套级比检验不问前提。
- 求解设计：累加生成和参数估计需核对版本。
- 验证计划：外推回测、残差和趋势改变敏感性。
- 来源线索：[Deng 1982](https://doi.org/10.1016/S0167-6911(82)80025-X)；定位：Control problems of grey systems；具体主张运行时复核。

## LSTM/神经时序
- 前提与数据：足够有效样本和时间窗口；预测时特征可得。
- 常见误用：全序列归一化、未来特征泄漏。
- 求解设计：训练窗口构样本；早停只用验证段。
- 验证计划：与简单基线同窗口比较、重复种子和多步误差。
- 来源线索：[scikit-learn Common pitfalls](https://scikit-learn.org/stable/common_pitfalls.html)；定位：Data leakage / Inconsistent preprocessing；具体主张运行时复核。
