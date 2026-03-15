# 短剧生产流程阶段状态模型

> **版本**：v1.0
> **日期**：2026-03-15
> **配套文档**：`docs/skill-refactor-plan.md`（产物契约定义）
> **范围**：25 集 / 30 秒 / Part A-B / 9 宫格，DM-XXX 系列作品

---

## 总览

### 状态机图

```
produce-anime(步1-6)         generate-media              assemble-tasks            submit-project
        │                          │                           │                        │
        ▼                          ▼                           ▼                        ▼
  ┌───────────┐             ┌─────────────┐           ┌──────────────────┐      ┌────────────┐
  │ SCRIPTED  │──────────►  │ MEDIA_READY │──────────►│ TASKS_ASSEMBLED  │─────►│ SUBMITTED  │
  └───────────┘             └─────────────┘           └──────────────────┘      └────────────┘
       │                                                       │
       │ （可选的显式中间状态）                                   │（可选的显式验证状态）
       ▼                                                       ▼
┌──────────────┐                                      ┌──────────────────┐
│ MEDIA_PENDING│                                      │ READY_TO_SUBMIT  │
└──────────────┘                                      └──────────────────┘
```

### 状态一览表

| # | 状态标识 | 中文名 | 写入者 | 前置状态 |
|---|---------|--------|--------|---------|
| 1 | `scripted` | 前期制作完成 | produce-anime | —（初始） |
| 2 | `media_pending` | 媒体待生成 | produce-anime（可选写入） | scripted |
| 3 | `media_ready` | 媒体生成完成 | generate-media | media_pending / scripted |
| 4 | `tasks_assembled` | 任务已组装 | assemble-tasks | media_ready |
| 5 | `ready_to_submit` | 可提交 | assemble-tasks（验证后写入） | tasks_assembled |
| 6 | `submitted` | 已提交 | submit-project | ready_to_submit |

**状态的物理载体**：`video_index.json` 根字段 `"status"`。
该字段是整个生产流程的**唯一可信状态源（single source of truth）**。

---

## 阶段详细定义

---

### Stage 1 — `scripted`（前期制作完成）

#### Purpose
标志 produce-anime 的创作性工作（剧本、角色设计、分镜规划）已全部完成，项目进入等待媒体资产生成的状态。

#### Required Artifacts

| 文件路径 | 类型 | 说明 |
|---------|------|------|
| `metadata.json` | 必须存在 | 含 `project_id`、`project_name`、`visual_style` |
| `script/full_script.md` | 必须存在 | 含 25 集大纲及各集剧情摘要 |
| `characters/character_bible.md` | 必须存在 | 含所有角色的 `AI绘图关键词（英文）` 字段 |
| `scenes/scene_bible.md` | 必须存在 | 含所有场景的 `AI绘图关键词（英文）` 字段 |
| `props/prop_bible.md` | 必须存在 | 含所有道具的 `AI绘图关键词（英文）` 字段（若无道具可为空文件） |
| `episodes/EP01/dialogue.md` … `episodes/EP25/dialogue.md` | 必须全部存在 | 共 25 个文件，每集覆盖 Part A 和 Part B |
| `episodes/EP01/storyboard_config.json` … `EP25/` | 必须全部存在 | 共 25 个文件，每个含 `part_a` 和 `part_b`，各含 9 格分镜 |
| `video_index.json` | 必须存在 | `status = "scripted"`，`videos` 数组含 25 条，每条含 `part_a` 和 `part_b` |
| `projects/index.json` | 必须已更新 | 含本作品条目 |

#### Exit Criteria（退出条件）
以下所有条件同时满足，方可离开本阶段：

