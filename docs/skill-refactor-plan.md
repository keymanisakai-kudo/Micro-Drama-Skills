# 短剧 Skill 体系重构方案

> **版本**：v1.0
> **日期**：2026-03-15
> **范围**：25集 / 30秒 / Part A-B / 9宫格，当前三技能体系
> **目标**：拆分职责、明确阶段边界、定义产物契约，使各技能可独立执行和验证

---

## 一、现状分析

### 1.1 当前技能清单

| 技能 | 文件 | 当前职责 |
|------|------|---------|
| `produce-anime` | `.claude/skills/produce-anime/SKILL.md` | 项目初始化 → 剧本 → 角色/场景/道具设计 → 25集内容生成 → 索引 → Seedance任务生成（共7步） |
| `generate-media` | `.claude/skills/generate-media/SKILL.md` | 调用 Gemini API 生成角色图/场景图/道具图/分镜图，同时在作品目录写入 generate_media.py 并执行 |
| `submit-anime-project` | `.claude/skills/submit-anime-project/SKILL.md` | 读取 `seedance_project_tasks.json`，展开 base64，批量提交到 Seedance API |
| `produce-mv` | `.claude/skills/produce-mv/SKILL.md` | 与 produce-anime 并行的 MV 流程，结构高度重复 |

### 1.2 当前 4 阶段工作流

```
阶段1 produce-anime(步1-6)     阶段2 generate-media        阶段3 produce-anime(步7)   阶段4 submit-anime-project
─────────────────────────────  ──────────────────────────  ─────────────────────────  ──────────────────────────
项目初始化                       角色参考图                   读取 storyboard_config     读取 seedance_project_tasks.json
剧本编写                         场景四宫格图                 读取 dialogue.md           展开 referenceFiles → base64
角色/场景/道具设计                道具三视图                   读取 *_ref.png             批量 POST /api/tasks/push
EP01-EP25 dialogue.md           分镜9宫格PNG                 生成 seedance_project_     生成 submission_report.json
EP01-EP25 storyboard_config.json                            tasks.json（50条）
video_index.json
```

**关键问题**：阶段3（任务生成）被嵌入在 `produce-anime` 的第七步中，但它依赖阶段2的媒体文件，导致阶段1技能在运行时需要感知阶段2的完成状态。

---

## 二、当前设计最重要的 5 个问题

### 问题1：`produce-anime` 是 God Skill（最严重）

`produce-anime` 当前包含 7 个步骤，覆盖从项目初始化到 Seedance 任务生成的全部逻辑。这导致：

- 无法单独重新运行某一步（如只重新生成 EP15 的 storyboard）
- 阶段1和阶段3在同一技能中，但两者之间有强制依赖（必须先完成 generate-media）
- 技能文件过长（700+ 行），认知负担高
- 任何步骤的格式调整都需要在整个技能文件中搜索多处

### 问题2：阶段边界被破坏——Stage 3 的逻辑住在 Stage 1

`produce-anime` 第七步（生成 `seedance_project_tasks.json`）在逻辑上属于第三阶段，但实现上被写入了第一阶段的技能文件。结果是：

- 用户必须记住"在 generate-media 之后运行 produce-anime 的第七步"这一隐含的时序规则
- 没有任何机制防止用户在 generate-media 之前触发第七步
- `submit-anime-project` 的前置检查清单里没有校验 seedance_project_tasks.json 中的 referenceFiles 是否真实存在

### 问题3：`produce-anime` 和 `produce-mv` 有 80% 重复代码

两技能共享以下完全相同的逻辑：
- 9宫格分镜格式（grid_number, time_start, time_end, camera, characters, atmosphere, sfx, ai_image_prompt）
- `ai_image_prompt` 注入 visual_style.prompt_suffix 的规则
- prompt 标准排除指令（115字的固定中英文文本）
- `referenceFiles` 相对路径格式
- `(@文件名)` 引用语法规则
- Seedance 任务 JSON 格式

任何对核心格式的修改（如增加一个字段）都需要同步修改两处，且容易遗漏。

### 问题4：没有正式的 Artifact Contract（产物契约）

