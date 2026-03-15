# Skill Registry — 短剧生产体系

> **版本**：v1.0
> **日期**：2026-03-15
> **配套文档**：`docs/skill-refactor-plan.md`、`docs/stage-model.md`
> **范围**：25 集 / 30 秒 / Part A-B / 9 宫格，DM-XXX / MV-XXX 系列作品

---

## 注册表总览

### 优先级说明

| 标记 | 含义 |
|------|------|
| **P0** | 核心流程必须，系统不能运行 |
| **P1** | 重要但可用当前实现替代，应在下一迭代落地 |
| **P2** | 扩展能力，当前无此技能不影响主流程 |

### 实现状态说明

| 标记 | 含义 |
|------|------|
| `EXISTING` | 已有对应实现（可能需要重命名或剪裁边界） |
| `MVP` | 本次重构必须新建，是 MVP 交付物 |
| `P1-NEW` | 下一迭代新建 |
| `P2-NEW` | 未来迭代新建 |
| `DOC-ONLY` | 不是可执行技能，是治理文档（governance skill） |

### 全量注册表

| 分类 | skill 名称 | 优先级 | 状态 | MVP |
|------|-----------|--------|------|-----|
| governance | `drama-base` | P0 | `DOC-ONLY` | ✅ |
| governance | `prompt-rules` | P0 | `DOC-ONLY` | ✅ |
| governance | `visual-style-spec` | P1 | `DOC-ONLY` | — |
| governance | `api-config-spec` | P1 | `DOC-ONLY` | — |
| project | `init-project` | P1 | `P1-NEW` | — |
| project | `update-project-index` | P2 | `P2-NEW` | — |
| story | `write-script` | P2 | `P2-NEW` | — |
| story | `design-characters` | P2 | `P2-NEW` | — |
| story | `design-scenes` | P2 | `P2-NEW` | — |
| story | `design-props` | P2 | `P2-NEW` | — |
| production | `produce-drama` | P0 | `EXISTING` | — |
| production | `produce-mv` | P1 | `EXISTING` | — |
| episode | `write-episode-dialogue` | P2 | `P2-NEW` | — |
| episode | `write-episode-storyboard` | P2 | `P2-NEW` | — |
| delivery | `generate-media` | P0 | `EXISTING` | — |
| delivery | `assemble-tasks` | P0 | `MVP` | ✅ |
| delivery | `submit-project` | P0 | `EXISTING` | — |
| review | `validate-stage` | P0 | `MVP` | ✅ |
| review | `validate-storyboard` | P1 | `P1-NEW` | — |
| review | `validate-tasks` | P1 | `P1-NEW` | — |
| review | `inspect-submission` | P2 | `P2-NEW` | — |

> **MVP 交付物（本次重构必做）**：`drama-base`、`prompt-rules`、`assemble-tasks`、`validate-stage`

---

## 分类一：governance（治理）

> **定义**：不直接执行制作任务，提供跨 skill 的共享规范、格式约定和单一定义来源（single source of truth）。以文档形式存在，由其他 skill 在执行前引用。

---

### `drama-base`

| 字段 | 内容 |
|------|------|
| **name** | `drama-base` |
| **priority** | P0 |
| **status** | `DOC-ONLY` — MVP ✅ |
| **purpose** | 定义 9 宫格分镜格式、视频编号规则、项目目录结构、文件命名规则。是所有 production/episode/delivery skill 的格式权威来源。 |
| **when_to_use** | 在实现任何读写 `storyboard_config.json`、`video_index.json`、`seedance_project_tasks.json` 的 skill 时，必须先引用本文档确认字段名与格式。 |
| **when_not_to_use** | 不直接触发，不被用户调用。仅被其他 skill 内部引用。 |
| **inputs** | 无（静态文档） |
| **outputs** | 无（静态文档，存放于 `docs/drama-base.md`） |
| **constraints** | 字段定义一旦发布，修改须同步通知所有依赖方；不得出现两个名称不同但含义相同的字段 |
| **dependencies** | 无 |

**覆盖内容**：
- 9宫格分镜格式（`grid_number`、`time_start`、`time_end`、`camera`、`characters`、`atmosphere`、`sfx`、`ai_image_prompt` 的完整字段规范）
- 视频编号规则（`DM-XXX-EPxx-A/B`、`MV-XXX-SEGxx`）
- 项目目录结构（`episodes/`、`characters/`、`scenes/`、`props/`、`segments/`）
- 文件命名规则（`*_ref.png`、`*_storyboard.png`、`*_bible.md`）
- `storyboard_config.json` 顶层必填字段列表（含 `subtitle: false` 强制值）

---

### `prompt-rules`