1. 上表所有文件均存在且非空
2. `video_index.json` 的 `status` 字段为 `"scripted"`
3. `video_index.json` 的 `videos` 数组恰好有 25 条记录
4. 每条记录均包含 `part_a.video_id` 和 `part_b.video_id`，格式为 `DM-XXX-EPxx-A` / `DM-XXX-EPxx-B`
5. 所有 `storyboard_config.json` 中 `subtitle` 字段均为 `false`
6. 所有 `storyboard_config.json` 中 `visual_style` 字段均已填写

#### Forbidden Actions（禁止动作）
在 `status = "scripted"` 时，以下操作**不应执行**：

| 禁止操作 | 原因 |
|---------|------|
| 运行 `assemble-tasks` | 媒体文件尚未生成，所有 `referenceFiles` 将无法解析 |
| 运行 `submit-project` | 不存在 `seedance_project_tasks.json` |
| 修改任意 `storyboard_config.json` 的 `part_a/part_b` 结构 | 将与后续媒体文件命名产生不一致 |
| 手动写入 `media_index.json` | 媒体索引只能由 generate-media 写入 |

#### Next Stage
→ `media_pending`（若 produce-anime 主动标记）或直接进入 `media_ready`（generate-media 执行完成后）

---

### Stage 2 — `media_pending`（媒体待生成）

#### Purpose
明确记录"生成工作已完成、媒体生成尚未开始"这一过渡状态，避免 generate-media 被遗漏或重复触发。此状态是**可选的显式状态**：如果 produce-anime 不主动写入该状态，则 `scripted` 状态将直接被 `media_ready` 覆盖。

#### Required Artifacts
与 Stage 1 的 Required Artifacts 完全相同（无新增产物）。

#### 状态写入方式
produce-anime 在第六步（更新全局索引）完成后，**可以**将 `video_index.json` 的 `status` 更新为 `"media_pending"` 作为显式标记。
若未写入该值，则 `video_index.json` 的 `status` 将保持 `"scripted"`，不影响后续流程。

#### Exit Criteria
generate-media 执行完成后，通过 Stage 3 的进入检查，退出本状态进入 `media_ready`。

#### Forbidden Actions

| 禁止操作 | 原因 |
|---------|------|
| 运行 `assemble-tasks` | 与 scripted 状态相同，媒体文件仍未生成 |
| 运行 `submit-project` | 与 scripted 状态相同 |

#### Next Stage
→ `media_ready`（generate-media 完成后写入）

---

### Stage 3 — `media_ready`（媒体生成完成）

#### Purpose
标志所有 AI 生成的参考图和分镜图均已落盘，项目可以进入任务组装阶段。这是 `assemble-tasks` 的**最低准入阶段**。

#### Required Artifacts

除继承 Stage 1 的所有产物外，还需新增：

| 文件路径 | 类型 | 说明 |
|---------|------|------|
| `characters/{角色名}_ref.png` | 必须存在（每角色1张） | 由 generate-media Phase 1 生成 |
| `scenes/{scene_id}_ref.png` | 必须存在（每场景1张） | 四宫格合成图，由 Phase 1B 生成 |
| `props/{prop_id}_ref.png` | 道具存在时必须有 | 三视图合成图，由 Phase 1C 生成 |
| `episodes/EPxx/DM-XXX-EPxx-A_storyboard.png` | 必须存在（共 25 张） | 9宫格分镜图，由 Phase 2 生成 |
| `episodes/EPxx/DM-XXX-EPxx-B_storyboard.png` | 必须存在（共 25 张） | 9宫格分镜图，由 Phase 2 生成 |
| `media_index.json` | 必须存在 | 含 `storyboards` 数组，所有条目的 `exists` 字段均为 `true` |
| `characters/ref_index.json` | 必须存在 | 角色名 → 图片路径映射 |
| `scenes/ref_index.json` | 若有场景则必须存在 | 场景 ID → 图片路径映射 |
| `props/ref_index.json` | 若有道具则必须存在 | 道具 ID → 图片路径映射 |

