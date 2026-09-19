# 参考库烟测报告

> 目标：确认每个算法的 Python 与 MATLAB 模板都能真正跑出结果，而不是只贴了代码。
> 最近更新：2026-09-10（扩容到 90 个算法后重跑）。

## 结果

| 语言 | 运行方式 | 通过 | 失败 |
|---|---|---|---|
| Python | `python scripts/build_library.py --smoke`（工作区 `工具/code_env`，Python 3.12.14） | 90 | 0 |
| MATLAB | `matlab -batch "matlab_smoke"`（单会话逐个执行，`scripts/matlab_smoke.m`） | 90 | 0 |

每个模板运行时都会在自身目录写出 `out/` 结果表与（涉及的）300dpi PNG 与矢量 PDF 图。

## 覆盖范围

12 大类 90 个算法：优化与启发式 9、评价决策 9、预测时序 12、聚类分类 11、图与网络 6、
机理与微分方程 10、随机模拟 8、统计检验 8、降维与特征 5、数据预处理 6、空间与地理 3、博弈与决策 3。

## 过程中修正的问题（保留供参考）

| 模板 | 问题 | 处理 |
|---|---|---|
| `dynamic_programming_knapsack`(m) | 动态规划数组按 0 基索引，MATLAB 报下标越界 | 容量维整体 +1 偏移 |
| `nsga2`(m) | 非支配排序用空胞元自增下标，越界 | 重写排序与拥挤度函数 |
| `arima_forecast`(m) | `forecast` 与工具箱版本/签名不兼容 | 改为差分 + 最小二乘 AR 递推，去工具箱依赖 |
| `gradient_boosting_regression`(m) | `MaxNumSplits` 与 `Tree` 模板冲突 | 去掉该参数 |
| `random_forest_regression`(m) | 未开启 OOB 变量重要性 | 增加 `OOBPredictorImportance','on'` |
| `mlp_regression`(m) | `tansig` 属深度学习工具箱，本机未装 | 改为手写 tanh 的 ELM 实现 |
| `mlp_classification`(m) | `ind2vec` 同属深度学习工具箱 | 改为手写 one-hot 编码 |
| `naive_bayes`(m) | `CellOfMu` 字段不存在 | 改用 `DistributionParameters` |
| `dijkstra`(m) | `shortestpath` 不接受向量目标 | 改用 `shortestpathtree` + 逐点回溯 |
| `max_flow`(m) | `maxflow` 输出语义随版本变化 | 改为纯数组 Edmonds-Karp 实现 |
| `markov_chain`(m) | 表变量名与矩阵列数不匹配 | 显式构造各状态列 |
| `chi_square_test`(m) | `chi2gof`/`crosstab` 入参不匹配 | 手写卡方统计量与 p 值 |
| `nar_mlp_forecast`(m) | 矩阵维度写法歧义 | 改为显式转置的 `W'*feat + b'` |
| `laplace_equation_2d`(m) | 旧版本无 `inferno` 配色 | 改用 `parula` |
| `shapley_value`(m) | 循环变量 `size` 覆盖内置函数 | 改名为 `subsetSize` |
| `nash_equilibrium`(m) | 表格行列数不一致 | 按 4 个策略组合构造表 |
| `shapley_value`(py) | 演示数据用元组键，JSON 落盘崩溃 | `mmlib.demo` 增加键安全转换 |

以上 17 项都是烟测跑出来的真实缺陷，不是代码风格问题。

## 复现方式

```text
# Python
& "<你的工作区>\工具\code_env\Scripts\python.exe" build_library.py --smoke

# MATLAB（在 scripts 目录下执行）
matlab -batch "matlab_smoke"
```
