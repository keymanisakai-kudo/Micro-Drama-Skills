# Artifact Contracts — 短剧生产体系

> **版本**：v1.0
> **日期**：2026-03-15
> **配套文档**：`docs/stage-model.md`、`docs/skill-refactor-plan.md`
> **范围**：25 集 / 30 秒 / Part A-B / 9 宫格，DM-XXX 系列

---

## 索引

| ID | Artifact | 路径 | 格式 | Producer | Consumer |
|----|---------|------|------|----------|----------|
| AC-001 | `metadata.json` | `{project_dir}/metadata.json` | JSON | produce-anime | generate-media, assemble-tasks |
| AC-002 | `full_script.md` | `{project_dir}/script/full_script.md` | Markdown | produce-anime | produce-anime（写集内容时引用） |
| AC-003 | `character_bible.md` | `{project_dir}/characters/character_bible.md` | Markdown | produce-anime | generate-media, assemble-tasks |
| AC-004 | `scene_bible.md` | `{project_dir}/scenes/scene_bible.md` | Markdown | produce-anime | generate-media, assemble-tasks |
| AC-005 | `prop_bible.md` | `{project_dir}/props/prop_bible.md` | Markdown | produce-anime | generate-media, assemble-tasks |
| AC-006 | `dialogue.md` | `{project_dir}/episodes/EPxx/dialogue.md` | Markdown | produce-anime | assemble-tasks |
| AC-007 | `storyboard_config.json` | `{project_dir}/episodes/EPxx/storyboard_config.json` | JSON | produce-anime | generate-media, assemble-tasks |
| AC-008 | `video_index.json` | `{project_dir}/video_index.json` | JSON | produce-anime, generate-media, assemble-tasks, submit-project | 所有 pipeline 技能（读取 status） |
| AC-009 | `seedance_project_tasks.json` | `{project_dir}/seedance_project_tasks.json` | JSON | assemble-tasks | submit-project |

---

## AC-001: `metadata.json`

### 1. Artifact Name

`metadata.json` — 作品元数据

### 2. Purpose

记录一部作品的基础身份和配置信息。是所有下游技能获取 `project_id`、`visual_style` 等全局配置的唯一来源。

### 3. Required Fields

```
project_id          : string       # 格式: "DM-XXX"，XXX 为三位零填充数字
project_name        : string       # 中文作品名称，非空
directory           : string       # 相对于 projects/ 的目录名，格式: "DM-XXX_拼音缩写"
total_episodes      : integer      # 固定值: 25
episode_duration_seconds : integer # 固定值: 30
created_date        : string       # ISO 8601 日期: "YYYY-MM-DD"
visual_style        : object       # 来自 .config/visual_styles.json 的完整风格对象
  └─ style_id       : integer
  └─ style_name     : string
  └─ camera         : string
  └─ film_stock     : string
  └─ filter         : string
  └─ focal_length   : string
  └─ aperture       : string
  └─ prompt_suffix  : string       # 追加到 ai_image_prompt 末尾的风格描述，英文
```

### 4. Optional Fields

```
project_name_en     : string       # 英文作品名称
genre               : string | string[]  # 题材类型，可为字符串或数组
style               : string       # 叙事风格描述
theme               : string       # 世界观描述
core_theme          : string       # 一句话核心主题
target_audience     : string       # 目标受众
updated_date        : string       # ISO 8601 日期
video_count         : integer      # 等于 total_episodes × 2
total_duration_seconds : integer   # 等于 total_episodes × episode_duration_seconds
status              : string       # 历史兼容字段，部分旧项目存在，不作为状态判断依据
                                   # 项目阶段状态的唯一来源是 video_index.json.status（见 AC-008）
```

### 5. Naming Rules

- 文件名固定为 `metadata.json`
- `project_id` 格式：`DM-XXX`（`XXX` 为三位数字，从 `001` 递增）
- `directory` 格式：`DM-XXX_拼音缩写`（拼音缩写由项目名拼音首字母组成，全小写）

### 6. Validation Rules

1. `project_id` 必须匹配正则 `^DM-\d{3}$`
2. `total_episodes` 必须等于 `25`
3. `episode_duration_seconds` 必须等于 `30`
4. `visual_style.prompt_suffix` 必须非空字符串
5. `created_date` 必须为合法 ISO 8601 日期格式
6. `directory` 必须与父目录实际目录名一致

### 7. Blocking Errors

| 错误 | 条件 |
|------|------|
| `[BLOCK] project_id 格式非法` | 不匹配 `^DM-\d{3}$` |
| `[BLOCK] visual_style 缺失` | `visual_style` 字段不存在或为 `null` |
| `[BLOCK] prompt_suffix 为空` | `visual_style.prompt_suffix` 为空字符串 |
| `[BLOCK] total_episodes 不为 25` | 值不等于 `25` |

### 8. Warning Issues

| 警告 | 条件 |
|------|------|
| `[WARN] 存在冗余 status 字段` | `metadata.json` 包含 `status` 字段（应以 `video_index.json.status` 为准，此字段无实际效力） |
| `[WARN] 缺少 visual_style_id` | `visual_style` 存在但 `style_id` 缺失 |
| `[WARN] directory 格式不规范` | `directory` 不匹配 `^DM-\d{3}_[a-z]+$` |