| 字段 | 内容 |
|------|------|
| **name** | `prompt-rules` |
| **priority** | P0 |
| **status** | `DOC-ONLY` — MVP ✅ |
| **purpose** | 定义 Seedance prompt 的构建规则，包含：标准排除指令文本（唯一权威版本）、`(@文件名)` 引用语法、prompt 各部分的组装顺序。消除 `produce-drama` 与 `produce-mv` 各自维护排除指令导致的偏差风险。 |
| **when_to_use** | 在 `assemble-tasks` 组装任何 prompt 时必须引用。在 `produce-mv` 步7生成 MV 任务时必须引用。 |
| **when_not_to_use** | 不直接触发，不被用户调用。 |
| **inputs** | 无（静态文档） |
| **outputs** | 无（静态文档，存放于 `docs/prompt-rules.md`） |
| **constraints** | 标准排除指令文本（含中英文双语）不得被任何 skill 擅自修改；`(@文件名)` 语法中的文件名必须与 `referenceFiles[].fileName` 严格匹配 |
| **dependencies** | `drama-base`（引用文件命名规则） |

**覆盖内容**：
- 标准排除指令文本（`从镜头1开始…` 完整 115 字，唯一来源）
- prompt 组装顺序：① 头部声明（分镜图 + 角色参考图）→ ② 排除指令 → ③ 集信息行（含场景/道具内联引用）→ ④ 逐镜头描述（9条）
- `(@文件名)` 语法规范（`fileName` 与 `referenceFiles` 数组的对应关系）
- `ai_image_prompt` 注入 `visual_style.prompt_suffix` 的时机（在 assemble-tasks 阶段追加，不在 produce-drama 阶段写入）
- 缺失参考图时的降级规则（`pending` 状态资产改为纯文字描述）

---

### `visual-style-spec`

| 字段 | 内容 |
|------|------|
| **name** | `visual-style-spec` |
| **priority** | P1 |
| **status** | `DOC-ONLY` |
| **purpose** | 定义 `visual_styles.json` 的字段含义、风格注入规则（`prompt_suffix` 追加时机）、`default_style_id` 选取逻辑、双风格模式（MV专用）的行为规范。 |
| **when_to_use** | 在实现或修改 `produce-drama`、`produce-mv`、`generate-media`、`assemble-tasks` 对视觉风格的处理逻辑时引用。 |
| **when_not_to_use** | 不直接触发。 |
| **inputs** | 无（静态文档） |
| **outputs** | 无（静态文档，存放于 `docs/visual-style-spec.md`） |
| **constraints** | `prompt_suffix` 只在 `ai_image_prompt` 的最末尾追加，不插入中间；风格选择交互必须通过 `ask_questions` 工具进行，不可静默默认 |
| **dependencies** | `drama-base` |

---

### `api-config-spec`

| 字段 | 内容 |
|------|------|
| **name** | `api-config-spec` |
| **priority** | P1 |
| **status** | `DOC-ONLY` |
| **purpose** | 定义 `api_keys.json` 的标准读取路径（相对于 workspace 根目录，而非硬编码的 `/data/dongman/`）、环境变量优先级、`gemini_image_model` 合法值清单。解决当前路径硬编码问题。 |
| **when_to_use** | 在实现或修改 `generate-media` 的 Python 脚本生成逻辑时必须引用。 |
| **when_not_to_use** | 不直接触发。 |
| **inputs** | 无（静态文档） |
| **outputs** | 无（静态文档，存放于 `docs/api-config-spec.md`） |
| **constraints** | API Key 不得出现在任何 skill 文件或日志中；路径必须使用相对路径或环境变量，禁止绝对路径 |
| **dependencies** | 无 |

---

## 分类二：project（项目管理）

> **定义**：管理项目目录的初始化、元数据维护和全局索引更新。职责边界：不生成内容，只管理结构。

---

### `init-project`

| 字段 | 内容 |
|------|------|
| **name** | `init-project` |
| **priority** | P1 |
| **status** | `P1-NEW`（当前逻辑内嵌于 `produce-drama` 步1） |
| **purpose** | 创建新作品目录结构、生成 `metadata.json`、分配项目编号（`DM-XXX` 或 `MV-XXX`）、创建各子目录占位结构。 |
| **when_to_use** | 用户明确要创建一个新项目但暂不生成内容时。`produce-drama` 在完成拆分后内部将调用本技能。 |
| **when_not_to_use** | 项目目录已存在时（会误覆盖）；当用户意图是修改已有项目时 |
| **inputs** | `project_type: "drama" / "mv"`<br>`project_name: string`<br>`visual_style_id: integer`（可选） |
| **outputs** | `projects/DM-XXX_{slug}/metadata.json`<br>`projects/DM-XXX_{slug}/` 空目录结构<br>`projects/index.json`（已追加新条目，`status = "initialized"`） |
| **constraints** | 项目编号必须从 `index.json` 读取，不得手动指定；同一个 slug 不能重复创建 |
| **dependencies** | `drama-base`（目录结构规范） |

