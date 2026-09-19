# 随机过程与仿真：方案审查卡

核查来源状态见 [登记表](../sources-methods.json)。以下“误用”是风险检查点，发现相关证据后才能认定缺陷，不能仅凭使用了某方法扣分。

## Monte Carlo
- 前提与数据：输入概率分布及相关结构有依据。
- 常见误用：单次随机结果当期望；忽略抽样误差。
- 求解设计：明确采样器、样本数和种子。
- 验证计划：误差条、样本量加倍、独立重复。
- 来源线索：[SALib Basics](https://salib.readthedocs.io/en/latest/user_guide/basics.html)；定位：Sampling / Run model / Analyze；具体主张运行时复核。

## 离散事件/排队
- 前提与数据：到达服务分布、资源纪律和暖机明确。
- 常见误用：非泊松数据强套M/M/1；稳态条件不检查。
- 求解设计：事件调度仿真或适合条件的解析式。
- 验证计划：暖机、独立重复、排队守恒与极限场景。
- 来源线索：[SimPy documentation](https://simpy.readthedocs.io/en/latest/)；定位：Discrete event simulation；具体主张运行时复核。

## Markov链/MDP
- 前提与数据：状态足够表达依赖，转移概率有数据基础。
- 常见误用：无依据假设无记忆或平稳。
- 求解设计：转移矩阵/动态规划；奖励与折扣说明。
- 验证计划：行和、吸收态、状态划分与策略验证。
- 来源线索：[Sutton Barto Reinforcement Learning](http://incompleteideas.net/book/the-book-2nd.html)；定位：Dynamic programming and Markov decision processes；具体主张运行时复核。

## Bootstrap/置换
- 前提与数据：重抽样单位符合原抽样机制。
- 常见误用：时序独立重抽样破坏依赖；小样本万能化。
- 求解设计：成对、分层或块重抽样按设计选。
- 验证计划：区间稳定性与样本代表性局限。
- 来源线索：[SciPy bootstrap](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html)；定位：Parameters paired / method；具体主张运行时复核。