#### Exit Criteria
1. `media_index.json` 存在且 `storyboards` 数组恰好有 50 条记录
2. 所有 50 条 `storyboards[].exists` 均为 `true`
3. `characters/ref_index.json` 中记录的所有图片路径均真实存在于磁盘
4. `video_index.json` 的 `status` 字段已被更新为 `"media_ready"`

#### Forbidden Actions

| 禁止操作 | 原因 |
|---------|------|
| 运行 `submit-project` | `seedance_project_tasks.json` 尚未生成 |
| 删除或覆盖任意 `*_ref.png` 文件 | 将导致 assemble-tasks 的 referenceFiles 路径校验失败 |
| 重新运行 produce-anime 步 1-6 并覆盖 `storyboard_config.json` | 将与已生成的分镜图命名产生不一致 |

#### Next Stage
→ `tasks_assembled`（assemble-tasks 完成后写入）

---

### Stage 4 — `tasks_assembled`（任务已组装）

#### Purpose
标志 `seedance_project_tasks.json` 已完整生成，所有 50 条任务的 `prompt` 和 `referenceFiles`（相对路径）均已按规则组装完毕，但尚未经过提交前最终验证。

#### Required Artifacts

除继承所有前序产物外，还需新增：

| 文件路径 | 类型 | 说明 |
|---------|------|------|
| `seedance_project_tasks.json` | 必须存在 | 根字段 `total_tasks = 50`，`tasks` 数组有 50 条 |

每条 Task 的必要字段：

| 字段 | 要求 |
|------|------|
| `prompt` | 非空字符串，含标准排除指令、`(@文件名)` 引用 |
| `description` | 非空字符串 |
| `modelConfig` | 含 `model`、`referenceMode`、`aspectRatio`、`duration` |
| `referenceFiles` | 字符串数组，相对路径，至少含1个分镜图路径 |
| `realSubmit` | boolean，默认 `false` |
| `tags` | 字符串数组，至少含 `[project_id, "EPxx", "A"/"B"]` |

#### Exit Criteria

此阶段分为两个子步骤：

**4a. 机械组装（Assembled）**
- `seedance_project_tasks.json` 文件存在且 `total_tasks = 50`
- 任务排列顺序为 EP01-A, EP01-B, ..., EP25-A, EP25-B

**4b. 路径完整性验证（Validated）→ 进入 Stage 5**
- `referenceFiles` 中列出的所有相对路径均可在项目目录下找到对应文件
- 所有 50 个 `prompt` 均包含标准排除指令文本（包含关键短语 `No speech bubbles`）
- 所有 50 个 `prompt` 均包含 9 条镜头描述（`镜头1` 到 `镜头9`）

**当 4a 完成但 4b 未通过时**：`status` 仍为 `"tasks_assembled"`，不晋升到 `ready_to_submit`。

#### Forbidden Actions

| 禁止操作 | 原因 |
|---------|------|
| 运行 `submit-project`（跳过 Stage 5） | 可能提交含损坏引用的任务，导致 Seedance 端报错 |
| 删除 `media_index.json` | 将无法重新验证分镜图是否完整 |
| 将 `referenceFiles` 从相对路径格式改为 base64 对象 | 格式由 submit-project 在提交时负责转换，tasks 文件中只保存路径 |

#### Next Stage
→ `ready_to_submit`（验证通过后由 assemble-tasks 写入）

---

### Stage 5 — `ready_to_submit`（可提交）

#### Purpose
标志本作品已通过所有提交前校验，可以安全执行真实提交（`realSubmit: true`）。此阶段是 `submit-project` 的**最低准入阶段**。

#### Required Artifacts

与 Stage 4 相同，无新增文件。
关键差异：`video_index.json` 的 `status` 字段值为 `"ready_to_submit"`。

#### 进入条件（同时也是 submit-project 的 Gate 条件，见下节）
1. `seedance_project_tasks.json` 存在且 `total_tasks = 50`
2. 所有 `referenceFiles` 路径均已解析为真实文件
3. 所有 `prompt` 均通过格式完整性检查
4. `video_index.json` 的 `status = "ready_to_submit"`