### 9. Producer Skill

`produce-anime`（步骤1：项目初始化时写入）

### 10. Consumer Skills

| 技能 | 用途 |
|------|------|
| `generate-media` | 读取 `project_id`、`visual_style` |
| `assemble-tasks` | 读取 `project_id`、`project_name`、`visual_style.prompt_suffix` |
| `submit-project` | 读取 `project_id`、`project_name` |

---

## AC-002: `full_script.md`

### 1. Artifact Name

`full_script.md` — 完整剧本

### 2. Purpose

作品的主叙事文档，定义 25 集的故事大纲、情感节奏和各集关键事件。是后续逐集内容生成的参考基础。

### 3. Required Sections

```
# 《{project_name}》完整剧本

## 作品信息
- 类型: string
- 风格: string
- 视觉风格: string        # 对应 visual_styles.json 的 style_name
- 目标受众: string
- 总时长: "25集 × 30秒 = 12分30秒"   # 固定文本
- 核心主题: string        # 一句话

## 世界观设定
[200-300 字正文]

## 故事大纲
[400-600 字正文，覆盖完整故事线]

## 各集概要
# 必须包含 EP01 到 EP25，共 25 条，每条格式:
### 第{N}集：{episode_title}
- 剧情概要: string        # 50 字以内
- 关键事件: list          # 列表
- 情感基调: string        # 如 "紧张、悬疑"
```

### 4. Optional Fields / Sections

```
## 人物关系图       # 文字描述角色关系网络
## 世界观补充       # 扩展设定
集概要中的"与上集衔接"/"为下集铺垫"字段
```

### 5. Naming Rules

- 文件名固定为 `full_script.md`
- 路径固定为 `{project_dir}/script/full_script.md`

### 6. Validation Rules

1. 文件必须包含 25 个 `### 第X集：` 标题（X 从 1 到 25）
2. 每个集概要必须包含 `剧情概要`、`关键事件`、`情感基调` 三个条目
3. `## 故事大纲` 段落必须存在且非空
4. `## 作品信息` 中的 `视觉风格` 必须与 `metadata.json.visual_style.style_name` 一致

### 7. Blocking Errors

| 错误 | 条件 |
|------|------|
| `[BLOCK] 集数不足` | `### 第X集：` 标题少于 25 个 |
| `[BLOCK] 故事大纲缺失` | `## 故事大纲` 段落不存在或内容少于 100 字 |

### 8. Warning Issues

| 警告 | 条件 |
|------|------|
| `[WARN] 集概要缺少情感基调` | 任意集缺少 `情感基调` 条目 |
| `[WARN] 视觉风格与 metadata.json 不一致` | `作品信息.视觉风格` ≠ `metadata.json.visual_style.style_name` |

### 9. Producer Skill

`produce-anime`（步骤2）

### 10. Consumer Skills

| 技能 | 用途 |
|------|------|
| `produce-anime` | 步骤4生成各集 `dialogue.md` 和 `storyboard_config.json` 时读取集概要 |

---

## AC-003: `character_bible.md`

### 1. Artifact Name

`character_bible.md` — 角色设定集

### 2. Purpose

定义全剧所有角色的视觉形象、性格、背景和 AI 绘图关键词。`AI绘图关键词（英文）` 是 `generate-media` 生成角色参考图的核心输入。

### 3. Required Sections

```
# 角色设定集

## 主要角色

### 角色{N}：{character_name}
- 全名: string
- 年龄: string            # 如 "30岁"
- 性别: string
- 身高/体重: string        # 如 "178cm / 70kg"
- 外貌特征:
  - 发型/发色: string
  - 瞳色: string
  - 体型: string
  - 标志性特征: string
- 服装设计:
  - 日常服装: string
- 性格特点: string
- 口头禅: string
- 背景故事: string        # 100 字以内
- 角色弧光: string        # 描述 25 集中的成长变化
- AI绘图关键词（英文）: string  # 英文，详细描述外貌和服装，不含 visual_style.prompt_suffix

## 次要角色    # 可选，若有次要角色则按同样格式列出
```

### 4. Optional Fields

```
特殊服装 / 战斗服装
角色关系图          # 文字描述各角色间关系网络
```

### 5. Naming Rules

- 文件名固定为 `character_bible.md`
- 路径固定为 `{project_dir}/characters/character_bible.md`
- 角色参考图命名：`{character_name}_ref.png`（`character_name` 为 `### 角色N：` 后的中文名）

### 6. Validation Rules

1. 每个角色必须包含 `AI绘图关键词（英文）` 字段且值为英文非空字符串
2. `AI绘图关键词（英文）` 必须包含外貌描述（身高、发型、服装中至少两项）
3. `AI绘图关键词（英文）` 不得包含 `visual_style.prompt_suffix` 中的风格词（如 `shot on`）
4. 必须至少包含一个主要角色

### 7. Blocking Errors

| 错误 | 条件 |
|------|------|
| `[BLOCK] 角色缺少 AI绘图关键词` | 任意角色的 `AI绘图关键词（英文）` 字段不存在或为空 |
| `[BLOCK] AI关键词非英文` | `AI绘图关键词（英文）` 包含中文字符超过 5 个 |
| `[BLOCK] 无主要角色` | `## 主要角色` 段落不存在或无任何角色条目 |

