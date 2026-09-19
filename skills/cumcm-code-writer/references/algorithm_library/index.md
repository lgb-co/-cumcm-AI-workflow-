# 算法参考库索引

> 模板总数：90 个；每个模板含 Python 与 MATLAB 最小可运行实现、演示数据与 `meta.yaml`。
> 生成时间：2026-09-10 18:13；明细见 `manifest.csv`。

用法：命中算法 → 读该目录的 `meta.yaml`（成立条件与常见坑）与 `python/main.py`（接口与数据约定）→ 按用户题目重写，而不是整段复制。

## 01_优化与启发式（9）

| 算法 | 适用题型 | Python 依赖 | MATLAB 工具箱 | 状态 |
|---|---|---|---|---|
| `ant_colony_tsp` 蚁群算法 | 路径规划/TSP | numpy | base | py=pass/ml=skipped |
| `dynamic_programming_knapsack` 动态规划背包 | 多阶段决策/装载/资源分配 | numpy | - | py=pass/ml=skipped |
| `genetic_algorithm` 遗传算法 | 组合优化/复杂约束寻优 | numpy | - | py=pass/ml=skipped |
| `integer_programming` 整数规划 | 选址/排班/0-1决策 | numpy;scipy | optim | py=pass/ml=skipped |
| `linear_programming` 线性规划 | 资源分配/生产计划/运输问题 | numpy;scipy | optim | py=pass/ml=skipped |
| `nonlinear_programming` 非线性规划 | 连续变量非线性优化 | numpy;scipy | optim | py=pass/ml=skipped |
| `nsga2` NSGA-II 多目标优化 | 多目标权衡/Pareto前沿 | numpy | - | py=pass/ml=skipped |
| `particle_swarm` 粒子群优化 | 连续参数寻优 | numpy | - | py=pass/ml=skipped |
| `simulated_annealing` 模拟退火 | 组合优化/路径规划/布局 | numpy | base | py=pass/ml=skipped |

## 02_评价决策（9）

| 算法 | 适用题型 | Python 依赖 | MATLAB 工具箱 | 状态 |
|---|---|---|---|---|
| `ahp` 层次分析法 | 指标权重/方案排序 | numpy | - | py=pass/ml=skipped |
| `coefficient_of_variation` 变异系数法赋权 | 客观赋权 | numpy | - | py=pass/ml=skipped |
| `critic_weight` CRITIC 赋权法 | 指标权重与客观评价 | numpy | - | py=pass/ml=skipped |
| `dea` DEA 数据包络分析 | 多投入多产出效率评价 | numpy;scipy | optim | py=pass/ml=skipped |
| `entropy_weight` 熵权法 | 客观赋权 | numpy | - | py=pass/ml=skipped |
| `fuzzy_comprehensive` 模糊综合评价 | 定性指标量化评价 | numpy | - | py=pass/ml=skipped |
| `grey_relational` 灰色关联分析 | 小样本影响因素排序 | numpy | - | py=pass/ml=skipped |
| `rsr` 秩和比综合评价 | 综合评价与分档 | numpy;pandas | - | py=pass/ml=skipped |
| `topsis` TOPSIS 逼近理想解 | 多方案排序 | numpy | - | py=pass/ml=skipped |

## 03_预测时序（12）

| 算法 | 适用题型 | Python 依赖 | MATLAB 工具箱 | 状态 |
|---|---|---|---|---|
| `arima_forecast` ARIMA 时序预测 | 平稳或差分平稳序列预测 | numpy;pandas;statsmodels | econ | py=pass/ml=skipped |
| `bass_diffusion` Bass 扩散模型 | 新产品与技术扩散预测 | numpy;scipy | econ;optim | py=pass/ml=skipped |
| `exponential_smoothing` 指数平滑预测 | 短期趋势预测 | numpy | - | py=pass/ml=skipped |
| `gm11` 灰色预测GM(1 | 1) | numpy | - | py=pass/ml=skipped |
| `gradient_boosting_regression` 梯度提升回归 | 高精度回归预测 | numpy;sklearn | stats | py=pass/ml=skipped |
| `linear_regression` 多元线性回归 | 影响因素建模与预测 | numpy | stats | py=pass/ml=skipped |
| `mlp_regression` BP神经网络回归 | 非线性回归预测 | numpy;sklearn | - | py=pass/ml=skipped |
| `nar_mlp_forecast` NAR 非线性自回归神经网络预测 | 非线性时序预测 | numpy;sklearn | econ | py=pass/ml=skipped |
| `polynomial_fit` 多项式拟合 | 趋势拟合与插值建模 | numpy | base | py=pass/ml=skipped |
| `random_forest_regression` 随机森林回归 | 非线性预测与特征重要性 | numpy;sklearn | stats | py=pass/ml=skipped |
| `ridge_regression` 岭回归 | 共线性下的回归 | numpy;sklearn | stats | py=pass/ml=skipped |
| `svr_regression` 支持向量回归 | 小样本非线性回归 | numpy;sklearn | - | py=pass/ml=skipped |