#### Exit Criteria
`submit-project` 执行并返回 `success: true`，生成 `submission_report.json`。

#### Forbidden Actions

| 禁止操作 | 原因 |
|---------|------|
| 重新运行 `assemble-tasks` 并覆盖 `seedance_project_tasks.json` | 将使当前的 ready 状态失效，需重新验证 |
| 手动修改 `seedance_project_tasks.json` 中任何 task 的 `referenceFiles` | 可能使已通过的路径校验失效 |
| 在 `realSubmit: false` 状态下判断"提交已完成" | 模拟模式不产生真实 taskCodes，不算已提交 |

#### Next Stage
→ `submitted`（submit-project 完成后写入）

---

### Stage 6 — `submitted`（已提交）

#### Purpose
标志所有 50 条任务均已成功推送到 Seedance API，`taskCodes` 已记录在 `submission_report.json` 中。此为终态。

#### Required Artifacts

| 文件路径 | 类型 | 说明 |
|---------|------|------|
| `submission_report.json` | 必须存在 | 含 `submitted_tasks = 50`、`failed_tasks = 0`、`task_codes` 数组 |
| `video_index.json` | `status = "submitted"` | 终态标记 |

`submission_report.json` 必要字段：

| 字段 | 要求 |
|------|------|
| `project_id` | 与 metadata.json 一致 |
| `submitted_at` | ISO 8601 时间戳 |
| `total_tasks` | 50 |
| `submitted_tasks` | 50（若有失败则不能进入此状态） |
| `failed_tasks` | 0 |
| `task_codes` | 非空字符串数组，长度 = submitted_tasks |
| `failed_items` | 空数组 `[]` |

#### Exit Criteria
本阶段为终态，无后续阶段。

#### Forbidden Actions

| 禁止操作 | 原因 |
|---------|------|
| 重新运行 `submit-project` 而不先确认意图 | 将产生重复提交，消耗额外算力配额 |
| 删除 `submission_report.json` | 将丢失 taskCodes，无法追踪 Seedance 端的生成结果 |
| 将 `video_index.json` 的 `status` 回退到前序状态 | 状态机只允许单向前进 |

#### Next Stage
终态，无下一阶段。

---

## Gate 条件定义

### assemble-tasks 的 Gate 条件

`assemble-tasks` 在执行前必须按顺序完成以下检查，任意一项 BLOCKING 检查失败则**立即中止并报错**，不得继续执行。

#### BLOCKING Checks（阻断检查）

| # | 检查项 | 检查方式 | 失败时的错误消息模板 |
|---|--------|---------|---------------------|
| B1 | `video_index.json` 必须存在 | 文件系统检查 | `[BLOCK] video_index.json 不存在，请先运行 produce-anime 完成前期制作` |
| B2 | `video_index.json` 的 `status` 必须为 `"media_ready"` 或 `"ready_to_submit"` 之前的合法值 | 读取并比较 status 字段 | `[BLOCK] 当前状态为 "{status}"，assemble-tasks 需要 status = "media_ready"，请先运行 generate-media` |
| B3 | `media_index.json` 必须存在 | 文件系统检查 | `[BLOCK] media_index.json 不存在，请先运行 generate-media 生成媒体文件` |
| B4 | 所有 50 张分镜图必须存在 | 读取 `media_index.json` 的 `storyboards` 数组，逐条检查 `exists` 字段 | `[BLOCK] {count} 张分镜图缺失，缺失列表：{missing_list}，请重新运行 generate-media` |
| B5 | 所有角色参考图必须存在 | 读取 `characters/ref_index.json`，逐条检查文件路径是否真实存在 | `[BLOCK] 以下角色参考图缺失：{missing_chars}，请重新运行 generate-media` |
| B6 | 所有 25 个 `storyboard_config.json` 必须存在 | 文件系统检查 EP01-EP25 | `[BLOCK] {count} 个 storyboard_config.json 缺失，缺失集：{missing_eps}` |
| B7 | 所有 25 个 `dialogue.md` 必须存在 | 文件系统检查 EP01-EP25 | `[BLOCK] {count} 个 dialogue.md 缺失，缺失集：{missing_eps}` |