---

### `update-project-index`

| 字段 | 内容 |
|------|------|
| **name** | `update-project-index` |
| **priority** | P2 |
| **status** | `P2-NEW`（当前内嵌于 `produce-drama` 步6） |
| **purpose** | 单独更新 `projects/index.json` 中某个项目的状态字段（`status`、`video_count`、`last_updated`），不重建目录结构。 |
| **when_to_use** | 需要手动修正某个项目在全局索引中的记录时；自动化流程需要幂等地更新状态时。 |
| **when_not_to_use** | 创建新项目时（使用 `init-project`）；批量重建整个 `index.json` 时 |
| **inputs** | `project_id: string`<br>`fields: { status?, video_count?, last_updated? }` |
| **outputs** | `projects/index.json`（更新对应条目） |
| **constraints** | 只允许更新 `index.json` 中已存在的条目；不允许修改 `project_id`、`directory` 字段 |
| **dependencies** | 无 |

---

## 分类三：story（剧本创作）

> **定义**：负责创作性内容的生成。当前全部内嵌于 `produce-drama`，P2 阶段拆分后允许单独调用某一步。每个 skill 都是幂等的（可安全重跑覆盖）。

---

### `write-script`

| 字段 | 内容 |
|------|------|
| **name** | `write-script` |
| **priority** | P2 |
| **status** | `P2-NEW`（当前内嵌于 `produce-drama` 步2） |
| **purpose** | 根据题材/类型/视觉风格生成 `script/full_script.md`，包含世界观设定、故事大纲、25 集各集概要（含情感基调和关键事件）。 |
| **when_to_use** | 需要单独重写剧本，而不重新生成角色/分镜时；`produce-drama` 拆分后内部调用。 |
| **when_not_to_use** | 已有剧本且只需修改某集对话时（直接编辑 `dialogue.md`）；项目目录未初始化时 |
| **inputs** | `project_id: string`<br>`genre: string`（题材，可选）<br>`style: string`（风格，可选）<br>`visual_style_id: integer`（可选） |
| **outputs** | `script/full_script.md`（含 25 集大纲） |
| **constraints** | 第1-3集须包含世界观介绍和冲突引入；第25集须有明确结局；每集情感基调字段不能为空 |
| **dependencies** | `init-project`（项目目录存在）、`drama-base`（目录结构规范） |

---

### `design-characters`

| 字段 | 内容 |
|------|------|
| **name** | `design-characters` |
| **priority** | P2 |
| **status** | `P2-NEW`（当前内嵌于 `produce-drama` 步3） |
| **purpose** | 根据剧本生成 `characters/character_bible.md`，为每个角色提供完整的外貌描述、服装设计、性格、背景故事和英文 AI 绘图关键词。 |
| **when_to_use** | 剧本已完成、需要单独补充或重建角色设定时；`produce-drama` 拆分后内部调用。 |
| **when_not_to_use** | 角色参考图已生成后（修改角色设定将导致参考图与文字描述不一致） |
| **inputs** | `project_id: string`<br>`script/full_script.md`（必须已存在） |
| **outputs** | `characters/character_bible.md`（含所有角色的 `AI绘图关键词（英文）` 字段） |
| **constraints** | 每个角色必须有 `AI绘图关键词（英文）` 字段；关键词须为英文；主角数量建议 2-4 个，次要角色不超过 6 个 |
| **dependencies** | `write-script`（剧本已存在）、`drama-base` |

---

### `design-scenes`

| 字段 | 内容 |
|------|------|
| **name** | `design-scenes` |
| **priority** | P2 |
| **status** | `P2-NEW`（当前内嵌于 `produce-drama` 步3B） |
| **purpose** | 根据剧本生成 `scenes/scene_bible.md`，筛选出在 3 集以上反复出现的核心场景，为每个场景提供场景 ID、描述、出现集数和英文 AI 绘图关键词。 |
| **when_to_use** | 剧本已完成、需要单独补充或重建场景设定时。 |
| **when_not_to_use** | 场景参考图已生成后；只有一次性出现的场景（不需要建参考图） |
| **inputs** | `project_id: string`<br>`script/full_script.md`（必须已存在） |
| **outputs** | `scenes/scene_bible.md`（含 3-6 个核心场景，每个含 `scene_id` 和 `AI绘图关键词（英文）`） |
| **constraints** | 场景 ID 格式为 `scene_XX`（两位数字）；只收录出现 ≥ 3 集的场景；总数上限 6 个 |
| **dependencies** | `write-script`、`drama-base` |

---

### `design-props`