### 8. Warning Issues

| 警告 | 条件 |
|------|------|
| `[WARN] AI关键词过短` | 任意角色的 `AI绘图关键词（英文）` 少于 30 个英文单词 |
| `[WARN] 缺少角色弧光` | 任意主要角色缺少 `角色弧光` 字段 |

### 9. Producer Skill

`produce-anime`（步骤3）

### 10. Consumer Skills

| 技能 | 用途 |
|------|------|
| `generate-media` | 读取每个角色的 `AI绘图关键词（英文）` 生成 `{character_name}_ref.png` |
| `assemble-tasks` | 构建 `characters/ref_index.json`，在 prompt 中生成 `(@{character_name}_ref.png)` 引用 |

---

## AC-004: `scene_bible.md`

### 1. Artifact Name

`scene_bible.md` — 场景设定集

### 2. Purpose

定义全剧反复出现的核心场景的视觉规格和 AI 绘图关键词。`generate-media` 据此生成四宫格场景参考图。只收录出现 3 集及以上的场景。

### 3. Required Sections

```
# 场景设定集

## 场景{N}：{scene_name}
- 场景ID: string          # 格式: "scene_XX"，XX 为两位零填充数字
- 场景描述: string        # 50-100 字，描述物理空间、装饰、氛围
- 出现集数: string        # 如 "EP01, EP02, EP05"
- 关键视觉元素: string    # 逗号分隔的标志性物件列表
- AI绘图关键词（英文）: string  # 英文，包含空间布局、光影、陈设风格
```

> 若全剧无可收录场景（所有场景均只出现 1-2 集），则文件内容为空（保留文件头 `# 场景设定集`）。

### 4. Optional Fields

```
场景的改造前/改造后描述   # 若场景在剧中发生视觉变化
```

### 5. Naming Rules

- 文件名固定为 `scene_bible.md`
- 路径固定为 `{project_dir}/scenes/scene_bible.md`
- `scene_id` 格式：`scene_XX`（`XX` 为两位零填充数字，从 `01` 递增）
- 场景参考图命名：`{scene_id}_ref.png`（如 `scene_01_ref.png`）

### 6. Validation Rules

1. 每个场景的 `场景ID` 必须唯一且匹配 `^scene_\d{2}$`
2. `AI绘图关键词（英文）` 必须为英文非空字符串
3. `出现集数` 中列出的集数不得少于 3 个（否则不应收录该场景）
4. `scene_id` 必须与 `storyboard_config.json` 中 `scene_refs` 数组的引用值一致

### 7. Blocking Errors

| 错误 | 条件 |
|------|------|
| `[BLOCK] scene_id 格式非法` | 不匹配 `^scene_\d{2}$` |
| `[BLOCK] scene_id 重复` | 两个场景使用相同的 `scene_id` |
| `[BLOCK] AI关键词缺失` | 任意场景的 `AI绘图关键词（英文）` 不存在或为空 |

### 8. Warning Issues

| 警告 | 条件 |
|------|------|
| `[WARN] 场景出现集数不足 3 集` | `出现集数` 中列出集数少于 3 |
| `[WARN] AI关键词过短` | 少于 20 个英文单词 |
| `[WARN] scene_id 被 storyboard_config 引用但在 scene_bible 中不存在` | `scene_refs` 中有不在 `scene_bible.md` 中的 `scene_id` |

### 9. Producer Skill

`produce-anime`（步骤3B）

### 10. Consumer Skills

| 技能 | 用途 |
|------|------|
| `generate-media` | 读取 `AI绘图关键词（英文）` 生成 `{scene_id}_ref.png` 四宫格合成图 |
| `assemble-tasks` | 构建 `scenes/ref_index.json`，在 prompt 中内联 `(@{scene_id}_ref.png)` 引用 |

---

## AC-005: `prop_bible.md`

### 1. Artifact Name

`prop_bible.md` — 道具设定集

### 2. Purpose

定义全剧具有剧情意义的核心道具的视觉规格和 AI 绘图关键词。`generate-media` 据此生成三视图合成图。只收录剧情推动性或象征性道具。

### 3. Required Sections

```
# 道具设定集

## 道具{N}：{prop_name}
- 道具ID: string          # 格式: "prop_XX"，XX 为两位零填充数字
- 道具描述: string        # 30-50 字，描述外观、材质、尺寸
- 出现集数: string        # 如 "EP10, EP12, EP25"
- 剧情意义: string        # 此道具在剧中的象征/功能意义
- AI绘图关键词（英文）: string  # 英文，包含材质、颜色、形状、细节
```

> 若全剧无核心道具，则文件内容为空（保留文件头 `# 道具设定集`）。**空文件是合法状态，不触发任何错误。**

### 4. Optional Fields

无

### 5. Naming Rules

- 文件名固定为 `prop_bible.md`
- 路径固定为 `{project_dir}/props/prop_bible.md`
- `prop_id` 格式：`prop_XX`（`XX` 为两位零填充数字，从 `01` 递增）
- 道具参考图命名：`{prop_id}_ref.png`（如 `prop_01_ref.png`）

