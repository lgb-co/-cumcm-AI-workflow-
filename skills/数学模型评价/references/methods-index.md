# 方法审查索引

这些卡片是问题导向的审查提示，不是唯一标准答案。每项含适用前提/数据、误用、求解、验证与来源。方法库不能替代上传题意或运行时联网。来源待打开状态见 sources-methods.json；通用文档只支持相应范围，遇具体定理须进一步查原始文献。

- [规划优化](methods/01-optimization.md)：线性规划 LP；混合整数规划 MILP；非线性/凸规划；动态规划；随机规划；鲁棒优化
- [图论与调度](methods/02-graphs.md)：Dijkstra/Bellman-Ford；最小生成树 Kruskal/Prim；最大流/最小费用流；二分匹配/匈牙利算法；车辆路径/作业调度
- [回归与统计](methods/03-statistics.md)：OLS/WLS/GLS；Logistic/Poisson GLM；Ridge/Lasso；假设检验/ANOVA；成分数据 ALR/CLR/ILR
- [时序预测](methods/04-forecast.md)：ARIMA/SARIMA；ETS/指数平滑；VAR；GM(1,1)；LSTM/神经时序
- [综合评价](methods/05-evaluation.md)：AHP；TOPSIS；熵权；CRITIC；DEA CCR/BCC；灰色关联分析
- [聚类分类与降维](methods/06-machine-learning.md)：K-means；层次聚类/DBSCAN；PCA；SVM/SVR；随机森林/梯度提升
- [机理方程与数值计算](methods/07-mechanistic.md)：ODE/传染病SIR/种群模型；PDE/有限差分；插值/样条/数值积分；参数估计/反问题
- [随机过程与仿真](methods/08-simulation.md)：Monte Carlo；离散事件/排队；Markov链/MDP；Bootstrap/置换
- [启发式与多目标](methods/09-heuristics.md)：GA遗传算法；PSO粒子群；SA模拟退火；NSGA-II；差分进化 DE
- [敏感性与稳健性](methods/10-sensitivity.md)：局部敏感性/有限差分；Sobol全局敏感性；Morris筛选；情景/消融/稳健性比较

## 证据纠偏

- OLS不要求因变量自身正态；正态误差条件与特定推断有关，模型目标和误差结构仍需核查。
- 成分数据不是必须采用CLR；根据零值、目标和解释需求比较ALR、ILR、组成回归或其他有依据的约束模型。
- AHP判断矩阵为正互反矩阵，通常不是对称矩阵；某些官方库文字可能写错，应回看公式并交叉查证。CR通过不证明专家偏好或现实结论正确。
- 熵权衡量给定规范化和样本下的差异，不自动等于业务重要性。相关、聚类或特征重要度不自动给出因果。
- 启发式有限运行只能报告找到的解和实验证据；全局最优需要适用的证明或最优性证书。

共 49 个重点方法条目。分组卡按任务读取，不应每次全部加载。