| 字段 | 内容 |
|------|------|
| **name** | `design-props` |
| **priority** | P2 |
| **status** | `P2-NEW`（当前内嵌于 `produce-drama` 步3C） |
| **purpose** | 根据剧本生成 `props/prop_bible.md`，筛选出具有剧情推动或象征意义的核心道具，为每个道具提供道具 ID、外观描述、象征意义和英文 AI 绘图关键词。 |
| **when_to_use** | 剧本已完成、需要单独补充或重建道具设定时。 |
| **when_not_to_use** | 道具参考图已生成后；日常无剧情意义的道具 |
| **inputs** | `project_id: string`<br>`script/full_script.md`（必须已存在） |
| **outputs** | `props/prop_bible.md`（含 2-5 个核心道具，每个含 `prop_id` 和 `AI绘图关键词（英文）`） |
| **constraints** | 道具 ID 格式为 `prop_XX`（两位数字）；只收录具有剧情意义的道具；总数上限 5 个 |
| **dependencies** | `write-script`、`drama-base` |

---

## 分类四：production（制作编排）

> **定义**：负责编排完整一部作品的全流程生成。职责边界：调用 story/episode 技能并组合结果，最终写入 `video_index.json` 并将状态推进到 `scripted`。不负责任何媒体生成或任务提交。

---

### `produce-drama`

| 字段 | 内容 |
|------|------|
| **name** | `produce-drama` |
| **priority** | P0 |
| **status** | `EXISTING`（原名 `produce-anime`，当前步1-6 范围） |
| **purpose** | 编排生成一部完整短剧作品（25 集）的全部前期制作产物，最终将 `video_index.json` 的 `status` 写入 `scripted`。是 Stage 1 的唯一执行者。 |
| **when_to_use** | 用户要从零创建一部新短剧时；唯一触发方式：自然语言指令（"制作一部短剧"、"generate short drama"）。 |
| **when_not_to_use** | 项目已处于 `media_ready` 或更后续的状态（重跑会覆盖已有剧本，但不影响已生成的媒体文件）；用户只想修改某集对话时（直接编辑 `dialogue.md`）；用户要制作 MV 时（使用 `produce-mv`） |
| **inputs** | `genre: string`（可选，不指定则随机）<br>`visual_style: string / integer`（可选，不指定则用 `default_style_id`）<br>`character_count: integer`（可选） |
| **outputs** | `projects/DM-XXX_{slug}/metadata.json`<br>`projects/DM-XXX_{slug}/script/full_script.md`<br>`characters/character_bible.md`<br>`scenes/scene_bible.md`<br>`props/prop_bible.md`<br>`episodes/EP01-EP25/dialogue.md` × 25<br>`episodes/EP01-EP25/storyboard_config.json` × 25<br>`video_index.json`（`status = "scripted"`）<br>`projects/index.json`（已更新） |
| **constraints** | 只执行 Stage 1（步1-6），**不执行原步7（任务生成）**，任务生成已拆出由 `assemble-tasks` 负责；一次运行生成且仅生成 1 部完整作品（25 集）；每集对话须为中文；所有 `subtitle` 字段强制为 `false` |
| **dependencies** | `drama-base`（格式规范）、`visual-style-spec`（风格注入规则） |

---

### `produce-mv`

| 字段 | 内容 |
|------|------|
| **name** | `produce-mv` |
| **priority** | P1 |
| **status** | `EXISTING`（需移除步7，将其对接 `assemble-tasks`） |
| **purpose** | 编排生成一部完整 MV 作品的全部前期制作产物（MV 剧本、角色/场景/道具设计、按歌曲分段的故事板配置），最终写入 `video_index.json` 的 `status = "scripted"`。 |
| **when_to_use** | 用户要根据歌词或已有 MV 剧本生成 MV 分镜时；用户提供了素材文件夹需要导入时。 |
| **when_not_to_use** | 制作短剧时（使用 `produce-drama`）；步7（任务生成）已拆出，不再在本技能中调用 |
| **inputs** | `song_title: string`（可选）<br>`lyrics_or_script_path: string`（可选）<br>`assets_folder: string`（可选，用户素材目录）<br>`visual_style: string`（可选，支持双风格如 "style_a=风格3, style_b=风格6"） |
| **outputs** | `projects/MV-XXX_{slug}/metadata.json`（`project_type: "mv"`）<br>`script/mv_script.md`<br>`characters/character_bible.md`<br>`scenes/scene_bible.md`<br>`props/prop_bible.md`<br>`segments/SEG01-SEGxx/storyboard_config.json` × N<br>`video_index.json`（`status = "scripted"`）<br>`projects/index.json`（已更新） |
| **constraints** | 段数根据歌曲时长动态计算（每段 15 秒）；双风格模式下每段通过 `active_visual_mode` 字段标记使用哪套风格；**不执行任务生成**，由 `assemble-tasks` 负责；`prompt-rules` 中的标准排除指令从文档引用，不在本技能中重复定义 |
| **dependencies** | `drama-base`、`prompt-rules`（仅用于校验格式，不生成任务）、`visual-style-spec` |