当前 `storyboard_config.json`、`seedance_project_tasks.json`、`video_index.json` 的格式只通过 SKILL.md 中的示例隐式约定，没有正式的 schema。这导致：

- 无法用工具校验某集的 storyboard_config.json 是否合法
- 上下游技能对字段名的理解可能出现偏差（如 `referenceFiles` 是相对路径字符串还是对象数组在两个技能中有歧义）
- 新增字段时不知道哪些是必填、哪些是可选
- 检查清单只能靠人工 tick，无法自动验证

### 问题5：配置路径硬编码为环境特定路径

`generate-media` 和 `produce-mv` 中多处出现 `/data/dongman/` 的绝对路径，与实际项目根目录（`/Users/bruce/project/Micro-Drama-Skills/`）不符。这使得：

- 新环境首次运行时必然报错
- `api_keys.json` 的读取路径在不同技能中描述不一致
- 技能难以移植或共享给他人使用

---

## 三、拆分建议

### 3.1 推荐的技能拆分清单

| 新技能名 | 对应当前来源 | 职责 | 阶段 |
|---------|-------------|------|------|
| `produce-drama` | produce-anime 步1-6 | 项目初始化、剧本、角色/场景/道具设计、25集内容生成、索引 | Stage 1 |
| `generate-media` | generate-media（保留，优化） | 调用 Gemini API 生成所有参考图 + 分镜图 | Stage 2 |
| `assemble-tasks` | produce-anime 步7 + produce-mv 步7 | 读取 storyboard configs + 媒体文件，组装 seedance_project_tasks.json | Stage 3（新建） |
| `submit-project` | submit-anime-project（重命名） | 读取任务文件，展开 base64，批量提交 | Stage 4 |
| `produce-mv` | produce-mv（精简） | MV专有逻辑（歌词同步、SEG结构、双风格），复用 drama-base 契约 | Stage 1（MV变体） |

### 3.2 保留 vs 拆出决策矩阵

| 内容 | 当前位置 | 建议 | 理由 |
|------|---------|------|------|
| 项目初始化（步1） | produce-anime | 保留在 produce-drama | 是 Stage 1 的起点 |
| 剧本编写（步2） | produce-anime | 保留在 produce-drama | 强依赖项目元数据 |
| 角色/场景/道具设计（步3-3C） | produce-anime | 保留在 produce-drama | 是剧本的直接产物 |
| EP01-25 内容生成（步4-5） | produce-anime | 保留在 produce-drama | 是 Stage 1 主体 |
| 全局索引更新（步6） | produce-anime | 保留在 produce-drama | Stage 1 的完成信号 |
| **Seedance 任务生成（步7）** | **produce-anime** | **拆出为 assemble-tasks** | **属于 Stage 3，依赖 Stage 2** |
| generate_media.py 内联生成 | generate-media | 移到 scripts/ 目录独立维护 | 代码不应内嵌在技能文件中 |
| 9宫格格式定义 | produce-anime + produce-mv | 提取到 drama-base 契约文档 | 共享格式，应有唯一定义源 |
| 标准排除指令（固定文本） | produce-anime + produce-mv | 提取到 drama-base 契约文档 | 防止两处各自维护产生偏差 |
| prompt 构建规则 | produce-anime + produce-mv | 提取到 drama-base 契约文档 | assemble-tasks 需复用 |
| MV特有逻辑（music_sync, SEG结构） | produce-mv | 保留在 produce-mv | 无需共享 |

---

## 四、推荐的阶段模型（Stage Model）

