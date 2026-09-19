# CUMCM 数模全流程工作流

（ps：能不能来个好心人莫名其妙给我一个线上实习机会QAQ）

只针对国赛内容，建议日常使用其中的小skill，整个流程预计10h

面向全国大学生数学建模竞赛（CUMCM）的 Codex 技能包：把「建模 → 方案评审 → 代码实现 → 代码检测 → 结果驱动复盘 → 国赛论文成文」串成一条留痕流水线。各阶段由彼此独立的任务完成，通过密封清单（SHA-256）、结构化回执与门禁交接；总指挥 `cumcm-fullflow` 只负责编排、调用与校验，不代替专业技能产出内容。

> 本项目为工程化整理的非官方项目。评审得分、位次与修改建议均为非官方估计，不代表全国大学生数学建模竞赛组委会。

## 快速开始

### 方式一：下载安装包（推荐）

1. 下载最新安装包：[CUMCM全流程工作流-安装包-v1.1.0.zip](releases/CUMCM全流程工作流-安装包-v1.1.0.zip)
2. 解压后双击 `Install.cmd`（无需管理员权限）。
3. 在 Codex 新任务中说：

```text
用 $cumcm-fullflow 跑 2026A：赛题和附件在 <路径>
```

只建模、只评方案、只写代码、只检测代码或只写论文时，不需要总指挥，直接调用对应技能即可。

### 方式二：从源码安装

```powershell
git clone https://github.com/star1342354/cumcm-pipeline.git
cd -
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

`install.ps1` 会把 `skills/` 下六个技能与 `tools/` 安装到 Codex 技能目录；覆盖或卸载前会把旧文件备份到 `~/.codex/.cumcm-workflow-backups/<时间戳>/`，不会直接删除。

## 包含的六个技能

| 目录 | 角色 |
| --- | --- |
| [`数学模型建立`](skills/数学模型建立) | 建模：拆题、数学化、检索取数，产出建模方案与数据文档 |
| [`数学模型评价`](skills/数学模型评价) | 方案评审：逐问四遍复读 + 联网查证，产出诊断、修改方案与优化脉络 |
| [`cumcm-code-writer`](skills/cumcm-code-writer) | 代码编写：按定稿方案编写竞赛可读代码，三轮自测，产出附录与结果文档 |
| [`cumcm-code-reviewer`](skills/cumcm-code-reviewer) | 代码检测：干净副本复跑 + 独立复算，产出 P0/P1/P2 问题清单 |
| [`cumcm-paper-writer`](skills/cumcm-paper-writer) | 论文成文：起草/改写/校验（格式 + 风格 + 数字一致性 + 赛题逐条对照） |
| [`cumcm-fullflow`](skills/cumcm-fullflow) | 总指挥：阶段编排、独立任务调用、密封交接、门禁与回执校验；不产出专业内容 |

四个核心技能（`数学模型建立`、`数学模型评价`、`cumcm-code-writer`、`cumcm-code-reviewer`）保持 v1.0.2 基线逐文件不变；`cumcm-paper-writer` 与 `cumcm-fullflow` 独立存在，由总指挥编排调用。

## 仓库结构

```text
.
├─ README.md                  # 本说明
├─ CHANGELOG.md               # 版本变更记录
├─ LICENSE                    # MIT
├─ SHA256SUMS.txt             # 发布包校验和
├─ Install.cmd / install.ps1  # Windows 安装器（事务式、可回滚）
├─ 使用与安装.md              # 安装、CLI 与依赖说明
├─ BUILD_METADATA.json        # 构建元数据与技能哈希
├─ skills/                    # 六个技能源码（v1.1.0）
├─ tools/                     # cumcm-flow CLI、交接/校验脚本、DOCX 导出工具
└─ releases/                  # 历史安装包
   ├─ CUMCM全流程工作流-安装包-v1.0.1.zip
   ├─ CUMCM全流程工作流-安装包-v1.0.2.zip
   ├─ CUMCM全流程工作流-安装包-v1.1.0.zip
   └─ legacy/                # 早期单技能安装包（仅存档，不推荐新用户使用）
```

## 版本与校验

| 版本 | 日期 | 安装包 | SHA-256（前 16 位） |
| --- | --- | --- | --- |
| v1.1.0（最新） | 2026-09-19 | [下载](releases/CUMCM全流程工作流-安装包-v1.1.0.zip) | `1843FE894471B899` |
| v1.0.2 | 2026-09-19 | [下载](releases/CUMCM全流程工作流-安装包-v1.0.2.zip) | `65EAB5C19792166A` |
| v1.0.1 | 2026-09-17 | [下载](releases/CUMCM全流程工作流-安装包-v1.0.1.zip) | `D0417E3847ABB1A0` |

完整 SHA-256 见 [`SHA256SUMS.txt`](SHA256SUMS.txt)。PowerShell 校验示例：

```powershell
Get-Content .\SHA256SUMS.txt
Get-FileHash .\releases\CUMCM全流程工作流-安装包-v1.1.0.zip -Algorithm SHA256
```

> v1.0.0 及部分早期单技能包内含打包机绝对路径，未纳入本仓库；`releases/legacy/` 仅保留扫描后无本地路径的归档包。新用户请直接使用 v1.1.0。

## CLI 与门禁

`tools/` 提供统一命令行入口（不是新技能，只做工程操作）：

```powershell
tools\cumcm-flow.cmd doctor                 # 陌生机器环境体检
tools\cumcm-flow.cmd doctor --json
tools\cumcm-flow.cmd init <运行目录>        # 建立运行目录骨架
tools\cumcm-flow.cmd seal S1 --run-dir <运行目录>
tools\cumcm-flow.cmd verify S1 --run-dir <运行目录>
tools\cumcm-flow.cmd status <运行目录>
```

总指挥按阶段调用独立任务：建模 → 方案评审 → 代码实现 → 代码检测 → 结果驱动的模型复盘 → 论文起草/改写/校验 → 交付核验。每个阶段用密封清单（SHA-256）交接、写结构化回执，并在数据确认、模型定稿等门禁处停下等待确认。独立任务不可用时会停下或改派，不会由总指挥在当前线程代做。

## 环境要求

- Python 3.11+（写码、计算与 DOCX 导出的硬需求）
- 建议安装：`numpy`、`pandas`、`matplotlib`、`scipy`、`scikit-learn`
- DOCX 原生公式导出需要 `pypandoc`：运行 `tools\setup-md2docx.ps1`，或安装时加 `-SetupTools`
- 主平台为 Windows（`Install.cmd` / `install.ps1`），同时提供 PowerShell 与 Unix 启动脚本
- 可选联网能力：文献核验、数据抓取、mermaid/Kroki 出图

安装完成后建议先运行：

```powershell
tools\cumcm-flow.cmd doctor
```

`doctor` 默认把 Python、技能与工具缺失视为硬失败，把可选计算、文档与 OCR 依赖列为警告；`--strict` 会把可选依赖缺失也视为失败，`--network` 会额外检查 PyPI 连通性。

## 许可

[MIT](LICENSE)