---

## 分类五：episode（集级生成）

> **定义**：管理单集内容的独立生成。当前 `produce-drama` 内部循环完成 25 集生成，P2 阶段拆分后允许单独重新生成某一集，支持并行分发给多个 agent。

---

### `write-episode-dialogue`

| 字段 | 内容 |
|------|------|
| **name** | `write-episode-dialogue` |
| **priority** | P2 |
| **status** | `P2-NEW`（当前内嵌于 `produce-drama` 步4） |
| **purpose** | 为指定集生成 `dialogue.md`，覆盖 Part A 和 Part B 的全部对话，格式为标准对话表格（序号/时间/角色/内容/语气/备注）。 |
| **when_to_use** | 需要单独重新生成某集对话时（如第15集对话不满意）；并行生成多集时由 `episode-writer` agent 批量调用。 |
| **when_not_to_use** | 角色设定尚未完成时；该集的 `storyboard_config.json` 还没有最终确认时（对话应基于分镜设计） |
| **inputs** | `project_id: string`<br>`episode: integer`（1-25）<br>`character_bible.md`（已存在）<br>`full_script.md`（已存在，参考该集概要） |
| **outputs** | `episodes/EPxx/dialogue.md`（覆盖写入） |
| **constraints** | 所有对话必须为中文；每集对话总量控制在 3-6 句（Part A 1-3 句，Part B 1-3 句）；每句不超过 15 字；不包含字幕说明 |
| **dependencies** | `design-characters`（角色已定义）、`write-script`（集概要已存在） |

---

### `write-episode-storyboard`

| 字段 | 内容 |
|------|------|
| **name** | `write-episode-storyboard` |
| **priority** | P2 |
| **status** | `P2-NEW`（当前内嵌于 `produce-drama` 步4） |
| **purpose** | 为指定集生成 `storyboard_config.json`，包含 `part_a` 和 `part_b`，每部分含 9 格分镜（含 `scene_refs`、`prop_refs`、`ai_image_prompt`）。 |
| **when_to_use** | 需要单独重新生成某集分镜时；并行生成多集时由 `episode-writer` agent 调用。 |
| **when_not_to_use** | 该集的分镜图已生成（`*_storyboard.png` 已存在）时，重新生成 JSON 会导致 JSON 与图片不一致；该集的媒体文件已生成后，不得修改已生成的分镜配置 |
| **inputs** | `project_id: string`<br>`episode: integer`<br>`character_bible.md`<br>`scene_bible.md`<br>`prop_bible.md`<br>`dialogue.md`（当集，已存在）<br>`visual_style_id: integer` |
| **outputs** | `episodes/EPxx/storyboard_config.json`（覆盖写入） |
| **constraints** | 每部分固定 9 格；`subtitle` 字段必须为 `false`；`ai_image_prompt` 须为英文且不含 `visual_style.prompt_suffix`（由 `assemble-tasks` 在后续追加）；`scene_refs` 和 `prop_refs` 中的 ID 必须与 `scene_bible.md` / `prop_bible.md` 中的 ID 一致 |
| **dependencies** | `drama-base`（9宫格格式规范）、`design-characters`、`design-scenes`、`design-props`、`write-episode-dialogue` |

---

## 分类六：delivery（交付流水线）

> **定义**：负责从剧本产物到最终视频任务提交的整条流水线。三个技能分别对应 Stage 2、Stage 3、Stage 4，顺序依赖，不可跳过。

---

### `generate-media`

| 字段 | 内容 |
|------|------|
| **name** | `generate-media` |
| **priority** | P0 |
| **status** | `EXISTING` |
| **purpose** | 调用 Google Gemini API 批量生成角色参考图、场景四宫格图、道具三视图和 9 宫格分镜图，最终写入 `media_index.json` 并将 `video_index.json` 的 `status` 推进到 `media_ready`。是 Stage 2 的唯一执行者。 |
| **when_to_use** | `video_index.json` 的 `status = "scripted"` 或 `"media_pending"` 时；需要重新生成部分失败的图片时（指定集数范围）。 |
| **when_not_to_use** | `status` 已为 `media_ready` 或更后续状态，且无图片需要重新生成时；Gemini API Key 未配置时 |
| **inputs** | `project_id: string`<br>`start_ep: integer`（可选，默认 1）<br>`end_ep: integer`（可选，默认 25）<br>`--skip-chars: boolean`（可选，跳过角色图生成） |
| **outputs** | `characters/{角色名}_ref.png` × N<br>`scenes/{scene_id}_ref.png` × M（四宫格合成图）<br>`props/{prop_id}_ref.png` × K（三视图合成图）<br>`episodes/EPxx/DM-XXX-EPxx-A_storyboard.png` × 25<br>`episodes/EPxx/DM-XXX-EPxx-B_storyboard.png` × 25<br>`characters/ref_index.json`<br>`scenes/ref_index.json`<br>`props/ref_index.json`<br>`media_index.json`（`status` 全部为 `exists: true` 时更新 `video_index.json` 为 `media_ready`） |
| **constraints** | 前置条件：`video_index.json` 存在且 `status ∈ {scripted, media_pending}`；每次 API 调用后暂停 2 秒限流；已存在的文件自动跳过（断点续传）；视频生成不在本技能中处理（由 Seedance 负责） |
| **dependencies** | `produce-drama`（Stage 1 完成）、`drama-base`（文件命名规则）、`api-config-spec`（API 配置读取） |

