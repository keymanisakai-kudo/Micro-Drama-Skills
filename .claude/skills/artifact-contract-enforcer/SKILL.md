---
name: artifact-contract-enforcer
description: >
  对指定文件执行 artifact contract（产物契约）验证，检查其是否符合
  docs/artifact-contracts.md 中定义的格式规范和约束。
  支持验证所有9种 artifact 类型，输出详细的合规/违规报告。
category: governance
version: "1.0"
---

# artifact-contract-enforcer

## Purpose

作为"契约执行者"，对任意一个或一批短剧生产产物文件执行格式和内容验证：

1. 判断文件是否符合对应的 Artifact Contract（AC-001 到 AC-009）
2. 区分阻断性违规（BLOCKING）和警告性违规（WARNING）
3. 输出详细的违规清单，指明具体的字段路径和期望值 vs 实际值

本技能是**只读验证工具**，不修改任何文件。

---

## When to Use

- 任何生产技能执行完毕后的验收检查
- 手动修改某个 artifact 文件后，确认修改未引入格式错误
- `assemble-tasks` 的 4b 子步骤：验证 `seedance_project_tasks.json` 的 prompt 完整性
- CI/CD 集成时的自动化验证触发点

---

## When Not to Use

- 需要验证阶段状态转换是否合法——使用 `stage-gate-checker` 代替
- 需要验证媒体文件（PNG）是否存在——使用 `stage-gate-checker` 代替

---

## Inputs

| 输入 | 说明 |
|------|------|
| 目标文件路径（一个或多个） | 用户指定或由调用技能传入 |
| 契约类型（AC-001 到 AC-009，可自动推断） | 可由文件名/路径自动推断，或手动指定 |

---

## Outputs

验证报告（控制台输出，不写入文件）：

```
=== Artifact Contract 验证报告 ===
文件：{file_path}
契约：{AC-XXX} - {artifact_name}
验证时间：{timestamp}

BLOCKING 违规（{N}项）：
  [ERR] {field_path}：期望 {expected}，实际 {actual}
  [ERR] ...

WARNING 违规（{N}项）：
  [WARN] {field_path}：{warning_message}

通过项（{N}项）：
  [OK] {check_description}
  ...

=== 结论 ===
✅ PASS：文件符合 AC-XXX 契约规范
❌ FAIL：存在 {N} 项阻断性违规
```

---

## Constraints

本技能**只读**，不修改任何文件。

---

## Workflow

### Step 1：确定契约类型

根据文件路径自动推断或用户指定：

| 文件名/路径模式 | 对应契约 |
|---------------|---------|
| `metadata.json` | AC-001 |
| `script/full_script.md` | AC-002 |
| `characters/character_bible.md` | AC-003 |
| `scenes/scene_bible.md` | AC-004 |
| `props/prop_bible.md` | AC-005 |
| `episodes/EPxx/dialogue.md` | AC-006 |
| `episodes/EPxx/storyboard_config.json` | AC-007 |
| `video_index.json` | AC-008 |
| `seedance_project_tasks.json` | AC-009 |

### Step 2：执行契约验证

---

#### AC-001：metadata.json

**BLOCKING 检查**：
- `project_id` 存在且格式为 `DM-XXX`（三位数字）
- `project_name` 存在且非空
- `total_episodes` = 25
- `video_count` = 50
- `visual_style` 对象存在
- `visual_style.prompt_suffix` 存在且非空
- `created_date` 为合法日期格式（YYYY-MM-DD）

**WARNING 检查**：
- `status` 字段存在（历史兼容字段，应以 `video_index.json.status` 为准）

---

#### AC-002：full_script.md

**BLOCKING 检查**：
- 文件非空
- 包含"作品信息"章节
- 包含"世界观设定"章节
- 包含"故事大纲"章节
- 包含"各集概要"章节
- 各集概要包含 EP01–EP25 共 25 集（检查是否存在"第1集"到"第25集"的标题）

**WARNING 检查**：
- 故事大纲字数不少于 200 字
- 各集概要字数不少于 30 字/集

---

#### AC-003：character_bible.md

**BLOCKING 检查**：
- 文件非空
- 至少定义一个角色（含"角色"关键词的章节标题）
- 每个角色含 `AI绘图关键词（英文）` 字段
- `AI绘图关键词（英文）` 字段值为英文（非中文主体）

**WARNING 检查**：
- 每个角色含"背景故事"字段
- 每个角色含"角色弧光"字段

---

#### AC-004：scene_bible.md

**BLOCKING 检查**：
- 每个场景有 `**场景ID**` 字段且格式为 `scene_XX`
- 每个场景含 `AI绘图关键词（英文）` 字段且非空