### 6. Validation Rules

1. 每个道具的 `道具ID` 必须唯一且匹配 `^prop_\d{2}$`
2. `AI绘图关键词（英文）` 必须为英文非空字符串（若道具存在）
3. `prop_id` 必须与 `storyboard_config.json` 中 `prop_refs` 数组的引用值一致

### 7. Blocking Errors

| 错误 | 条件 |
|------|------|
| `[BLOCK] prop_id 格式非法` | 不匹配 `^prop_\d{2}$` |
| `[BLOCK] prop_id 重复` | 两个道具使用相同的 `prop_id` |
| `[BLOCK] AI关键词缺失（道具存在时）` | 道具存在但 `AI绘图关键词（英文）` 为空 |

### 8. Warning Issues

| 警告 | 条件 |
|------|------|
| `[WARN] prop_id 被 storyboard_config 引用但在 prop_bible 中不存在` | `prop_refs` 中有不在 `prop_bible.md` 中的 `prop_id` |
| `[WARN] AI关键词过短` | 少于 15 个英文单词 |

### 9. Producer Skill

`produce-anime`（步骤3C）

### 10. Consumer Skills

| 技能 | 用途 |
|------|------|
| `generate-media` | 读取 `AI绘图关键词（英文）` 生成 `{prop_id}_ref.png` 三视图合成图 |
| `assemble-tasks` | 构建 `props/ref_index.json`，在 prompt 中内联 `(@{prop_id}_ref.png)` 引用 |

---

## AC-006: `dialogue.md`

### 1. Artifact Name

`dialogue.md` — 集对话脚本

### 2. Purpose

记录单集 Part A 和 Part B 的全部对话台词，包含台词内容、说话者、时间点和情感。是 `assemble-tasks` 构建 `镜头N` 描述中台词行的输入来源。

### 3. Required Sections

```
# 第{episode}集：{episode_title} 对话脚本

## 注意：本集视频不带字幕，对话通过配音传达

## 上半部分（Part A：00:00-00:15）
## 视频编号：{project_id}-EP{XX}-A

| 序号 | 时间 | 角色 | 对话内容（中文） | 语气/情感 | 备注 |
|------|------|------|----------------|----------|------|
| {N} | {MM:SS} | {speaker} | 「{dialogue}」 | {emotion} | {note} |

## 下半部分（Part B：00:15-00:30）
## 视频编号：{project_id}-EP{XX}-B

| 序号 | 时间 | 角色 | 对话内容（中文） | 语气/情感 | 备注 |
|------|------|------|----------------|----------|------|
| {N} | {MM:SS} | {speaker} | 「{dialogue}」 | {emotion} | {note} |
```

### 4. Optional Fields

```
表格行中的「备注」列可为空（"—"）
单集可以零台词（全旁白或无对话）
旁白行角色列写"旁白"
```

### 5. Naming Rules

- 文件名固定为 `dialogue.md`
- 路径格式：`{project_dir}/episodes/EP{XX}/dialogue.md`
- `XX` 为两位零填充数字，如 `EP01`、`EP25`

### 6. Validation Rules

1. 文件必须包含 `## 上半部分` 和 `## 下半部分` 两个段落
2. 视频编号注释格式必须为 `{project_id}-EP{XX}-A` / `-B`
3. `对话内容（中文）` 列必须为中文（旁白台词亦需中文）
4. 时间格式必须为 `MM:SS`，Part A 范围 `00:00-00:15`，Part B 范围 `00:15-00:30`
5. 每集 Part A 和 Part B 合计对话行数建议 3-6 句（超出时触发警告）

### 7. Blocking Errors

| 错误 | 条件 |
|------|------|
| `[BLOCK] 缺少上半部分或下半部分段落` | 文件不包含 `上半部分` 或 `下半部分` 标题 |
| `[BLOCK] 视频编号格式错误` | 视频编号不匹配 `{project_id}-EP\d{2}-[AB]` |

### 8. Warning Issues

| 警告 | 条件 |
|------|------|
| `[WARN] 对话含英文` | 表格中出现英文台词（仅旁白引用英文词汇除外） |
| `[WARN] 单句超过 20 字` | 任意台词超过 20 个中文字符 |
| `[WARN] 单集对话行数超过 8 句` | Part A + Part B 合计对话行数超过 8 |

### 9. Producer Skill

`produce-anime`（步骤4.1）

### 10. Consumer Skills

| 技能 | 用途 |
|------|------|
| `assemble-tasks` | 读取每条台词，在 `镜头N` 描述中生成 `(@角色名_ref.png){角色名}说："{text}"（{emotion}）` |

---

## AC-007: `storyboard_config.json`

### 1. Artifact Name

`storyboard_config.json` — 集故事板配置

### 2. Purpose

定义单集的完整 9 宫格分镜结构（Part A + Part B），是 `generate-media` 生成分镜 PNG 和 `assemble-tasks` 构建 Seedance prompt 的核心输入。

### 3. Required Fields

**顶层字段：**