---

### `assemble-tasks`

| 字段 | 内容 |
|------|------|
| **name** | `assemble-tasks` |
| **priority** | P0 |
| **status** | `MVP` — 新建 ✅ |
| **purpose** | 读取 Stage 1 产物（storyboard_config × 25、dialogue.md × 25）和 Stage 2 产物（*_ref.png、*_storyboard.png），按 `prompt-rules` 规范组装 50 条 Seedance 任务，写入 `seedance_project_tasks.json`。验证通过后将 `status` 更新为 `ready_to_submit`。是 Stage 3 的唯一执行者，从 `produce-drama` 的步7中拆出。 |
| **when_to_use** | `video_index.json` 的 `status = "media_ready"` 时；需要重新组装任务时（会触发 WARNING 后允许覆盖）。 |
| **when_not_to_use** | `status ≠ "media_ready"`，如仍为 `scripted` 或 `media_pending` 时（BLOCKING 检查会拒绝）；媒体文件未全部生成时 |
| **inputs** | `project_id: string`<br>`episodes/EPxx/storyboard_config.json` × 25（读取）<br>`episodes/EPxx/dialogue.md` × 25（读取）<br>`characters/*_ref.png`（读取）<br>`scenes/*_ref.png`（读取，缺失时降级）<br>`props/*_ref.png`（读取，缺失时降级）<br>`episodes/EPxx/*_storyboard.png` × 50（读取） |
| **outputs** | `seedance_project_tasks.json`（50 条任务，`referenceFiles` 为相对路径字符串数组）<br>`video_index.json`（`status` 更新为 `tasks_assembled` → 验证通过后 `ready_to_submit`） |
| **constraints** | **Gate 条件**：见 `docs/stage-model.md` assemble-tasks 节（7 项 BLOCKING + 4 项 WARNING）；`referenceFiles` 必须为相对路径字符串数组，不得展开为 base64 对象（展开由 `submit-project` 负责）；`ai_image_prompt` 须追加 `visual_style.prompt_suffix` 后才写入 prompt；`prompt` 必须包含标准排除指令（从 `prompt-rules` 引用，不自定义）；任务排列顺序固定为 EP01-A, EP01-B, …, EP25-A, EP25-B |
| **dependencies** | `generate-media`（Stage 2 完成）、`prompt-rules`（prompt 构建规范）、`drama-base`（格式规范）、`validate-stage`（gate 校验） |

---

### `submit-project`

| 字段 | 内容 |
|------|------|
| **name** | `submit-project` |
| **priority** | P0 |
| **status** | `EXISTING`（原名 `submit-anime-project`，重命名后职责不变） |
| **purpose** | 读取 `seedance_project_tasks.json`，将 `referenceFiles` 相对路径展开为 base64 对象，按批次提交到 Seedance API（`POST /api/tasks/push`），生成 `submission_report.json`，并将 `status` 更新为 `submitted`。是 Stage 4 的唯一执行者。 |
| **when_to_use** | `video_index.json` 的 `status = "ready_to_submit"` 时；需要重试部分失败任务时（读取 `submission_report.json` 的 `failed_items`）。 |
| **when_not_to_use** | `status ≠ "ready_to_submit"`（BLOCKING 检查拒绝）；Seedance API 不可达时；`realSubmit: false` 状态下想确认"任务已完成"时（模拟模式不算真实提交） |
| **inputs** | `project_id: string`<br>`seedance_project_tasks.json`（读取）<br>`realSubmit: boolean`（可选，覆盖任务文件中的值）<br>`batch_size: integer`（可选，默认 20-50）<br>`api_base: string`（可选，默认 `http://localhost:3456`） |
| **outputs** | `submission_report.json`（含 `task_codes`、`submitted_tasks`、`failed_tasks`、`failed_items`）<br>`video_index.json`（`failed_tasks = 0` 时 `status = "submitted"`；否则保持 `ready_to_submit`） |
| **constraints** | **Gate 条件**：见 `docs/stage-model.md` submit-project 节（5 项 BLOCKING + 4 项 WARNING）；`referenceFiles` 的 base64 展开只在运行时进行，不写回 `seedance_project_tasks.json`；`submission_report.json` 已存在时触发 WARNING 但允许覆盖；`failed_tasks > 0` 时不更新状态 |
| **dependencies** | `assemble-tasks`（Stage 3 完成）、`validate-stage`（gate 校验） |

