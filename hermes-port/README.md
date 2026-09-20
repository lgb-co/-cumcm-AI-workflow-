# cumcm-pipeline → Hermes 技能移植（hermes-port）

把 `cumcm-pipeline/skills/` 下的六个 **Codex 技能**改造成 **Hermes 技能**，装在
`C:\Users\33422\AppData\Local\hermes\skills\research\` 下，被 Hermes 原生加载（`skill_view` / `skills_list` 可见）。

原 Codex 技能**未被修改**，完整保留在 `cumcm-pipeline/skills/`。移植是可重跑的：

```bash
python hermes-port/port_to_hermes.py     # 生成/覆盖 Hermes 版（幂等）
python hermes-port/verify_port.py        # 校验：frontmatter/残留引用/运行期产物名
python "$HOME/AppData/Local/hermes/skills/research/cumcm-fullflow/scripts/tools/cumcm_flow.py" doctor
```

## 1. 名称与位置

| Codex 技能（原名） | Hermes 技能名 | 安装位置（相对 `~/AppData/Local/hermes/skills/`） |
|---|---|---|
| `数学模型建立` | `cumcm-model-build` | `research/cumcm-model-build/` |
| `数学模型评价` | `cumcm-model-review` | `research/cumcm-model-review/` |
| `cumcm-code-writer` | `cumcm-code-writer` | `research/cumcm-code-writer/` |
| `cumcm-code-reviewer` | `cumcm-code-reviewer` | `research/cumcm-code-reviewer/` |
| `cumcm-paper-writer` | `cumcm-paper-writer` | `research/cumcm-paper-writer/` |
| `cumcm-fullflow` | `cumcm-fullflow` | `research/cumcm-fullflow/` |

两个中文名技能被重命名：Hermes 的技能名要求 ASCII、小写、连字符，且 `/^\w[\w.-]*$/`（不接受中文）。
**注意**：`数学模型评价` 作为**报告文件夹与报告文件名**是运行期产物（`scripts/review.py` 里的
`OUTPUT_FOLDER` / `REPORT_FILENAME`），移植时原样保留，没有跟着改。

## 2. frontmatter 规范对照

Codex 侧只用了 `name` + `description` 两行（其中 `数学模型建立/SKILL.md` 的 `name` 是中文，
`数学模型评价/SKILL.md` 的 `name` 与目录名不一致），description 长达 300–600 字。Hermes 版：

| 字段 | Codex 原状 | Hermes 版 | 原因 |
|---|---|---|---|
| `name` | 中文名或与目录不一致 | ASCII 小写连字符，**与目录名一致** | Hermes 校验器要求 |
| `description` | 300–600 字长段 | **≤60 字单句，以「。」结尾** | 该字段逐轮注入系统提示的技能索引；超长会被截断到 ~57 字，写长等于白写 |
| `version` | 无 | `1.1.0+hermes.1` | semver + 构建元数据，标明这是移植版 |
| `author` | 无 | `star1342354, Hermes Agent` | 人类作者在前 |
| `license` | 无（包级 MIT） | `MIT` | 与上游一致 |
| `platforms` | 无 | 按脚本依赖逐项审计（见 §4） | 不谎称跨平台 |
| `metadata.hermes.tags` | 无 | 中文检索词（如 `[cumcm, 数学建模, 建模方案, 国赛]`） | 便于按主题发现 |
| `metadata.hermes.related_skills` | 无 | 指向兄弟技能（全部已存在） | 管线内的互相跳转 |

每个 SKILL.md 的 frontmatter 之后插入一段 **移植说明**：写明原技能名、上游仓库与版本、
移植日期、改动范围、`$SKILLS` 约定，以及原版在本机的保留路径。正文业务逻辑一字未改。

`$SKILLS` 是移植说明里定义的约定变量，本机 =
`C:\Users\33422\AppData\Local\hermes\skills\research`，用于改写原先写死的
`~/.codex/skills/...` 式兄弟技能路径。

## 3. 目录与引用改动

- **根级散件归位**（Hermes 的可链接目录只有 `references/ templates/ scripts/ assets/`）：
  - `数学模型评价/{run.ps1, setup-dependencies.ps1, requirements-extraction.txt}` → `scripts/`
  - `数学模型评价/manifest.json` → `references/_上游原包校验单_manifest.json`
  - `cumcm-code-writer/{README.md, 安装说明.md}` → `references/_上游README.md`、`references/_上游安装说明_Codex版.md`
- **Codex 专有件删除**：`数学模型评价/agents/openai.yaml`（Codex 界面元数据，Hermes 无对应物）、
  `cumcm-code-writer/VERSION`（已折叠进 frontmatter）、`cumcm-code-writer/scripts/install_skill.ps1`
  （装到 `~/.codex/skills` 的安装器；Hermes 有自己的技能管理，同时删掉了 SKILL.md 里引用它的表格行）。
  带 `_上游` 前缀的归档件**原样保留**（含哈希），便于对照。
- **兄弟技能引用**：约 50 处，覆盖 18 个文件。技能名回指（如「转 `代码编写评价`」）改为
  `cumcm-code-reviewer`；跨技能数据路径改为 `$SKILLS/<技能名>/...`；文档标题里的
  「代码编写评价 Rubric」等**保持原样**（它们是文档名，不是技能引用）。
- **宿主指称**：把「由运行 Skill 的 Codex 完成」「由宿主 Codex 搜索工具提供」等行文改为 Hermes
  （`review-schema.md` ×3、`review.py` ×2、`run.ps1` ×1、总指挥 CLI 的 docstring/注释）。
- **`cumcm-fullflow` 内置总指挥 CLI**：原技能只写「安装包附带 `工具/cumcm-flow`」，而 CLI 在家目录的
  `tools/`，Hermes 技能包拿不到 —— 现把 `tools/` 整份复制进 `skills/tools/`（即
  `cumcm-fullflow/scripts/tools/`），并给 CLI 打五个补丁：
  1. `_skill_candidates()` 增加 Hermes 技能库候选（`_hermes_skills_root()` + `<分类>/<技能名>`），
     带重命名别名映射（`数学模型建立`→`cumcm-model-build`、`数学模型评价`→`cumcm-model-review`）；
  2. `_check_metadata()` 的哈希不一致从 `fail` 降为 `warn`（移植必然改写 SKILL.md，哈希不可能与上游一致）；
  3. `host` 体检项改述为「由 Hermes 宿主提供（delegate_task 子代理）」；
  4. `_check_runtime_env()` / 新增 `_resolve_env_dir()`：运行环境按 `CUMCM_CODE_ENV` → `环境配置.json` →
     技能库 `工具/` 的顺序定位，不再只认 `_here()/code_env`（见 §7）；
  5. `_check_environment_config()` 增加 Hermes 技能库候选，且经 `_code_writer_config()` **按技能查找结果**
     定位，不写死分类目录名。
  原 `CODEX_HOME` 候选**保留**为兼容分支（本机若也装了 Codex 版仍能找到）。

## 4. platforms 审计（不猜，按证据）

| 技能 | platforms | 依据 |
|---|---|---|
| `cumcm-model-build` | `[windows]` | DOCX 导出链依赖本机 Word/PowerShell；references 用 Windows 路径 |
| `cumcm-model-review` | `[windows]` | 入口是 `run.ps1` / `setup-dependencies.ps1` |
| `cumcm-code-writer` | `[linux, macos, windows]` | 核心是 Python；已移除 `install_skill.ps1` |
| `cumcm-code-reviewer` | `[linux, macos, windows]` | 纯 Python + Markdown |
| `cumcm-paper-writer` | `[linux, macos, windows]` | 纯 Python + Markdown |
| `cumcm-fullflow` | `[linux, macos, windows]` | CLI 提供 `.cmd`/`.ps1`/`.sh` 三种启动器 |

## 5. 有意保留的 Codex 痕迹（不算移植遗漏）

- `references/_上游*`：上游 README 与安装说明，讲的就是 Codex 安装方式，作为历史归档保留。
- `references/风格来源.md`：上游在盘点各 Agent（Codex / OpenCode 等）对 `SKILL.md` 的支持，是行文举例。
- 历史机器路径示例：`D:\综合处理\codex\演示\...`、`D:\CodexRuntime\venv`（CLI 的 `legacy-paths` 体检项还会专门提示）。
- 运行时缓存目录 `.cache\codex-runtimes`：改名会让本机已下载的运行时失效，故保留。
- HTTP UA 字符串 `CodexResearch/1.0`。
- 总指挥 CLI 的 `CODEX_HOME` 兼容候选分支。

## 6. 验证（2026-09-19 实测）

| 检查 | 结果 |
|---|---|
| `port_to_hermes.py` 规则断言（每条替换须按预期命中数命中） | 全部按预期命中 |
| `verify_port.py` ① frontmatter 合法性（对齐 Hermes 校验器 + 60 字上限 + name 与目录名一致 + 顶层目录规范） | fail=0 warn=0 |
| `verify_port.py` ② Codex 残留（区分「真依赖」与「有意保留」） | 无真依赖残留 |
| `verify_port.py` ②b 宿主错称 | 0 处 |
| `verify_port.py` ③ 兄弟技能旧名引用 | 0 处 |
| `verify_port.py` ④ 运行期产物名未被误改 | 通过 |
| `cumcm_flow.py doctor`（总指挥 CLI 在新布局下的自检） | 六个技能 + 四个工具全部 OK，`结果：通过` |
| Hermes `skill_view('cumcm-fullflow')` | 正文/tags/related_skills 解析正常，`readiness_status: available` |
| Hermes `skills_list(category='research')` | 六个技能均出现在索引中 |
| 链接文件解析 `skill_view('cumcm-model-review', 'references/review-schema.md')` | 正常返回 |
| `doctor` 的 `env:代码计算环境` / `config:工具环境配置` / `config:代码 Skill 环境配置（Hermes）` | 均已就位（接线前分别是 WARN / INFO / INFO） |
| `cumcm-code-writer/scripts/check_env.py` | `工作区虚拟环境：可用 <工作区>/工具/code_env/Scripts/python.exe` |
| 工作区 venv 直接导入 numpy/scipy/pandas/matplotlib/sklearn/statsmodels/seaborn/openpyxl/networkx/sympy/pulp/docx/yaml/imageio/tqdm/joblib | 16 个包全部可导入，无缺失 |

## 7. 环境接线（Hermes 布局的硬要求，必须单独做一步）

技能的 `scripts/_paths.py` 用 `WORKSPACE_DIR = SKILL_DIR.parent` 定位 `工具/code_env`——那是 **Codex 安装布局**
（技能与 `工具/` 同级）。在 Hermes 布局下技能装在 `<hermes>/skills/<分类>/`，所以
**照原样跑 `bootstrap_env.py` 会把虚拟环境建进技能目录里**，必须显式接线：

```powershell
# 1) 把环境建在工作区（示例路径）
python -m venv "<工作区>\工具\code_env"
"<工作区>\工具\code_env\Scripts\python.exe" -m pip install numpy scipy pandas matplotlib `
    scikit-learn statsmodels seaborn openpyxl networkx sympy pulp python-docx pyyaml imageio tqdm joblib

# 2) 接线：写 环境配置.json 到两处（CLI 读 <fullflow>/scripts/tools/，代码技能读 <code-writer>/）
python hermes-port/wire_code_env.py "<工作区>\工具\code_env"

# 3) 推荐：让所有脚本与 CLI 都指向它（用户级环境变量，新开的进程生效）
setx CUMCM_PYTHON   "<工作区>\工具\code_env\Scripts\python.exe"
setx CUMCM_CODE_ENV "<工作区>\工具\code_env"
```