```
video_id_prefix      : string       # 格式: "{project_id}-EP{XX}"，如 "DM-003-EP01"
episode              : integer      # 1-25
episode_title        : string       # 中文集标题
total_duration_seconds : integer    # 固定值: 30
subtitle             : boolean      # 固定值: false（永远不得为 true）
visual_style         : object       # 完整风格对象，与 metadata.json.visual_style 一致
  └─ style_id        : integer
  └─ style_name      : string
  └─ camera          : string
  └─ film_stock      : string
  └─ filter          : string
  └─ focal_length    : string
  └─ aperture        : string
  └─ prompt_suffix   : string
synopsis             : string       # 本集剧情概要，100 字以内
emotion_tone         : string       # 情感基调，如 "压抑、沉重、悬念"
connection           : object
  └─ from_previous   : string       # 与上集的衔接描述
  └─ to_next         : string       # 为下集的铺垫描述
part_a               : PartObject
part_b               : PartObject
```

**PartObject 必填字段：**

```
video_id             : string       # 格式: "{video_id_prefix}-A" 或 "-B"
label                : string       # "上" 或 "下"
time_range           : string       # Part A: "00:00-00:15"，Part B: "00:15-00:30"
duration_seconds     : integer      # 固定值: 15
scene_refs           : string[]     # 本 Part 引用的 scene_id 列表，可为空数组
prop_refs            : string[]     # 本 Part 引用的 prop_id 列表，可为空数组
atmosphere           : object
  └─ overall_mood    : string
  └─ color_palette   : string[]     # HEX 颜色数组，建议 2-4 个
  └─ lighting        : string
  └─ weather         : string
video_prompt         : string       # 英文，供 AI 视频生成的整体描述，不含 prompt_suffix
storyboard_9grid     : GridItem[9]  # 固定 9 条，grid_number 从 1 到 9 连续
```

**GridItem 必填字段：**

```
grid_number          : integer      # 1-9，连续不重复
time_start           : number       # 单位秒，精度 0.01
time_end             : number       # 单位秒，精度 0.01
scene_description    : string       # 50 字以内的画面描述
camera               : object
  └─ type            : string       # "远景" | "中景" | "近景" | "特写"
  └─ movement        : string       # "固定" | "推" | "拉" | "摇" | "移" | "跟" | "缓慢推进" 等
  └─ angle           : string       # "平视" | "俯视" | "仰视"
characters           : CharacterInFrame[]   # 本格出场角色，可为空数组
dialogue             : object
  └─ speaker         : string | null
  └─ text            : string | null
  └─ emotion         : string | null
atmosphere           : string       # 本格氛围描述
sfx                  : string       # 音效描述
ai_image_prompt      : string       # 英文，不含 visual_style.prompt_suffix（由 assemble-tasks 追加）
```

**CharacterInFrame 必填字段：**

```
name                 : string       # 必须与 character_bible.md 中的角色名一致
action               : string
expression           : string
position             : string       # "左" | "中" | "右" | 其他位置描述
```

### 4. Optional Fields

```
fps                  : integer      # 建议值: 24
resolution           : string       # 建议值: "1920x1080"
aspect_ratio         : string       # 建议值: "16:9"
style                : string       # 如 "short_drama"
bgm                  : object       # 背景音乐描述
  └─ description     : string
  └─ mood            : string
```

### 5. Naming Rules

- 文件名固定为 `storyboard_config.json`
- 路径格式：`{project_dir}/episodes/EP{XX}/storyboard_config.json`
- `video_id_prefix` 格式：`{project_id}-EP{XX}`
- `part_a.video_id` 格式：`{video_id_prefix}-A`
- `part_b.video_id` 格式：`{video_id_prefix}-B`
- 生成的分镜图命名：`{video_id}_storyboard.png`（如 `DM-003-EP01-A_storyboard.png`）

### 6. Validation Rules

1. `subtitle` 必须为 `false`
2. `total_duration_seconds` 必须为 `30`
3. `part_a.duration_seconds` 和 `part_b.duration_seconds` 均必须为 `15`
4. `part_a.storyboard_9grid` 和 `part_b.storyboard_9grid` 均必须恰好有 9 条
5. 每个 Part 的 `grid_number` 必须从 1 到 9 连续且不重复
6. `ai_image_prompt` 不得包含 `visual_style.prompt_suffix` 中的词（如 `shot on`）
7. `scene_refs` 中的每个 `scene_id` 必须存在于 `scene_bible.md` 中（或 `scene_bible.md` 为空）
8. `prop_refs` 中的每个 `prop_id` 必须存在于 `prop_bible.md` 中（或 `prop_bible.md` 为空）
9. `part_a.time_range` 必须为 `"00:00-00:15"`，`part_b.time_range` 必须为 `"00:15-00:30"`
10. 各 Grid 的 `time_start`/`time_end` 应从 0.0 到 15.0 连续覆盖（相邻格的 time_end ≈ 下一格的 time_start）
11. `characters[].name` 必须在 `character_bible.md` 中有对应角色

### 7. Blocking Errors

