# 聚类分类与降维：方案审查卡

核查来源状态见 [登记表](../sources-methods.json)。以下“误用”是风险检查点，发现相关证据后才能认定缺陷，不能仅凭使用了某方法扣分。

## K-means
- 前提与数据：数值距离及近球状簇近似合理。
- 常见误用：类别编码直接当距离；所有数据定缩放。
- 求解设计：多初始点聚类；训练预处理。
- 验证计划：轮廓系数、稳定性、离群点与业务解释。
- 来源线索：[scikit-learn User Guide](https://scikit-learn.org/stable/user_guide.html)；定位：Supervised / Unsupervised learning；具体主张运行时复核。

## 层次聚类/DBSCAN
- 前提与数据：连接法或密度尺度适合数据。
- 常见误用：不同密度用单阈值；高维距离失效不检查。
- 求解设计：层次距离/密度邻域；说明参数来源。
- 验证计划：参数扰动、噪声比例、重抽样稳定性。
- 来源线索：[scikit-learn User Guide](https://scikit-learn.org/stable/user_guide.html)；定位：Supervised / Unsupervised learning；具体主张运行时复核。

## PCA
- 前提与数据：变量尺度可比、线性子空间有意义。
- 常见误用：高解释方差等于高预测力；全数据拟合PCA。
- 求解设计：只训练集拟合中心化/缩放/PCA。
- 验证计划：载荷、稳定性、目标保留度；主成分符号可翻转。
- 来源线索：[scikit-learn Common pitfalls](https://scikit-learn.org/stable/common_pitfalls.html)；定位：Data leakage / Inconsistent preprocessing；具体主张运行时复核。

## SVM/SVR
- 前提与数据：核、尺度和参数范围合理。
- 常见误用：小样本测试集重复调参。
- 求解设计：管道内缩放并验证C/gamma/epsilon。
- 验证计划：嵌套或独立验证、类别不平衡指标。
- 来源线索：[scikit-learn User Guide](https://scikit-learn.org/stable/user_guide.html)；定位：Supervised / Unsupervised learning；具体主张运行时复核。

## 随机森林/梯度提升
- 前提与数据：训练样本代表应用对象；标签可用。
- 常见误用：特征重要度等于因果；组间泄漏。
- 求解设计：训练内调参；按人/地点/时间分组。
- 验证计划：校准、组外泛化和置换重要性局限。
- 来源线索：[scikit-learn Common pitfalls](https://scikit-learn.org/stable/common_pitfalls.html)；定位：Data leakage / Inconsistent preprocessing；具体主张运行时复核。