#### WARNING Checks（警告检查）

WARNING 不阻断执行，但必须在控制台输出警告，并在生成的 `seedance_project_tasks.json` 中对应 task 的 `tags` 里追加 `"incomplete_refs"` 标记。

| # | 检查项 | 检查方式 | 警告消息模板 |
|---|--------|---------|------------|
| W1 | 场景参考图是否全部存在 | 读取 `scenes/ref_index.json`，逐条检查文件路径 | `[WARN] 场景参考图缺失：{missing_scenes}，相关集的 prompt 将降级为纯文字描述` |
| W2 | 道具参考图是否全部存在 | 读取 `props/ref_index.json`，逐条检查文件路径 | `[WARN] 道具参考图缺失：{missing_props}，相关集的 prompt 将降级为纯文字描述` |
| W3 | 是否存在旧的 `seedance_project_tasks.json` | 文件系统检查 | `[WARN] 已存在 seedance_project_tasks.json（创建于 {date}），将被覆盖` |
| W4 | `media_index.json` 中是否有 `exists: false` 的边缘条目 | 遍历所有字段 | `[WARN] media_index.json 中存在 exists: false 的条目：{list}` |

#### Gate 通过后的必要动作

所有 BLOCKING 检查通过后，assemble-tasks 还必须：
1. 在生成 `seedance_project_tasks.json` 完成后，执行路径完整性验证（Stage 4 的 4b 子步骤）
2. 验证通过后，将 `video_index.json` 的 `status` 更新为 `"ready_to_submit"`
3. 验证失败（部分路径无效）时，将 `status` 保留为 `"tasks_assembled"`，并在报告中列出失败条目

---

### submit-project 的 Gate 条件

`submit-project` 在执行前必须完成以下检查，任意 BLOCKING 项失败则**立即中止**。

#### BLOCKING Checks（阻断检查）

| # | 检查项 | 检查方式 | 失败时的错误消息模板 |
|---|--------|---------|---------------------|
| B1 | `seedance_project_tasks.json` 必须存在 | 文件系统检查 | `[BLOCK] seedance_project_tasks.json 不存在，请先运行 assemble-tasks` |
| B2 | `total_tasks` 必须等于 50 | 读取并比较字段值 | `[BLOCK] total_tasks = {actual}，期望 50，任务文件不完整，请重新运行 assemble-tasks` |
| B3 | `video_index.json` 的 `status` 必须为 `"ready_to_submit"` | 读取并比较 status 字段 | `[BLOCK] 当前状态为 "{status}"，submit-project 需要 status = "ready_to_submit"，请确认已运行 assemble-tasks 且验证通过` |
| B4 | 所有 task 的 `referenceFiles` 中的路径必须全部存在于磁盘 | 遍历所有 50 条任务的 `referenceFiles` 数组，逐路径检查文件是否存在 | `[BLOCK] {count} 条任务存在无效 referenceFiles 路径，失败任务：{task_ids}，请重新运行 assemble-tasks` |
| B5 | Seedance API 服务必须可达 | 向 `{api_base}/api/config` 发送 GET 请求 | `[BLOCK] Seedance API 不可达（{api_base}），请检查服务是否启动` |

#### WARNING Checks（警告检查）