```
┌─────────────────────────────────────────────────────────────────────┐
│  Stage 1: Pre-Production（前期制作）                                  │
│  技能: produce-drama  │  触发: "制作一部短剧"                          │
│                                                                      │
│  输入: 用户描述（类型/风格/视觉风格）                                    │
│  产出: full_script.md                                                │
│        character_bible.md / scene_bible.md / prop_bible.md          │
│        EP01-EP25/dialogue.md × 25                                   │
│        EP01-EP25/storyboard_config.json × 25                        │
│        video_index.json                                              │
│        metadata.json                                                 │
│        projects/index.json（更新）                                    │
│  完成标志: video_index.json 存在且 status = "scripted"                │
└────────────────────────┬────────────────────────────────────────────┘
                         │ 前置检查: video_index.json 存在
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Stage 2: Asset Generation（素材生成）                                │
│  技能: generate-media  │  触发: "生成 DM-XXX 的图片"                   │
│                                                                      │
│  输入: character_bible.md, scene_bible.md, prop_bible.md            │
│        storyboard_config.json × 25                                  │
│  产出: characters/{角色名}_ref.png                                   │
│        scenes/{scene_id}_ref.png（四宫格合成图）                      │
│        props/{prop_id}_ref.png（三视图合成图）                        │
│        EP01-EP25/{video_id}_storyboard.png（9宫格分镜图）× 50        │
│        media_index.json                                              │
│  完成标志: media_index.json 存在且所有 50 张分镜图均有记录              │
└────────────────────────┬────────────────────────────────────────────┘
                         │ 前置检查: media_index.json 存在且分镜图完整
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Stage 3: Task Assembly（任务组装）                                   │
│  技能: assemble-tasks（新）│  触发: "组装 DM-XXX 的提交任务"            │
│                                                                      │
│  输入: storyboard_config.json × 25                                  │
│        dialogue.md × 25                                             │
│        *_ref.png（角色/场景/道具）                                    │
│        *_storyboard.png × 50                                        │
│  验证: 所有 referenceFiles 中的文件路径真实存在                         │
│  产出: seedance_project_tasks.json（50条，含完整 prompt + 相对路径）   │
│  完成标志: seedance_project_tasks.json 存在且 total_tasks = 50        │
└────────────────────────┬────────────────────────────────────────────┘
                         │ 前置检查: seedance_project_tasks.json 存在
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Stage 4: Submission（提交）                                          │
│  技能: submit-project  │  触发: "提交 DM-XXX 到 Seedance"             │
│                                                                      │
│  输入: seedance_project_tasks.json                                   │
│  处理: referenceFiles 相对路径 → base64 展开                          │
│  产出: submission_report.json                                        │
│  完成标志: submission_report.json 存在且 failed_tasks = 0            │
└─────────────────────────────────────────────────────────────────────┘
```

### 阶段状态机（对应 video_index.json 中的 status 字段）

```
scripted → media_generated → tasks_assembled → submitted → completed
   ↑                ↑                ↑               ↑
Stage 1结束     Stage 2结束      Stage 3结束     Stage 4结束
```

---

## 五、推荐的 Artifact Contracts（产物契约）清单

### Contract 1：`storyboard_config.json`

**路径**：`episodes/EPxx/storyboard_config.json`
**适用技能**：produce-drama（写）、generate-media（读）、assemble-tasks（读）

```
必填字段（顶层）:
  video_id_prefix: string          # 如 "DM-001-EP01"
  episode: integer                 # 1-25
  episode_title: string
  total_duration_seconds: 30
  subtitle: false                  # 永远为 false
  visual_style: VisualStyleObject  # 来自 visual_styles.json
  synopsis: string
  emotion_tone: string
  connection: { from_previous, to_next }
  part_a: PartObject
  part_b: PartObject

PartObject 必填字段:
  video_id: string                 # 如 "DM-001-EP01-A"
  label: "上" | "下"
  time_range: string
  duration_seconds: 15
  scene_refs: string[]             # scene_id 列表
  prop_refs: string[]              # prop_id 列表
  atmosphere: AtmosphereObject
  video_prompt: string             # 英文
  storyboard_9grid: GridItem[9]    # 固定9条

GridItem 必填字段:
  grid_number: 1-9
  time_start: number
  time_end: number
  scene_description: string
  camera: { type, movement, angle }
  characters: CharacterInFrame[]
  dialogue: { speaker, text, emotion }
  atmosphere: string
  sfx: string
  ai_image_prompt: string          # 英文，不含 visual_style.prompt_suffix
```

### Contract 2：`seedance_project_tasks.json`

**路径**：`{project_dir}/seedance_project_tasks.json`
**适用技能**：assemble-tasks（写）、submit-project（读）

