# 真实获奖代码语料（calibration corpus）

> 来源：数据集 5 份"【代码无论文】…说明.md"指向的作者公开 GitHub 仓库（2026-09-06 抓取，仅作评价参照/教学，勿商业分发）。
> 用途：横向参照——评某题代码时，可对比同/近题获奖代码的落地方式与质量档位；也可作为"真实获奖代码长什么样"的校准样本。

| 目录 | 年份-题号 | 作者 | 奖项 | 仓库 | 代码形态 |
|---|---|---|---|---|---|
| 2021C-zz-wolf | 2021-C | zz-wolf | 全国二等奖 | github.com/zz-wolf/CUMCM2021-C | 第1~4问.py（Python） |
| 2022B-YancyLan | 2022-B | YancyLan | 全国二等奖 | github.com/YancyLan/-2022CUMCM-B-Mathematics-Modelling | CUMCM.m / iteration.m（MATLAB） |
| 2023C-xtan2002 | 2023-C | xtan2002 | 全国二等奖 | github.com/xtan2002/CUMCM-2023 | 10 个 .ipynb（Python）＋自整理数据 |
| 2024B-BoNingGu | 2024-B | BoNingGu | 全国二等奖 | github.com/BoNing-Gu/CUMCM24-ProblemB-SimulationApproach | Q2/Q3-GA/Q3-PSO/Q4 拓展 .py＋.ipynb（仿真/回归） |
| 2024B-cloudcollection | 2024-B | cloudcollection | 广东赛区二等奖 | github.com/cloudcollection/2024CUMCM_B | .py＋.m 混合（DP/遗传/退火等） |

## 使用注意
- 各仓库代码随作者原样保留；本安装包为**代码/文档版**（已裁剪数据与结果类大文件，语料目录约 2.6MB），需要原始数据时按上表仓库地址自行获取。
- 评价时优先读代码文件（.py/.m/.ipynb）；数据与结果文件用于理解输入输出口径。
- 仓库作者自述"代码较乱/能跑就行"等评价只代表其自评，不代表奖项档次。
- 2022B-YancyLan 的 CUMCM.m 注释声明了 Q1A1.m 等若干子程序，但仓库 main 分支仅含 CUMCM.m/iteration.m——以实际文件为准，必要时注明"文档声明与仓库内容不一致"（本身可作可复现性观察点）。