| # | 检查项 | 检查方式 | 警告消息模板 |
|---|--------|---------|------------|
| W1 | 任意 task 的 `realSubmit` 为 `false` | 遍历所有任务 | `[WARN] {count} 条任务的 realSubmit = false，这些任务将进入模拟模式，不会真实生成视频` |
| W2 | `submission_report.json` 已存在 | 文件系统检查 | `[WARN] 已存在 submission_report.json（提交于 {date}），本次运行将覆盖。如为重复提交，请确认意图` |
| W3 | 任意 task 的 `tags` 含 `"incomplete_refs"` | 遍历所有任务的 tags | `[WARN] {count} 条任务标记了 incomplete_refs，这些任务的角色/场景/道具参考图不完整，视频生成质量可能下降` |
| W4 | `total_tasks` 与 `tasks` 数组实际长度不一致 | 比较字段值与数组长度 | `[WARN] total_tasks 字段值（{declared}）与 tasks 数组实际长度（{actual}）不一致，以实际长度为准` |

#### Gate 通过后的必要动作

所有 BLOCKING 检查通过后，submit-project 在提交完成后必须：
1. 将 `video_index.json` 的 `status` 更新为 `"submitted"`
2. 写入 `submission_report.json`（含所有 taskCodes 和时间戳）
3. 若有失败任务（`failed_tasks > 0`），保持 `status = "ready_to_submit"` 不变，并在报告中列出失败条目以供重试

---

## Blocking Checks vs Warning Checks 完整对照

### 设计原则

| 类型 | 含义 | 遇到时的行为 |
|------|------|------------|
| **BLOCKING** | 继续执行必然导致不可恢复的错误（文件不存在、状态不合法、服务不可达） | 立即中止，打印错误，不写入任何新文件，`status` 保持不变 |
| **WARNING** | 继续执行可以完成，但产出质量或完整性有所降低 | 打印警告，继续执行，在产出物中标记受影响条目（如 `"incomplete_refs"` tag） |

### assemble-tasks 完整检查清单

```
BLOCKING（必须全部通过才能继续）
  [B1] video_index.json 存在
  [B2] video_index.json.status = "scripted" | "media_pending" | "media_ready"（不能已是 tasks_assembled 之后的状态，除非用户明确要求重建）
  [B3] media_index.json 存在
  [B4] 所有 50 张 storyboard PNG 存在（验证 media_index.storyboards[].exists = true）
  [B5] 所有角色 *_ref.png 存在（验证 characters/ref_index.json 中所有路径）
  [B6] 所有 25 个 storyboard_config.json 存在
  [B7] 所有 25 个 dialogue.md 存在

WARNING（打印后继续执行）
  [W1] 所有场景 *_ref.png 存在
  [W2] 所有道具 *_ref.png 存在
  [W3] seedance_project_tasks.json 是否已存在（覆盖确认）
  [W4] media_index.json 中是否有 exists: false 条目
```

### submit-project 完整检查清单

```
BLOCKING（必须全部通过才能继续）
  [B1] seedance_project_tasks.json 存在
  [B2] seedance_project_tasks.json.total_tasks = 50
  [B3] video_index.json.status = "ready_to_submit"
  [B4] 所有任务的 referenceFiles 路径均真实存在
  [B5] Seedance API 服务可达（GET /api/config 返回 200）

WARNING（打印后继续执行）
  [W1] 任意 task.realSubmit = false
  [W2] submission_report.json 已存在（重复提交检测）
  [W3] 任意 task.tags 含 "incomplete_refs"
  [W4] total_tasks 与 tasks 数组长度不一致
```

---

## 状态转换的写入责任

以下表格明确各技能对 `video_index.json` 的写入责任，确保没有技能"越权"写入不属于自己阶段的状态。

| 技能 | 可以写入的 status 值 | 禁止写入的 status 值 |
|------|---------------------|---------------------|
| `produce-anime` | `"scripted"`、`"media_pending"`（可选） | `"media_ready"` 及之后的所有状态 |
| `generate-media` | `"media_ready"` | `"scripted"`、`"tasks_assembled"` 及之后的所有状态 |
| `assemble-tasks` | `"tasks_assembled"`、`"ready_to_submit"` | `"scripted"`、`"media_pending"`、`"media_ready"`、`"submitted"` |
| `submit-project` | `"submitted"` | 所有前序状态 |