```
必填字段（顶层）:
  project_id: string               # 如 "DM-001"
  project_name: string
  total_tasks: 50                  # 25集 × 2 = 50
  created_date: string             # ISO date
  tasks: TaskItem[50]

TaskItem 必填字段:
  prompt: string                   # 完整 prompt，含标准排除指令
  description: string
  modelConfig: ModelConfigObject
  referenceFiles: string[]         # 相对路径数组（提交时由 submit-project 展开为 base64）
  realSubmit: boolean              # 默认 false
  priority: integer
  tags: string[]                   # 至少包含 [project_id, EPxx, "A"|"B"]

ModelConfigObject 默认值:
  model: "Seedance 2.0 Fast"
  referenceMode: "全能参考"
  aspectRatio: "16:9"
  duration: "15s"
```

**关键澄清**：`referenceFiles` 在 `seedance_project_tasks.json` 中**始终是相对路径字符串数组**，由 `submit-project` 在提交时即时展开为 base64 对象数组。两种格式不应混用。

### Contract 3：`video_index.json`

**路径**：`{project_dir}/video_index.json`
**适用技能**：produce-drama（写）、assemble-tasks（读取阶段状态）

```
必填字段:
  project_id: string
  project_name: string
  total_episodes: 25
  created_date: string
  status: "scripted" | "media_generated" | "tasks_assembled" | "submitted" | "completed"
  videos: VideoEntry[50]

VideoEntry:
  episode: integer
  episode_title: string
  part_a: { video_id, label, duration, status, files }
  part_b: { video_id, label, duration, status, files }
```

### Contract 4：`media_index.json`

**路径**：`{project_dir}/media_index.json`
**适用技能**：generate-media（写）、assemble-tasks（前置校验读）

```
必填字段:
  project_id: string
  generated_date: string
  characters: CharacterMedia[]     # 每角色1张 *_ref.png
  scenes: SceneMedia[]             # 每场景1张四宫格合成图
  props: PropMedia[]               # 每道具1张三视图合成图
  storyboards: StoryboardMedia[]   # 50张分镜图（EP01-A, EP01-B, ..., EP25-B）

StoryboardMedia:
  video_id: string                 # 如 "DM-001-EP01-A"
  file: string                     # 相对路径 "episodes/EP01/DM-001-EP01-A_storyboard.png"
  exists: boolean
```

---

## 六、推荐的 Governance Skills（治理技能）清单

治理技能不直接执行制作任务，而是定义规范、共享规则和可复用逻辑。

| 治理文档 | 建议路径 | 内容 |
|---------|---------|------|
| `drama-base` | `docs/drama-base.md` | 9宫格标准格式、视频编号规则、文件命名规则、项目目录结构 |
| `prompt-rules` | `docs/prompt-rules.md` | 标准排除指令文本、`(@文件名)` 引用语法、prompt 构建顺序（头部声明→排除指令→集信息行→逐镜头）|
| `visual-style-spec` | `docs/visual-style-spec.md` | visual_styles.json 字段含义、注入规则（prompt_suffix 追加时机）、默认风格选取逻辑 |
| `api-config-spec` | `docs/api-config-spec.md` | api_keys.json 位置约定（相对 workspace 根目录）、环境变量优先级、gemini_image_model 合法值 |

**关键原则**：当 produce-drama、produce-mv 或 assemble-tasks 的行为需要修改时，首先检查是否应修改对应的治理文档，再由技能引用该文档的规范。

---

## 七、推荐的 Agents 清单

以下 Agent 可在 Claude Agent SDK 或 `.agent/` 目录下定义，用于自动化或并行执行特定任务。

| Agent 名 | 职责 | 触发条件 |
|---------|------|---------|
| `episode-writer` | 生成单集的 dialogue.md + storyboard_config.json | produce-drama 的步4可并行分发给多个此 agent 处理 |
| `asset-validator` | 校验所有 referenceFiles 路径是否存在，生成缺失清单 | assemble-tasks 前自动执行 |
| `media-retry` | 识别 media_index.json 中 `exists: false` 的条目，重试 Gemini API 调用 | generate-media 失败后的 recovery agent |
| `task-inspector` | 读取 seedance_project_tasks.json，检查 prompt 格式合规性（含排除指令、@ref 格式、镜头数） | assemble-tasks 完成后的 QA agent |

---

## 八、下一步实施建议（MVP 最小可落地重构范围）

### MVP 目标