## 04_聚类分类（11）

| 算法 | 适用题型 | Python 依赖 | MATLAB 工具箱 | 状态 |
|---|---|---|---|---|
| `adaboost_classification` AdaBoost 集成分类 | 弱学习器集成分类 | numpy;sklearn | - | py=pass/ml=skipped |
| `dbscan` DBSCAN密度聚类 | 任意形状簇与异常点识别 | numpy;sklearn | base | py=pass/ml=skipped |
| `decision_tree` 决策树分类 | 可解释规则提取 | numpy;sklearn | stats | py=pass/ml=skipped |
| `gmm` 高斯混合模型软聚类 | 概率归属与软聚类 | numpy;sklearn | base;stats | py=pass/ml=skipped |
| `hierarchical_clustering` 层次聚类 | 样本与指标分层归并 | numpy;scipy;sklearn | base | py=pass/ml=skipped |
| `kmeans` K-means聚类 | 样本分群/区域划分 | numpy;sklearn | base | py=pass/ml=skipped |
| `knn_classification` KNN分类 | 小样本分类 | numpy;sklearn | stats | py=pass/ml=skipped |
| `logistic_regression` Logistic回归 | 二分类概率建模 | numpy;sklearn | stats | py=pass/ml=skipped |
| `mlp_classification` BP 神经网络分类 | 非线性分类 | numpy;sklearn | - | py=pass/ml=skipped |
| `naive_bayes` 朴素贝叶斯分类 | 文本与高维分类 | numpy;sklearn | stats | py=pass/ml=skipped |
| `svm_classification` 支持向量机分类 | 中小样本分类 | numpy;sklearn | stats | py=pass/ml=skipped |

## 05_图与网络（6）

| 算法 | 适用题型 | Python 依赖 | MATLAB 工具箱 | 状态 |
|---|---|---|---|---|
| `critical_path_cpm` 关键路径CPM | 项目工期与关键工序 | - | base | py=pass/ml=skipped |
| `dijkstra` Dijkstra最短路 | 非负权网络最短路径 | numpy | base | py=pass/ml=skipped |
| `floyd` Floyd全源最短路 | 任意两点最短路径 | numpy | - | py=pass/ml=skipped |
| `max_flow` 最大流 | 运输能力与匹配问题 | numpy | - | py=pass/ml=skipped |
| `minimum_spanning_tree` 最小生成树 | 网络铺设与聚类连接 | - | base | py=pass/ml=skipped |
| `tsp_two_opt` TSP两阶段启发式 | 巡回路径规划 | numpy | base | py=pass/ml=skipped |

## 06_机理与微分方程（10）

| 算法 | 适用题型 | Python 依赖 | MATLAB 工具箱 | 状态 |
|---|---|---|---|---|
| `heat_equation_1d` 一维热传导方程 | 温度扩散与时空演化 | numpy | - | py=pass/ml=skipped |
| `laplace_equation_2d` 二维拉普拉斯方程 SOR | 稳态温度与势场分布 | numpy | base | py=pass/ml=skipped |
| `logistic_population` Logistic人口增长模型 | 有限资源下的增长过程 | numpy;scipy | econ;optim | py=pass/ml=skipped |
| `lorenz_system` Lorenz混沌系统 | 非线性动力学与初值敏感性 | numpy;scipy | base | py=pass/ml=skipped |
| `lotka_volterra` Lotka-Volterra竞争捕食模型 | 种群竞争与捕食关系 | numpy;scipy | base | py=pass/ml=skipped |
| `second_order_ode` 二阶微分方程阻尼振动 | 振动与阻尼系统 | numpy;scipy | base | py=pass/ml=skipped |
| `seir_model` SEIR 传染病模型 | 潜伏期明显的传播建模 | numpy;scipy | base | py=pass/ml=skipped |
| `sir_model` SIR传染病模型 | 疫情传播与干预模拟 | numpy;scipy | base | py=pass/ml=skipped |
| `system_dynamics` 系统动力学存量流量模型 | 政策与系统演化仿真 | numpy | - | py=pass/ml=skipped |
| `wave_equation_1d` 一维波动方程有限差分 | 振动与波传播仿真 | numpy | - | py=pass/ml=skipped |

## 07_随机模拟（8）