| 错误 | 条件 |
|------|------|
| `[BLOCK] subtitle 为 true` | `subtitle` 字段值不为 `false` |
| `[BLOCK] storyboard_9grid 数量不为 9` | 任一 Part 的 `storyboard_9grid` 长度 ≠ 9 |
| `[BLOCK] grid_number 不连续` | 任一 Part 的 `grid_number` 不是 1-9 的完整序列 |
| `[BLOCK] video_id 格式错误` | `part_a.video_id` 或 `part_b.video_id` 不匹配 `{project_id}-EP\d{2}-[AB]` |
| `[BLOCK] visual_style 缺失` | `visual_style` 不存在或 `prompt_suffix` 为空 |

### 8. Warning Issues

| 警告 | 条件 |
|------|------|
| `[WARN] ai_image_prompt 含 prompt_suffix 词汇` | `ai_image_prompt` 中包含 `shot on`、`film grain` 等风格词 |
| `[WARN] scene_ref 不在 scene_bible 中` | `scene_refs` 引用的 scene_id 在 `scene_bible.md` 中找不到 |
| `[WARN] prop_ref 不在 prop_bible 中` | `prop_refs` 引用的 prop_id 在 `prop_bible.md` 中找不到 |
| `[WARN] 角色名不在 character_bible 中` | `characters[].name` 在 `character_bible.md` 中没有对应条目 |

### 9. Producer Skill

`produce-anime`（步骤4.2）

### 10. Consumer Skills

| 技能 | 用途 |
|------|------|
| `generate-media` | 读取 `ai_image_prompt` + `visual_style.prompt_suffix` 生成 `{video_id}_storyboard.png` 九宫格 |
| `assemble-tasks` | 读取 `storyboard_9grid`、`synopsis`、`atmosphere`、`scene_refs`、`prop_refs` 构建 Seedance prompt |

---

## AC-008: `video_index.json`

### 1. Artifact Name

`video_index.json` — 视频编号管理索引 / 项目状态机

### 2. Purpose

两个职责合一：
1. **状态机载体**：根字段 `status` 是整个生产流程的**唯一可信状态源（single source of truth）**，所有 Gate 条件均读取此字段
2. **视频 ID 注册表**：记录全剧 50 条视频的编号、状态和关联文件路径

### 3. Required Fields

**顶层字段：**

```
project_id           : string       # 格式: "DM-XXX"
project_name         : string
total_episodes       : integer      # 固定值: 25
created_date         : string       # ISO 8601 日期
status               : string       # 状态机字段，见合法值列表
videos               : VideoEntry[] # 长度恰好为 25（每集一条），或 50（每 Part 一条，见 Note）
```

**`status` 合法值（只能单向递进）：**

```
"scripted"           → Stage 1 完成（produce-anime 写入）
"media_pending"      → 媒体待生成，可选中间状态（produce-anime 可选写入）
"media_ready"        → Stage 2 完成（generate-media 写入）
"tasks_assembled"    → Stage 3 组装完成但未验证（assemble-tasks 写入）
"ready_to_submit"    → Stage 3 验证通过（assemble-tasks 在路径验证后写入）
"submitted"          → Stage 4 完成（submit-project 写入）
```

**VideoEntry 字段（推荐格式，每集一条）：**

```
episode              : integer      # 1-25
episode_title        : string
part_a               : PartEntry
part_b               : PartEntry

PartEntry:
  video_id           : string       # 格式: "{project_id}-EP{XX}-A" 或 "-B"
  label              : string       # "上" 或 "下"
  duration           : integer      # 固定值: 15
  status             : string       # 本视频生产状态，如 "script_ready"、"media_ready"、"submitted"
  files              : object
    └─ dialogue      : string       # 相对路径: "episodes/EP{XX}/dialogue.md"
    └─ storyboard_config : string   # 相对路径: "episodes/EP{XX}/storyboard_config.json"
```

> **Note（兼容格式）**：现有项目（如 DM-003）`videos` 数组为 50 条的扁平格式：
> `{ "video_id": "DM-003-EP01-A", "episode": 1, "part": "A", "title": "...", "status": "pending" }`
> 两种格式均可接受，但根字段 `status` 不可缺失。

### 4. Optional Fields

```
total_videos         : integer      # 等于 total_episodes × 2 = 50
video_duration       : string       # 如 "15s"
editing_guide        : object       # 编辑参数汇总（仅供参考，不被工具读取）
```

### 5. Naming Rules

- 文件名固定为 `video_index.json`
- 路径固定为 `{project_dir}/video_index.json`
- `video_id` 格式：`{project_id}-EP{XX}-[A|B]`（`XX` 为两位零填充数字）

### 6. Validation Rules

1. 根 `status` 必须是六个合法值之一
2. `status` 只允许单向前进（不允许回退，仅 `ready_to_submit` → `tasks_assembled` 的重建例外）
3. `videos` 数组记录必须覆盖 EP01 到 EP25 的所有集（25 集或 50 个 Part）
4. `total_episodes` 必须为 `25`
5. 每条 `video_id` 必须匹配 `{project_id}-EP\d{2}-[AB]`，且在整个数组中唯一

### 7. Blocking Errors

| 错误 | 条件 | 触发技能 |
|------|------|---------|
| `[BLOCK] status 非法值` | `status` 不在合法值列表中 | 所有 pipeline 技能 |
| `[BLOCK] status 不满足前置要求` | `assemble-tasks` 需要 `media_ready`；`submit-project` 需要 `ready_to_submit` | 见 stage-model.md Gate 条件 |
| `[BLOCK] videos 集数不足` | 覆盖集数 < 25 | assemble-tasks |
| `[BLOCK] video_id 格式错误` | 不匹配命名规则 | assemble-tasks |