---

## 分类七：review（验证与审查）

> **定义**：负责在各阶段边界进行质量校验。`validate-stage` 是 Gate 条件的执行者，`validate-storyboard` 和 `validate-tasks` 验证产物结构完整性，`inspect-submission` 分析提交结果。

---

### `validate-stage`

| 字段 | 内容 |
|------|------|
| **name** | `validate-stage` |
| **priority** | P0 |
| **status** | `MVP` — 新建 ✅ |
| **purpose** | 检查当前项目的阶段状态是否满足指定操作的准入条件，输出 BLOCKING 和 WARNING 两类检查结果。被 `assemble-tasks` 和 `submit-project` 在执行前调用，也可由用户单独调用以诊断当前状态。 |
| **when_to_use** | 在运行 `assemble-tasks` 或 `submit-project` 之前自动调用；用户不确定当前应运行哪个技能时手动调用（"检查一下 DM-001 现在可以做什么"）。 |
| **when_not_to_use** | 在 `produce-drama` 或 `generate-media` 内部（这两个技能不依赖 Gate 条件，自主写入状态）；频繁轮询时（本技能是只读诊断，不修改任何状态） |
| **inputs** | `project_id: string`<br>`target_action: "assemble-tasks" / "submit-project"`（可选，指定要校验哪个操作的 Gate） |
| **outputs** | 检查报告（控制台输出）：`BLOCKING` 列表（含失败原因）、`WARNING` 列表、`PASS/FAIL` 总结、建议下一步操作<br>**不修改任何文件** |
| **constraints** | 只读操作，不得修改任何文件；BLOCKING 项必须完整列出所有失败原因，不得只报告第一个；不依赖 AI 内容生成，完全基于文件系统检查 |
| **dependencies** | `drama-base`（文件命名规则，用于校验路径格式）、`stage-model`（Gate 条件定义，见 `docs/stage-model.md`） |

---

### `validate-storyboard`

| 字段 | 内容 |
|------|------|
| **name** | `validate-storyboard` |
| **priority** | P1 |
| **status** | `P1-NEW` |
| **purpose** | 对指定集（或全部 25 集）的 `storyboard_config.json` 进行结构完整性校验，检查必填字段是否存在、`storyboard_9grid` 是否恰好 9 格、`subtitle` 是否为 `false`、`scene_refs` / `prop_refs` 中的 ID 是否在对应 Bible 文件中有定义。 |
| **when_to_use** | `produce-drama` 完成后的自查；在运行 `generate-media` 之前发现异常分镜配置时；修改了某集 `storyboard_config.json` 后验证格式。 |
| **when_not_to_use** | 分镜图已生成后（此时修改 JSON 会导致不一致，应先评估影响再决定是否修改） |
| **inputs** | `project_id: string`<br>`episode: integer / "all"`（可选，默认 `"all"`） |
| **outputs** | 校验报告（控制台输出）：每集的 PASS/FAIL 状态、字段缺失清单、格数异常清单<br>**不修改任何文件** |
| **constraints** | 只读；若 `scenes/scene_bible.md` 不存在则跳过 `scene_refs` 校验并输出 WARNING；只验证结构，不验证内容质量（如 AI prompt 的语义合理性） |
| **dependencies** | `drama-base`（格式规范）、`design-scenes`、`design-props`（Bible 文件须存在） |

---

### `validate-tasks`

| 字段 | 内容 |
|------|------|
| **name** | `validate-tasks` |
| **priority** | P1 |
| **status** | `P1-NEW` |
| **purpose** | 对 `seedance_project_tasks.json` 进行完整性校验，包括：任务总数是否为 50、每条任务的 `prompt` 是否包含标准排除指令、是否包含 9 条镜头描述、`referenceFiles` 路径是否全部真实存在、`tags` 是否包含必要字段。 |
| **when_to_use** | `assemble-tasks` 完成后的自查；准备真实提交（`realSubmit: true`）前的最终校验；发现 Seedance 端报错后反查任务文件格式。 |
| **when_not_to_use** | `seedance_project_tasks.json` 尚未生成时；只需要快速确认状态时（用 `validate-stage` 即可） |
| **inputs** | `project_id: string` |
| **outputs** | 校验报告（控制台输出）：总体 PASS/FAIL、各任务的问题清单（缺失字段、路径不存在、prompt 格式问题）<br>**不修改任何文件** |
| **constraints** | 只读；标准排除指令的检查以关键短语（`No speech bubbles`）为锚点，允许微小文本差异；路径校验基于 assemble-tasks 写入时的项目根目录 |
| **dependencies** | `assemble-tasks`（任务文件须存在）、`prompt-rules`（用于校验 prompt 格式） |