---

## 异常路径处理

### 媒体生成部分失败（generate-media 中断）

**场景**：generate-media 运行到 EP13 时 Gemini API 超限，EP14-EP25 的分镜图未生成。

**处理方式**：
1. generate-media 不将 `status` 写入 `"media_ready"`（因为 media_index.json 中有 `exists: false` 条目）
2. `status` 保持 `"media_pending"`（或 `"scripted"`）
3. 用户可指定范围重新运行 generate-media（`generate-media 14 25`）
4. 所有 50 张分镜图生成完毕后，generate-media 更新 `status = "media_ready"`

**assemble-tasks 的行为**：遇到 `status ≠ "media_ready"` 时触发 BLOCKING [B2]，拒绝执行。

---

### 任务提交部分失败（submit-project 中途报错）

**场景**：提交到第 35 条时 Seedance API 返回 5xx，后续 15 条未能提交。

**处理方式**：
1. submit-project 生成 `submission_report.json`，其中 `submitted_tasks = 35`、`failed_tasks = 15`、`failed_items` 列出未提交的 task 描述
2. `video_index.json` 的 `status` **不更新为 `"submitted"`**，保持 `"ready_to_submit"`
3. 用户可重新运行 submit-project，此时 submit-project 的 WARNING [W2]（已存在报告）会触发
4. submit-project 应支持"只重试 failed_items"模式：读取上次报告的 `failed_items`，仅提交这些任务

---

### 强制重建任务文件（assemble-tasks 重跑）

**场景**：用户发现某集的 prompt 生成有误，需要重新运行 assemble-tasks。

**处理方式**：
1. assemble-tasks 检测到 `status = "ready_to_submit"`，触发 WARNING [W3]
2. 用户确认覆盖后，assemble-tasks 将 `status` 临时回退为 `"tasks_assembled"` 再执行
3. 执行完成后重新验证，通过则写入 `"ready_to_submit"`
4. 注意：如果对应的媒体文件没有变化，不需要重新运行 generate-media

**状态的唯一合法回退**：`"ready_to_submit"` → `"tasks_assembled"`（仅当用户明确重建任务时）。所有其他状态不允许回退。

---

## 附录：状态值与可执行操作矩阵

| 当前 status | produce-anime | generate-media | assemble-tasks | submit-project |
|------------|:------------:|:-------------:|:--------------:|:--------------:|
| （未创建） | ✅ 允许 | ❌ 禁止 | ❌ 禁止 | ❌ 禁止 |
| `scripted` | ⚠️ 会覆盖 | ✅ 允许 | ❌ BLOCK | ❌ BLOCK |
| `media_pending` | ⚠️ 会覆盖 | ✅ 允许 | ❌ BLOCK | ❌ BLOCK |
| `media_ready` | ⚠️ 会覆盖 | ⚠️ 会覆盖 | ✅ 允许 | ❌ BLOCK |
| `tasks_assembled` | ⚠️ 会覆盖 | ⚠️ 会覆盖 | ⚠️ 警告后允许 | ❌ BLOCK |
| `ready_to_submit` | ⚠️ 会覆盖 | ⚠️ 会覆盖 | ⚠️ 警告后允许 | ✅ 允许 |
| `submitted` | ⚠️ 会覆盖 | ⚠️ 会覆盖 | ⚠️ 警告后允许 | ⚠️ 警告后允许 |

> **图例**：
> - ✅ 允许：正常执行路径
> - ❌ 禁止：BLOCKING 检查失败，立即中止
> - ⚠️ 警告后允许：触发 WARNING，但允许用户确认后继续