### 8. Warning Issues

| 警告 | 条件 |
|------|------|
| `[WARN] 缺少根 status 字段` | `status` 字段不存在（历史格式兼容问题） |
| `[WARN] metadata.json.status 与此文件不同步` | 两文件 `status` 值不一致 |

### 9. Producer Skill

| 技能 | 写入的 status 值 |
|------|----------------|
| `produce-anime` | `"scripted"`、`"media_pending"`（可选） |
| `generate-media` | `"media_ready"` |
| `assemble-tasks` | `"tasks_assembled"`、`"ready_to_submit"` |
| `submit-project` | `"submitted"` |

### 10. Consumer Skills

| 技能 | 用途 |
|------|------|
| `generate-media` | Gate 检查：读取 `status` 确认前置状态 |
| `assemble-tasks` | Gate 检查：`status` 必须为 `media_ready` |
| `submit-project` | Gate 检查：`status` 必须为 `ready_to_submit` |
| `validate-stage` | 读取 `status` 判断当前所处阶段 |

---

## AC-009: `seedance_project_tasks.json`

### 1. Artifact Name

`seedance_project_tasks.json` — 全剧 Seedance 提交任务集

### 2. Purpose

整合全剧 50 条视频的 Seedance 提交任务，每条任务包含完整 prompt 和参考文件的相对路径。是 `submit-project` 读取并提交到 Seedance API 的唯一任务源。

**关键约束**：`referenceFiles` 在本文件中**始终是相对路径字符串数组**，由 `submit-project` 在提交时实时读取磁盘文件并展开为 base64 对象数组。两种格式绝对不可混用。

### 3. Required Fields

**顶层字段：**

```
project_id           : string       # 格式: "DM-XXX"
project_name         : string
total_tasks          : integer      # 固定值: 50
created_date         : string       # ISO 8601 日期
tasks                : TaskItem[50] # 排列顺序: EP01-A, EP01-B, EP02-A, EP02-B, ..., EP25-A, EP25-B
```

**TaskItem 必填字段：**

```
prompt               : string       # 完整 Seedance prompt，见 Prompt 结构规范
description          : string       # 格式: "{project_id} EP{XX} Part-{A|B} 「{episode_title}」{上|下}半部分 9宫格分镜→视频"
modelConfig          : object
  └─ model           : string       # 默认: "Seedance 2.0 Fast"
  └─ referenceMode   : string       # 默认: "全能参考"
  └─ aspectRatio     : string       # 默认: "16:9"
  └─ duration        : string       # 默认: "15s"
referenceFiles       : string[]     # 相对路径数组，至少包含 1 个分镜图路径
  # 路径格式示例:
  #   "episodes/EP01/DM-003-EP01-A_storyboard.png"   ← 分镜图（必须）
  #   "characters/林宇_ref.png"                        ← 角色参考图（本 Part 出场时）
  #   "scenes/scene_01_ref.png"                        ← 场景参考图（可选）
  #   "props/prop_01_ref.png"                          ← 道具参考图（可选）
realSubmit           : boolean      # 默认: false；true = 真实提交生成视频
priority             : integer      # 优先级，通常与集数顺序一致（EP01 = 1）
tags                 : string[]     # 必须至少包含 ["{project_id}", "EP{XX}", "A" 或 "B"]
```

**Prompt 结构规范（固定四段，顺序不可变）：**

```
段1 — 头部声明（列出分镜图和角色参考图）:
  "(@{project_id}-EP{XX}-{A|B}_storyboard.png) 为9宫格分镜参考图，(@{角色名}_ref.png) 为角色「{角色名}」的参考形象，..."
  规则: 仅列出本 Part 出场的角色；场景/道具参考图不在此段声明

段2 — 标准排除指令（固定文本，不可修改）:
  "从镜头1开始，不要展示多宫格分镜参考图片。分镜图制作成电影级别的高清影视级别的视频。严禁参考图出现在画面中。每个画面为单一画幅，独立展示，没有任何分割线或多宫格效果画面。(Exclusions); Do not show speech bubbles, do not show comic panels, remove all text, full technicolor.排除项: No speech bubbles(无对话气泡),No text(无文字), No comic panels(无漫画分镜),No split screen(无分屏),No monochrome(非单色/黑白),No manga effects(无漫画特效线).正向替代:Fullscreen(全屏),Single continuous scene(单一连续场景).表情、嘴型、呼吸、台词严格同步。去掉图片中的水印，不要出现任何水印。没有任何字幕。"

段3 — 集信息行（含场景/道具内联引用）:
  "{video_id} 第{N}集「{episode_title}」{上|下}半部分。{synopsis}。 氛围：{atmosphere.overall_mood}。 场景参考 (@{scene_id}_ref.png) ...。道具参考 (@{prop_id}_ref.png) ...。"
  规则: 无场景/道具时省略对应子句

段4 — 逐镜头描述（9条，格式固定）:
  "镜头{N}({time_start}s-{time_end}s): 第{episode}集{上|下}半第{N}格：{scene_description}。 {camera}。 {atmosphere}。 音效:{sfx}。 (@{角色名}_ref.png){角色名}{action}，表情{expression}。 (@{角色名}_ref.png){角色名}说：\"{dialogue.text}\"（{dialogue.emotion}）"
  旁白格式: "旁白，{emotion}：\"{text}\""
```