**WARNING 检查**：
- 每个场景含"出现集数"字段
- `AI绘图关键词（英文）` 字段值为英文（非中文主体）

---

#### AC-005：prop_bible.md

**BLOCKING 检查**：
- 若有道具定义，每个道具有 `**道具ID**` 字段且格式为 `prop_XX`
- 若有道具定义，每个道具含 `AI绘图关键词（英文）` 字段且非空

**WARNING 检查**：
- 若有道具，`AI绘图关键词（英文）` 字段值为英文

---

#### AC-006：dialogue.md

**BLOCKING 检查**：
- 含"上半部分"或"Part A"章节
- 含"下半部分"或"Part B"章节
- 对话内容主体为中文

**WARNING 检查**：
- 每集总对话不超过 6 句
- 视频编号格式正确（`{project_id}-EPxx-A/B`）

---

#### AC-007：storyboard_config.json

**BLOCKING 检查**：
- 可解析为合法 JSON
- `subtitle = false`（不得为 true 或其他值）
- `visual_style` 对象存在且含 `prompt_suffix`
- `part_a` 存在
- `part_b` 存在
- `part_a.video_id` 格式为 `{project_id}-EPxx-A`
- `part_b.video_id` 格式为 `{project_id}-EPxx-B`
- `part_a.storyboard_9grid` 数组长度 = 9
- `part_b.storyboard_9grid` 数组长度 = 9
- `storyboard_9grid` 中每个元素的 `grid_number` 从 1 到 9，不缺不重
- 每个 GridItem 的 `ai_image_prompt` 字段存在且非空

**WARNING 检查**：
- `ai_image_prompt` 不包含 `visual_style.prompt_suffix` 中的关键词（避免重复注入）
- `part_a.duration_seconds = 15`
- `part_b.duration_seconds = 15`
- `total_duration_seconds = 30`

---

#### AC-008：video_index.json

**BLOCKING 检查**：
- 可解析为合法 JSON
- `project_id` 字段存在且格式为 `DM-XXX`
- `status` 字段存在（合法值：`scripted`/`media_pending`/`media_ready`/`tasks_assembled`/`ready_to_submit`/`submitted`）
- `videos` 数组存在
- `videos` 数组长度 = 25（每集一条）

**WARNING 检查**：
- 每条 video 记录含 `part_a.video_id` 和 `part_b.video_id`
- 所有 `video_id` 格式符合 `{project_id}-EPxx-A/B` 规范

---

#### AC-009：seedance_project_tasks.json

**BLOCKING 检查**：
- 可解析为合法 JSON
- `project_id` 字段存在且格式为 `DM-XXX`
- `total_tasks = 50`
- `tasks` 数组长度 = 50
- 任务排列顺序为 EP01-A, EP01-B, ..., EP25-A, EP25-B（通过 `tags` 字段验证）
- 每条任务：`prompt` 字段存在且非空
- 每条任务：`prompt` 包含关键短语 `No speech bubbles`（标准排除指令存在性验证）
- 每条任务：`prompt` 包含 `镜头1` 到 `镜头9` 共9条逐镜头描述
- 每条任务：`referenceFiles` 为非空字符串数组
- 每条任务：`referenceFiles` 中不含 base64 格式的对象（必须为相对路径字符串）
- 每条任务：`modelConfig` 存在且含 `model`、`referenceMode`、`aspectRatio`、`duration`
- 每条任务：`tags` 数组至少包含 `project_id`、`EPxx`、`"A"` 或 `"B"` 三个标签

**WARNING 检查**：
- `modelConfig.model = "Seedance 2.0 Fast"`（非默认值时警告）
- `modelConfig.duration = "15s"`（非默认值时警告）
- 任意任务的 `realSubmit = true`（提醒用户这些任务将产生真实提交）
- 任意任务的 `tags` 含 `"incomplete_refs"`（引用不完整）

---

## Checklist

- [ ] 已识别目标文件对应的契约类型
- [ ] 已按契约执行所有 BLOCKING 检查
- [ ] 已按契约执行所有 WARNING 检查
- [ ] 已输出完整报告（含通过项、BLOCKING 违规、WARNING 违规）
- [ ] 结论明确标明 PASS 或 FAIL

---

## Failure Modes

| 错误场景 | 处理方式 |
|---------|---------|
| 文件不存在 | 直接报告为 FAIL，所有检查项标记为缺失 |
| 文件无法解析（非法 JSON/Markdown） | 报告解析错误，跳过内容检查项，整体结论为 FAIL |
| 无法自动推断契约类型 | 提示用户手动指定契约类型（AC-001 到 AC-009） |
| 批量验证时某文件失败 | 继续验证其他文件，汇总报告中列出每个文件的结论 |
