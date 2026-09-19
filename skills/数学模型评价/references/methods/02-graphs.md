# 图论与调度：方案审查卡

核查来源状态见 [登记表](../sources-methods.json)。以下“误用”是风险检查点，发现相关证据后才能认定缺陷，不能仅凭使用了某方法扣分。

## Dijkstra/Bellman-Ford
- 前提与数据：节点、边、方向和权值单位明确。
- 常见误用：Dijkstra直接处理负边，忽略负环。
- 求解设计：非负权Dijkstra；有负边考虑Bellman-Ford。
- 验证计划：小图手算、不可达节点及负环检查。
- 来源线索：[NetworkX Algorithms](https://networkx.org/documentation/stable/reference/algorithms/index.html)；定位：Shortest Paths / Flow / Matching；具体主张运行时复核。

## 最小生成树 Kruskal/Prim
- 前提与数据：无向连通图，目标为连接全部节点最小总边权。
- 常见误用：当成任意两点最短路径或有向网络设计。
- 求解设计：Kruskal/Prim；不连通输出森林并解释。
- 验证计划：连通性、边数、替换边界性质。
- 来源线索：[NetworkX Algorithms](https://networkx.org/documentation/stable/reference/algorithms/index.html)；定位：Shortest Paths / Flow / Matching；具体主张运行时复核。

## 最大流/最小费用流
- 前提与数据：容量、供需和费用有物理含义。
- 常见误用：违反流守恒，漏掉容量或把费用当距离。
- 求解设计：增广路、网络单纯形等；整数条件须核实。
- 验证计划：守恒与容量残差，最大流最小割证书。
- 来源线索：[NetworkX Algorithms](https://networkx.org/documentation/stable/reference/algorithms/index.html)；定位：Shortest Paths / Flow / Matching；具体主张运行时复核。

## 二分匹配/匈牙利算法
- 前提与数据：两类对象及允许边；一对一目标明确。
- 常见误用：多容量任务硬塞一对一匹配。
- 求解设计：指派求解器或扩展为网络流/MILP。
- 验证计划：小例枚举、禁用边与未匹配惩罚。
- 来源线索：[NetworkX Algorithms](https://networkx.org/documentation/stable/reference/algorithms/index.html)；定位：Shortest Paths / Flow / Matching；具体主张运行时复核。

## 车辆路径/作业调度
- 前提与数据：资源、时间窗、优先关系与服务时间完整。
- 常见误用：距离最短等同总成本最小；漏返程或子回路。
- 求解设计：MILP/约束规划/启发式按规模选择。
- 验证计划：独立重算路线时间与资源冲突。
- 来源线索：[SciPy optimization](https://docs.scipy.org/doc/scipy/reference/optimize.html)；定位：Optimization / Linear programming / MILP；具体主张运行时复核。