### 4. Optional Fields

```
tasks[].tags 可追加额外标签:
  "incomplete_refs"   # 由 assemble-tasks 在场景/道具参考图缺失时追加（WARNING 标记）
```

### 5. Naming Rules

- 文件名固定为 `seedance_project_tasks.json`
- 路径固定为 `{project_dir}/seedance_project_tasks.json`
- 文件中**只允许出现相对路径**，不得出现绝对路径或 base64 data URI

### 6. Validation Rules

1. `total_tasks` 必须等于 `50`
2. `tasks` 数组长度必须等于 `total_tasks`
3. 任务排列顺序必须为 EP01-A, EP01-B, ..., EP25-A, EP25-B
4. 每条 `referenceFiles` 均必须为字符串（相对路径），不得为对象或 base64 字符串
5. 每条 `referenceFiles` 中至少有 1 个路径匹配 `episodes/EP\d{2}/.*_storyboard\.png`
6. 每条 `prompt` 必须包含段2的标准排除指令（含关键短语 `No speech bubbles`）
7. 每条 `prompt` 必须包含 9 条镜头描述（含关键短语 `镜头1` 到 `镜头9`）
8. 每条 `tags` 必须包含 3 个元素：`[project_id, "EP{XX}", "A" 或 "B"]`
9. `referenceFiles` 中所有路径均必须能在项目目录下找到对应文件（`submit-project` 的 Gate B4 校验）

### 7. Blocking Errors

| 错误 | 条件 | 触发技能 |
|------|------|---------|
| `[BLOCK] total_tasks ≠ 50` | `total_tasks` 值不为 50 | submit-project (B2) |
| `[BLOCK] referenceFiles 含 base64 对象` | 任意 `referenceFiles` 元素为对象而非字符串 | submit-project |
| `[BLOCK] 分镜图路径缺失` | 任意任务的 `referenceFiles` 中无 `_storyboard.png` 路径 | submit-project |
| `[BLOCK] referenceFiles 路径文件不存在` | 任意路径无法在磁盘上找到对应文件 | submit-project (B4) |
| `[BLOCK] prompt 缺少标准排除指令` | `No speech bubbles` 不在 prompt 中 | assemble-tasks（路径验证阶段） |

### 8. Warning Issues

| 警告 | 条件 |
|------|------|
| `[WARN] tags 含 incomplete_refs` | 任意任务的 `tags` 含 `"incomplete_refs"`（场景/道具参考图不完整）|
| `[WARN] realSubmit 为 false` | 任意任务的 `realSubmit` 为 `false`（模拟模式，不生成真实视频）|
| `[WARN] prompt 中 9 镜头描述不足` | `镜头1` 到 `镜头9` 中有缺失 |

### 9. Producer Skill

`assemble-tasks`（整个文件由此技能创建，任何字段均不由其他技能写入）

### 10. Consumer Skills

| 技能 | 用途 |
|------|------|
| `submit-project` | 读取所有 task，将 `referenceFiles` 相对路径展开为 base64 对象，POST 到 Seedance API `/api/tasks/push` |
| `validate-stage` | 读取 `total_tasks`、`referenceFiles` 进行路径完整性验证 |

---

## 附录：跨 Artifact 一致性约束

以下约束跨越多个 artifact，违反时应由 `validate-stage` 统一报告。

| 约束 | 涉及 Artifacts | 规则 |
|------|--------------|------|
| `project_id` 全局唯一 | AC-001, AC-007, AC-008, AC-009 | 同一项目下所有文件的 `project_id` 必须相同 |
| `visual_style` 全局一致 | AC-001, AC-007 | `metadata.json.visual_style` 与所有集的 `storyboard_config.json.visual_style` 必须相同 |
| `scene_id` 引用完整性 | AC-004, AC-007 | `storyboard_config.json` 中 `scene_refs` 引用的 `scene_id` 必须存在于 `scene_bible.md` |
| `prop_id` 引用完整性 | AC-005, AC-007 | `storyboard_config.json` 中 `prop_refs` 引用的 `prop_id` 必须存在于 `prop_bible.md` |
| `character_name` 引用完整性 | AC-003, AC-007, AC-009 | `storyboard_config.json` 中角色名、`seedance_project_tasks.json` prompt 中 `@` 引用名，必须存在于 `character_bible.md` |
| `referenceFiles` 格式一致性 | AC-009 | `seedance_project_tasks.json` 中的 `referenceFiles` 必须全为相对路径字符串，绝不能是 base64 对象 |
| `video_index.json.status` 是状态唯一来源 | AC-008 | 任何技能判断当前项目阶段必须读取此字段，不得依赖文件存在性推断状态 |
| `subtitle` 永远为 false | AC-007 | 所有 `storyboard_config.json` 的 `subtitle` 字段值必须为 `false` |