`wire_code_env.py` 通过 `HERMES_SKILLS_ROOT`（默认 `%LOCALAPPDATA%\hermes\skills`）定位技能，写完**回读自校验**。
**每次重跑 `port_to_hermes.py` 之后都要再跑一次**：移植会重建技能目录，接线文件随之丢失。

另一个 Windows 侧的健壮性修正：技能目录可能被某个进程当成 cwd 而无法删除（`rmdir` 永远报 WinError 32，
重试无意义），因此 `sync_tree()` 改为**删不掉就原地覆盖**，移植不会再半途中断。

未接线的部分：`ocr_env`（仅赛题附件是扫描件/图片、需要 OCR 抽取时才需要）。

## 8. 已知差异 / 下一步

- Hermes 下「全新独立子代理」用 `delegate_task` 实现；正文里「独立任务适配器 / 独立子代理」的表述
  对 Hermes 同样成立，但**回执里的 `session_id` 语义**需要按 Hermes 实际返回的句柄填写。
- `cumcm-model-review` 的 `manifest.json`（现为 `references/_上游原包校验单_manifest.json`）里的
  SHA-256 仍对应 **Codex 原版 SKILL.md**，移植后不再匹配，仅作溯源用。
- `doctor` 的 `python:compute` / `python:document` 两条 WARN 是**探测宿主解释器**（Hermes 自带 venv）得出的，
  与工作区 `工具/code_env` 无关；技能执行脚本走的是工作区环境（`check_env.py` 已确认可用）。
- 需要把 Hermes 版打包给他人时，直接压缩
  `~/AppData/Local/hermes/skills/research/cumcm-*` 六个目录即可；但要一并说明安装目标路径与
  `$SKILLS` 约定（移植说明里已写明本机路径，跨机需替换）。