# 工作记录与命令约定 v1

所有路径相对 JSON 文件所在目录解析，也接受绝对路径；安装包和可共享示例只使用相对路径。把用户直接粘贴的方案保存成 UTF-8 文本后引用。脚本只作结构与算术检查，数学判断及网页真实性必须由运行 Skill 的 Codex 完成。

## 顶层字段

- `status`: `missing_inputs` / `draft` / `provisional` / `complete`。实际状态由工具重新计算；错误声称 complete 会被拒绝。
- `inputs`: `problem`、`plan` 为文件路径；`output_root` 是使用者指定的报告保存根路径；`attachments` 为路径列表；`expected_attachments` 为从赛题核实的全部附件原始文件名列表；`attachments_declared:true` 表示已经核对附件清单。无附件时两个列表都为空。工具不可能仅凭文件存在判断其内容完整，Codex 必须先阅读确认。重命名附件需恢复原始文件名。
- `rubric_version`、`requirements`: 固定量表版本与赛题检查项文本；首次评分前保存；修订沿用同一版本。
- `methods`: 对象列表。每项 `id` 唯一，`kind` 为 `model` / `algorithm` / `variant`，`name` 为名称，`claims` 为非空主张 id 列表。每个具体变体单列；基础方法与新增步骤分别查证。
- `evidence`: 每一 `(method_id, claim_id)` 至少一张卡。必填 `claim`（具体主张）、`applicability`（前提与本题匹配判断）和 `status`。状态为 `supported` / `partial` / `conflict` / `unverified`。前三者还需 `url`、`locator`（页/节/公式/代码行及支持内容）、`accessed`（YYYY-MM-DD）；未核验需 `reason`。`partial` 和 `conflict` 表示查证已实施，不能据此说模型适用。
- `issues`: 每项含 `id`、`severity`（critical/high/medium/low）、`location`、`problem`、`cause`、`impact`、`fix`、`acceptance`。问题关联多个步骤时在 impact 说明，仅在一个主维度扣分。
- `scores`: 有评分时必须包含全部十维，`dimension` 依次使用 fit/coverage/data/assumptions/rigor/algorithm/feasibility/validation/interpretability/necessity。每项含 `ratio`（0..1 或 null）、`rationale`、`location`、`requirement`、`improvement`、`issue_ids`（实际扣分的问题 id）。null 只表示外部证据不足等无法评价的事项，方案遗漏应正常评价并说明。禁止同一问题在两个维度扣分。
- 推荐将每个维度写为 `{ "dimension":"fit", "items":[...] }`；各子项含唯一 `id`、正数 `weight`，以及上述 ratio/rationale/location/requirement/improvement/issue_ids。子项权重合计必须等于该维固定权重，且不能同时填写整维 ratio。部分子项未知时只排除该子项权重，保留已知不利判断；不得因一个未知子项排除整个维度。冻结量表时同时冻结子项与权重。
- 报告正文采用 Markdown 字符串：`summary`、`data_profile`、`question_reviews`、`method_reviews`、`chain_review`、`optimized_outline`、`validation_plan`、`unresolved`。无内容时明确“无”并解释，不空填。

## 计算与命令

`python scripts/review.py intake record.json` 检查材料；缺件时不得出分。

`python scripts/review.py validate record.json` 检查结构、证据卡覆盖、重复扣分及完整性声明。

`python scripts/review.py score record.json` 输出状态、得分、可评权重及证据覆盖率。

`python scripts/review.py report record.json --output-root "用户指定路径"` 在该路径下创建 `数学模型评价` 文件夹并生成中文报告。也可省略参数并使用记录中的 `inputs.output_root`。同名报告已存在时生成带时间戳的新文件，避免覆盖；缺件时只生成缺件清单，记录错误时不出分。

`python scripts/review.py report-check record.json` 检查正文、量表版本、逐问要求、模型清单和评分是否齐全。正文缺失时 report 也会拒绝出分并给出待补内容。完整不等于优质，仍需 Codex 检查具体建议是否可执行。

`python scripts/review.py environment` 检查 Python 及可选提取依赖。工具无第三方必需依赖，不会执行用户代码，也不会调用模型 API。

百分制分数 = 100 × Σ(可评子项权重 × ratio) / Σ可评子项权重。全未知时 score=null。coverage_percent 为已评权重 / 100，evidence_coverage 为有查证状态的主张数 / 声明的全部主张数；它不表示网页真实性或正确性。证据不全或权重未评全时为 provisional。不存在方法/主张时不得为 complete。CLI 的 intake/validate/report-check 失败以及 score 的 draft/missing_inputs 返回 1，JSON 读取错误返回 2；report 输出仍需审查后交付。

## 交付前的人工作业检查

文件存在检查不能替代阅读完整性、扫描质量、附件字段核对。每个问题、每个模型和算法、每个关键变体都必须出现在记录中；工具无法识别被漏报的模型。引用必须真实打开并与主张相符。报告逐模型评价需要前提、数据、目标、约束、算法与输入输出检查，不能只重复证据表。建议需包含实施步骤、新增工作量、适用条件与验收方法。不得依据格式、方法数量、尚不存在的实验结果或奖次加减分。