| 算法 | 适用题型 | Python 依赖 | MATLAB 工具箱 | 状态 |
|---|---|---|---|---|
| `bootstrap_resampling` Bootstrap重采样 | 置信区间与稳健性评估 | numpy | base | py=pass/ml=skipped |
| `cellular_automata` 元胞自动机 | 传播扩散与演化仿真 | numpy | base | py=pass/ml=skipped |
| `markov_chain` 马尔可夫链预测 | 状态转移与份额预测 | numpy;pandas | - | py=pass/ml=skipped |
| `mcmc_metropolis` MCMC Metropolis抽样 | 后验抽样与参数估计 | numpy | base | py=pass/ml=skipped |
| `monte_carlo_integration` 蒙特卡洛积分 | 概率估算与复杂积分 | numpy | - | py=pass/ml=skipped |
| `queue_simulation` 蒙特卡洛排队仿真 | 服务系统等待时间评估 | numpy | base | py=pass/ml=skipped |
| `queueing_mm1` M/M/1排队论解析 | 服务能力与容量评估 | numpy | - | py=pass/ml=skipped |
| `queueing_mmc` M/M/c 多服务台排队 | 服务容量配置 | numpy | - | py=pass/ml=skipped |

## 08_统计检验（8）

| 算法 | 适用题型 | Python 依赖 | MATLAB 工具箱 | 状态 |
|---|---|---|---|---|
| `anova_oneway` 单因素方差分析 | 多组均值差异检验 | numpy;scipy | stats | py=pass/ml=skipped |
| `bayesian_inference` 贝叶斯参数估计 | 小样本参数估计与区间 | numpy;scipy | - | py=pass/ml=skipped |
| `canonical_correlation` 典型相关分析 | 两组变量整体关联 | numpy;sklearn | stats | py=pass/ml=skipped |
| `chi_square_test` 卡方检验 | 分类变量关联与拟合优度 | numpy;scipy | - | py=pass/ml=skipped |
| `correlation_analysis` 相关分析 | 变量关联强度与显著性 | numpy;pandas;scipy | base | py=pass/ml=skipped |
| `mann_kendall_trend` Mann-Kendall趋势检验 | 序列趋势显著性 | numpy;scipy | - | py=pass/ml=skipped |
| `regression_diagnostics` 回归诊断 | 模型假设检验与异常点识别 | numpy;scipy;statsmodels | stats | py=pass/ml=skipped |
| `robust_regression` Huber 稳健回归 | 含离群点的回归建模 | numpy;sklearn;statsmodels | base;stats | py=pass/ml=skipped |

## 09_降维与特征（5）

| 算法 | 适用题型 | Python 依赖 | MATLAB 工具箱 | 状态 |
|---|---|---|---|---|
| `factor_analysis` 因子分析 | 潜变量结构识别 | numpy;scipy;sklearn | stats | py=pass/ml=skipped |
| `lda` 线性判别分析 | 有监督降维与分类 | numpy;sklearn | base;stats | py=pass/ml=skipped |
| `pca` 主成分分析 | 降维与综合评价 | numpy;sklearn | stats | py=pass/ml=skipped |
| `rfe_feature_selection` 递归特征消除 | 特征筛选与变量精简 | numpy;sklearn | stats | py=pass/ml=skipped |
| `tsne` t-SNE降维可视化 | 高维数据二维可视化 | numpy;sklearn | base;stats | py=pass/ml=skipped |

## 10_数据预处理（6）

| 算法 | 适用题型 | Python 依赖 | MATLAB 工具箱 | 状态 |
|---|---|---|---|---|
| `cubic_spline_interpolation` 三次样条插值 | 平滑曲线重建 | numpy;scipy | base | py=pass/ml=skipped |
| `iqr_outlier` IQR四分位距异常检测 | 单变量异常识别 | numpy | - | py=pass/ml=skipped |
| `lagrange_interpolation` 拉格朗日插值 | 离散点补全 | numpy | - | py=pass/ml=skipped |
| `minmax_standardization` 归一化与标准化 | 建模前数据处理 | numpy | - | py=pass/ml=skipped |
| `missing_imputation` 缺失值插补 | 数据完整性修复 | numpy;pandas | base | py=pass/ml=skipped |
| `zscore_outlier` Z-Score异常检测 | 近似正态数据异常识别 | numpy | - | py=pass/ml=skipped |

## 11_空间与地理（3）

| 算法 | 适用题型 | Python 依赖 | MATLAB 工具箱 | 状态 |
|---|---|---|---|---|
| `geodetector_q` 地理探测器 q 统计量 | 驱动因子解释力分析 | numpy | - | py=pass/ml=skipped |
| `kriging` 普通克里金插值 | 空间插值与制图 | numpy | base | py=pass/ml=skipped |
| `moran_i` Moran's I 空间自相关 | 区域聚集与空间分异 | numpy;scipy | base | py=pass/ml=skipped |

## 12_博弈与决策（3）

| 算法 | 适用题型 | Python 依赖 | MATLAB 工具箱 | 状态 |
|---|---|---|---|---|
| `evolutionary_game` 演化博弈复制动态 | 策略演化与稳定策略 | numpy;scipy | base | py=pass/ml=skipped |
| `nash_equilibrium` 纳什均衡 | 策略博弈与均衡分析 | numpy | - | py=pass/ml=skipped |
| `shapley_value` Shapley 值 | 合作博弈收益与成本分摊 | numpy | - | py=pass/ml=skipped |