---

### `inspect-submission`

| 字段 | 内容 |
|------|------|
| **name** | `inspect-submission` |
| **priority** | P2 |
| **status** | `P2-NEW` |
| **purpose** | 读取 `submission_report.json`，分析提交结果：统计成功/失败任务数量，列出失败任务的 `description` 和 `tags`，生成可直接复用于重提交的失败任务子集文件 `submission_retry.json`。 |
| **when_to_use** | `submit-project` 完成后发现 `failed_tasks > 0` 时；需要追踪哪些 Seedance taskCodes 对应哪些集时。 |
| **when_not_to_use** | `submission_report.json` 不存在时；`failed_tasks = 0`（全部成功）时，无需运行 |
| **inputs** | `project_id: string`<br>`submission_report.json`（读取） |
| **outputs** | 分析报告（控制台输出）：成功/失败分布、失败任务列表<br>`submission_retry.json`（可选，仅在有失败任务时生成，格式与 `seedance_project_tasks.json` 一致但只含失败条目） |
| **constraints** | 只读（除生成 `submission_retry.json` 外）；`submission_retry.json` 不覆盖 `seedance_project_tasks.json` |
| **dependencies** | `submit-project`（报告文件须存在） |

---

## MVP 交付物清单

以下 4 个技能为本次重构的最小可落地范围，其余技能在后续迭代落地。

| # | skill 名称 | 分类 | 类型 | 交付形式 |
|---|-----------|------|------|---------|
| 1 | `drama-base` | governance | DOC-ONLY | 新增 `docs/drama-base.md` |
| 2 | `prompt-rules` | governance | DOC-ONLY | 新增 `docs/prompt-rules.md` |
| 3 | `assemble-tasks` | delivery | 可执行技能 | 新增 `.claude/skills/assemble-tasks/SKILL.md` |
| 4 | `validate-stage` | review | 可执行技能 | 新增 `.claude/skills/validate-stage/SKILL.md` |

**MVP 完成后的系统行为变化**：
- `produce-drama` 的步7（任务生成）可标记为 deprecated，用户运行步7时系统提示改用 `assemble-tasks`
- `assemble-tasks` 在执行前通过 `validate-stage` 做 Gate 校验，有文件缺失时立即报错而非静默跳过
- `submit-project` 的 Gate 条件更新：新增对 `status = "ready_to_submit"` 的检查，防止跳过 `assemble-tasks` 直接提交

---

## 依赖关系图

```
governance layer（文档，被引用）
  drama-base ◄──────────────────────── 所有写/读 storyboard 的技能
  prompt-rules ◄───────────────────── assemble-tasks, produce-mv (步7)
  visual-style-spec ◄──────────────── produce-drama, produce-mv, generate-media
  api-config-spec ◄────────────────── generate-media

production layer（编排）
  produce-drama
    └── [内部] init-project (P1)
    └── [内部] write-script (P2)
    └── [内部] design-characters (P2)
    └── [内部] design-scenes (P2)
    └── [内部] design-props (P2)
    └── [内部] write-episode-dialogue × 25 (P2)
    └── [内部] write-episode-storyboard × 25 (P2)

delivery layer（流水线）
  generate-media ──────► assemble-tasks ──────► submit-project
  [Stage 2]              [Stage 3, MVP]          [Stage 4]
                              │
                         validate-stage (MVP)
                              │
                        validate-tasks (P1)

review layer（质量保障）
  validate-stage ◄──── assemble-tasks, submit-project（执行前调用）
  validate-storyboard ◄── 用户手动调用，produce-drama 完成后
  validate-tasks ◄────── assemble-tasks 完成后
  inspect-submission ◄─── submit-project 完成后
```

---

## 实施优先级排期

| 迭代 | 交付内容 | 依赖 |
|------|---------|------|
| **MVP（当前）** | `drama-base`、`prompt-rules`、`assemble-tasks`、`validate-stage` | 无外部依赖 |
| **P1 迭代** | `visual-style-spec`、`api-config-spec`、`init-project`、`validate-storyboard`、`validate-tasks`、`produce-mv`（移除步7） | MVP 完成后 |
| **P2 迭代** | `write-script`、`design-characters`、`design-scenes`、`design-props`、`write-episode-dialogue`、`write-episode-storyboard`、`update-project-index`、`inspect-submission` | P1 完成后 |