在不修改现有 skill 的前提下，通过新增文档和脚本，消除问题1（God Skill）和问题2（阶段边界破坏），同时为问题3（重复代码）建立共享基础。

### MVP 三步走

#### Step 1：提取 `assemble-tasks` 技能（解决问题1+2）

- **新增** `.claude/skills/assemble-tasks/SKILL.md`
- 内容：从 produce-anime 步7 提取任务生成逻辑
- 关键新增：**前置校验**——检查所有 referenceFiles 中的文件是否存在，不存在则报错而非静默跳过
- produce-anime 步7 的内容可在 `produce-anime/SKILL.md` 中标记为 `(Deprecated: 使用 assemble-tasks 技能代替)`，但不删除（保持向后兼容）
- **验收标准**：用户可以独立运行 "组装 DM-001 的提交任务" 而无需重新运行 produce-anime

#### Step 2：新增产物契约文档（解决问题4）

- **新增** `docs/drama-base.md`（本文件第五节的契约定义）
- **新增** `schemas/storyboard_config.schema.json`（JSON Schema 格式）
- **新增** `schemas/seedance_tasks.schema.json`（JSON Schema 格式）
- `assemble-tasks` 技能在前置校验中引用这些 schema 进行结构验证
- **验收标准**：可以用 `python -m jsonschema` 或任意 JSON Schema 工具验证任意一集的 storyboard_config.json

#### Step 3：新增 `prompt-rules` 治理文档（解决问题3的第一步）

- **新增** `docs/prompt-rules.md`
- 内容：标准排除指令文本（唯一定义）、prompt 构建顺序、`(@文件名)` 语法说明
- `assemble-tasks` 和 `produce-mv` 步7均引用此文档，不再各自定义
- **验收标准**：如需修改标准排除指令文本，只需改 docs/prompt-rules.md 一处

### MVP 不包含的内容（留待后续迭代）

- 将 generate_media.py 从 SKILL.md 中提取到独立 scripts/ 目录（技术债，影响可维护性但不影响功能）
- 将 produce-mv 的共享逻辑与 produce-drama 统一（需要较大重构，建议在 Step 1-3 稳定后进行）
- 配置路径规范化（修改 api_keys.json 的读取路径约定）

### 实施顺序与依赖关系

```
Step 1 (assemble-tasks)
    └── 依赖: Step 2 的 schemas 目录存在（可以先建目录，schema 内容后填）

Step 2 (schemas)
    └── 独立，可与 Step 1 并行

Step 3 (prompt-rules)
    └── 依赖: Step 1 完成后才能验证 assemble-tasks 是否正确引用
```

---

## 附录A：当前技能问题速查表

| 问题 | 严重度 | 影响范围 | MVP 中解决 |
|------|--------|---------|-----------|
| produce-anime 是 God Skill | 🔴 高 | 所有 DM 项目 | ✅ Step 1 |
| Stage 3 嵌入 Stage 1 | 🔴 高 | 所有 DM 项目 | ✅ Step 1 |
| DM/MV 逻辑 80% 重复 | 🟡 中 | produce-mv 可维护性 | 🔶 Step 3（部分） |
| 无 Artifact Contract | 🟡 中 | 所有阶段 | ✅ Step 2 |
| 配置路径硬编码 | 🟡 中 | generate-media, produce-mv | ❌ 留后续 |
| generate_media.py 内嵌在 SKILL.md | 🟢 低 | 可维护性 | ❌ 留后续 |

---

## 附录B：文件路径变更对照表（MVP 后）

| 操作 | 当前路径/方式 | MVP 后路径/方式 |
|------|-------------|----------------|
| Seedance 任务生成 | produce-anime 第七步 | assemble-tasks 技能 |
| 排除指令文本 | produce-anime 内 + produce-mv 内（各自维护） | docs/prompt-rules.md（单一来源） |
| storyboard 格式定义 | produce-anime SKILL.md 示例 | schemas/storyboard_config.schema.json |
| 任务格式定义 | produce-anime SKILL.md + submit-anime-project SKILL.md | schemas/seedance_tasks.schema.json |
| 媒体生成脚本 | generate-media 内联生成到项目目录 | （后续迭代）scripts/generate_media.py |
