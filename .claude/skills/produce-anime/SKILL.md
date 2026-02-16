---
name: produce-anime
description: 短剧制作技能。用于生成完整短剧作品，包括剧本编写、角色设计、6宫格分镜、故事板配置。每次运行生成1部作品（25集，每集30秒=上下两部分各15秒，每部分6宫格分镜+视频生成故事板）。关键词：短剧、影视、drama、剧本、分镜、storyboard、角色设计、视频制作。
---

# 短剧制作技能 (Produce Short Drama)

## 概述

本技能用于自动化生成完整短剧作品的全套制作文档和脚本。每次运行生成 **1部完整作品**，包含 **25集**，每集 **30秒**，分为 **上、下两部分**（各15秒）：
- 每部分包含 **6宫格分镜提示词** + **视频生成故事板**
- 每集生成 **3个文件**：对话脚本 + 故事板配置 + Seedance任务JSON（每分镜一条任务）
- 含氛围描述、中文人物对话、无字幕
- 视频编号管理索引
- 支持**视觉风格预设**（从 `.config/visual_styles.json` 读取，注入到提示词和配置中）

---
## 视觉风格预设

项目支持从 `/data/dongman/.config/visual_styles.json` 读取视觉风格预设。用户可通过以下方式指定风格：
- 指定风格名：如 "使用 Vintage Hong Kong 风格"
- 指定风格ID：如 "风格7"
- 指定中文名：如 "港风复古"
- 不指定：使用 `default_style_id` 对应的默认风格

选中的风格会：
1. 写入 `metadata.json` 的 `visual_style` 字段
2. 写入每集 `storyboard_config.json` 的 `visual_style` 字段
3. 将 `prompt_suffix` 追加到所有 `ai_image_prompt` 和 `video_prompt` 末尾

风格预设字段说明：

| 字段 | 说明 | 示例 |
|------|------|------|
| `camera` | 摄影机/机身 | Panavision Sphero 65 and Hasselblad Lenses |
| `film_stock` | 胶片/传感器 | Vision3 500T 5219 |
| `filter` | 滤镜组合 | ND0.6, Diffusion Filter 1/4 |
| `focal_length` | 焦距 | 65mm |
| `aperture` | 光圈 | f/2.0 |
| `prompt_suffix` | 追加到AI提示词末尾的风格描述 | shot on Panavision... |

---
## 执行流程

当用户要求制作短剧/影视作品时，按以下步骤顺序执行：

### 第一步：初始化项目

1. 读取 `/data/dongman/projects/index.json` 获取当前作品编号（如不存在则从 `DM-001` 开始）
2. 在 `/data/dongman/projects/` 下创建新作品目录，命名规则：`{作品编号}_{作品名称拼音缩写}/`
3. 创建作品目录结构：

```
projects/
├── index.json                          # 所有作品索引（全局管理）
└── DM-001_xxxx/                        # 单部作品目录
    ├── metadata.json                   # 作品元数据
    ├── script/                         # 剧本
    │   └── full_script.md              # 完整剧本（25集大纲+详细剧本）
    ├── characters/                     # 角色设计
    │   └── character_bible.md          # 角色圣经（所有角色设定）
    ├── episodes/                       # 各集内容
    │   ├── EP01/
    │   │   ├── dialogue.md             # 本集对话脚本（中文，覆盖上下两部分）
    │   │   └── storyboard_config.json  # 故事板配置（含上下两部分，每部分6宫格+视频生成提示词）
    │   │   └── seedance_tasks.json     # Seedance提交任务（每分镜1条，共12条）
    │   ├── EP02/
    │   │   └── ...
    │   └── ... (EP01-EP25)
    ├── seedance_project_tasks.json     # 全剧任务汇总（300条任务）
    └── video_index.json                # 视频编号管理索引
```

### 第二步：剧本编写 (Script Writing)

生成 `script/full_script.md`，包含：

```markdown
# 《作品名称》完整剧本

## 作品信息
- **类型**：[冒险/奇幻/科幻/日常/恋爱 等]
- **风格**：[热血/治愈/悬疑/搞笑 等]
- **视觉风格**：[风格预设名称，如 Cinematic Film]
- **目标受众**：[少年/少女/青年/全年龄]
- **总时长**：25集 × 30秒 = 12分30秒
- **核心主题**：一句话概括

## 世界观设定
[200-300字描述世界观]

## 故事大纲
[500字总体故事线]

## 各集概要
### 第1集：[标题]
- **剧情概要**：[50字]
- **关键事件**：[列表]
- **情感基调**：[喜/怒/哀/乐/紧张/温馨]

### 第2集：[标题]
...（共25集）
```

### 第三步：角色设计 (Character Design)

生成 `characters/character_bible.md`，每个角色包含：

```markdown
# 角色设定集

## 主要角色

### 角色1：[名字]
- **全名**：
- **年龄**：
- **性别**：
- **身高/体重**：
- **外貌特征**：[详细描述，用于AI绘图提示词]
  - 发型/发色：
  - 瞳色：
  - 体型：
  - 标志性特征：
- **服装设计**：
  - 日常服装：
  - 战斗/特殊服装：
- **性格特点**：
- **口头禅**：
- **背景故事**：[100字]
- **角色弧光**：[在25集中的成长变化]
- **AI绘图关键词（英文）**：[用于生成角色一致性的Prompt]

## 次要角色
...

## 角色关系图
[用文字描述角色间的关系网络]
```

### 第四步：逐集生成内容

对每一集（EP01-EP25），生成以下 **3个文件**：

#### 4.1 对话脚本 `dialogue.md`

覆盖上、下两部分的全部对话：

```markdown
# 第X集：[标题] 对话脚本

## 注意：本集视频不带字幕，对话通过配音传达

## 上半部分（Part A：00:00-00:15）
## 视频编号：DM-001-EP01-A

| 序号 | 时间 | 角色 | 对话内容（中文） | 语气/情感 | 备注 |
|------|------|------|----------------|----------|------|
| 1 | 00:02 | 角色A | 「对话内容」 | 坚定 | — |
| 2 | 00:06 | 角色B | 「对话内容」 | 惊讶 | — |
| 3 | 00:11 | 角色A | 「对话内容」 | 激动 | — |

## 下半部分（Part B：00:15-00:30）
## 视频编号：DM-001-EP01-B

| 序号 | 时间 | 角色 | 对话内容（中文） | 语气/情感 | 备注 |
|------|------|------|----------------|----------|------|
| 4 | 00:17 | 角色B | 「对话内容」 | 低沉 | — |
| 5 | 00:22 | 角色A | 「对话内容」 | 温柔 | — |
| 6 | 00:27 | 角色C | 「对话内容」 | 神秘 | — |
```

#### 4.2 故事板配置 `storyboard_config.json`

包含上、下两部分，每部分 **6宫格分镜** + **视频生成故事板提示词**：

```json
{
  "video_id_prefix": "DM-001-EP01",
  "episode": 1,
  "episode_title": "第1集标题",
  "total_duration_seconds": 30,
  "fps": 24,
  "resolution": "1920x1080",
  "style": "short_drama",
  "visual_style": {
    "style_id": 1,
    "style_name": "Cinematic Film",
    "camera": "Panavision Sphero 65 and Hasselblad Lenses",
    "film_stock": "Vision3 500T 5219",
    "filter": "ND0.6, Diffusion Filter 1/4",
    "focal_length": "65mm",
    "aperture": "f/2.0",
    "prompt_suffix": "shot on Panavision Sphero 65 and Hasselblad Lenses, Vision3 500T 5219, ND0.6, Diffusion Filter 1/4, cinematic film grain, shallow depth of field"
  },
  "subtitle": false,
  "synopsis": "本集剧情概要（100字）",
  "emotion_tone": "情感基调",
  "connection": {
    "from_previous": "与上集的衔接",
    "to_next": "为下集的铺垫"
  },

  "part_a": {
    "video_id": "DM-001-EP01-A",
    "label": "上",
    "time_range": "00:00-00:15",
    "duration_seconds": 15,
    "atmosphere": {
      "overall_mood": "上半部分氛围总描述",
      "color_palette": ["#色值1", "#色值2", "#色值3"],
      "lighting": "光影描述",
      "weather": "天气/环境"
    },
    "video_prompt": "English prompt for AI video generation of Part A (15s). Describe the full scene, characters, actions, camera movements, mood, lighting. [visual_style.prompt_suffix appended automatically]. No subtitles.",
    "bgm": {
      "description": "背景音乐描述",
      "mood": "音乐情绪关键词"
    },
    "storyboard_6grid": [
      {
        "grid_number": 1,
        "time_start": 0.0,
        "time_end": 2.5,
        "scene_description": "画面描述（50字，含人物动作、表情、光影）",
        "camera": {
          "type": "远景|中景|近景|特写",
          "movement": "固定|推|拉|摇|移|跟",
          "angle": "平视|俯视|仰视"
        },
        "characters": [
          {
            "name": "角色名",
            "action": "动作描述",
            "expression": "表情",
            "position": "画面位置(左/中/右)"
          }
        ],
        "dialogue": {
          "speaker": "角色名（无对话则为null）",
          "text": "中文对话内容",
          "emotion": "语气/情感"
        },
        "atmosphere": "本格氛围描述",
        "sfx": "音效描述",
        "ai_image_prompt": "English prompt for this grid's image: character, composition, lighting, mood. [visual_style.prompt_suffix will be appended automatically]"
      },
      {
        "grid_number": 2,
        "time_start": 2.5,
        "time_end": 5.0,
        "scene_description": "...",
        "camera": {},
        "characters": [],
        "dialogue": {},
        "atmosphere": "...",
        "sfx": "...",
        "ai_image_prompt": "..."
      },
      {
        "grid_number": 3,
        "time_start": 5.0,
        "time_end": 7.5,
        "...": "同上结构"
      },
      {
        "grid_number": 4,
        "time_start": 7.5,
        "time_end": 10.0,
        "...": "同上结构"
      },
      {
        "grid_number": 5,
        "time_start": 10.0,
        "time_end": 12.5,
        "...": "同上结构"
      },
      {
        "grid_number": 6,
        "time_start": 12.5,
        "time_end": 15.0,
        "...": "同上结构"
      }
    ]
  },

  "part_b": {
    "video_id": "DM-001-EP01-B",
    "label": "下",
    "time_range": "00:15-00:30",
    "duration_seconds": 15,
    "atmosphere": {
      "overall_mood": "下半部分氛围总描述",
      "color_palette": ["#色值1", "#色值2", "#色值3"],
      "lighting": "光影描述",
      "weather": "天气/环境"
    },
    "video_prompt": "English prompt for AI video generation of Part B (15s). Describe the full scene, characters, actions, camera movements, mood, lighting. [visual_style.prompt_suffix appended automatically]. No subtitles.",
    "bgm": {
      "description": "背景音乐描述",
      "mood": "音乐情绪关键词"
    },
    "storyboard_6grid": [
      {
        "grid_number": 1,
        "time_start": 0.0,
        "time_end": 2.5,
        "scene_description": "画面描述（50字）",
        "camera": {},
        "characters": [],
        "dialogue": {},
        "atmosphere": "...",
        "sfx": "...",
        "ai_image_prompt": "..."
      },
      { "grid_number": 2, "time_start": 2.5, "time_end": 5.0, "...": "同上结构" },
      { "grid_number": 3, "time_start": 5.0, "time_end": 7.5, "...": "同上结构" },
      { "grid_number": 4, "time_start": 7.5, "time_end": 10.0, "...": "同上结构" },
      { "grid_number": 5, "time_start": 10.0, "time_end": 12.5, "...": "同上结构" },
      { "grid_number": 6, "time_start": 12.5, "time_end": 15.0, "...": "同上结构" }
    ]
  }
}
```

#### 4.3 Seedance 任务 JSON `seedance_tasks.json`

基于本集 `storyboard_config.json` 的上下半部分 12 个分镜（`part_a.storyboard_6grid` + `part_b.storyboard_6grid`）生成提交任务数据。

要求：
1. **每个分镜必须生成一条任务 JSON 对象**（每集固定 12 条）
2. 输出文件为 `episodes/EPxx/seedance_tasks.json`
3. 文件结构使用 `tasks` 数组，兼容 `/api/tasks/push` 的批量推送格式
4. 默认 `realSubmit` 设为 `false`（安全）
5. `prompt` 必须来源于分镜 `ai_image_prompt`，并补充镜头/动作/情绪信息

示例：

```json
{
  "project_id": "DM-001",
  "episode": 1,
  "episode_code": "EP01",
  "tasks": [
    {
      "prompt": "Cinematic shot... (from ai_image_prompt + visual_style.prompt_suffix) ... keep character consistency",
      "description": "DM-001 EP01 A-Grid1 第1集上半第1格",
      "modelConfig": {
        "model": "Seedance 2.0 Fast",
        "referenceMode": "全能参考",
        "aspectRatio": "16:9",
        "duration": "5s"
      },
      "referenceFiles": [],
      "realSubmit": false,
      "priority": 1,
      "tags": ["DM-001", "EP01", "A", "GRID1"]
    }
  ]
}
```

字段映射规则：
- `description`：`{project_id} {EPxx} {A|B}-Grid{n} {scene_description}`
- `modelConfig.aspectRatio`：默认 `16:9`
- `modelConfig.duration`：默认 `5s`
- `referenceFiles`：默认 `[]`（后续由媒体技能补充角色参考图 URL）
- `priority`：默认 `1`
- `tags`：至少包含 `project_id`、`EPxx`、`A|B`、`GRIDn`

另外在项目根目录生成 `seedance_project_tasks.json`，汇总 EP01-EP25 的全部任务（共300条），用于整部作品一键提交。

**6宫格分镜布局说明**（2行×3列）：

```
| 格1 (0.0-2.5s) | 格2 (2.5-5.0s) | 格3 (5.0-7.5s) |
|:---:|:---:|:---:|
| 格4 (7.5-10.0s) | 格5 (10.0-12.5s) | 格6 (12.5-15.0s) |
```

- 每格 **2.5秒**，6格覆盖 **15秒**
- 上下两部分各有独立的6宫格
- 每集共 **12格分镜**（上6格 + 下6格）

### 第五步：生成视频编号管理索引

生成 `video_index.json`：

```json
{
  "project_id": "DM-001",
  "project_name": "作品名称",
  "total_episodes": 25,
  "created_date": "2026-02-14",
  "status": "scripted",
  "videos": [
    {
      "episode": 1,
      "episode_title": "第1集标题",
      "part_a": {
        "video_id": "DM-001-EP01-A",
        "label": "上",
        "duration": 15,
        "status": "script_ready",
        "files": {
          "dialogue": "episodes/EP01/dialogue.md",
          "storyboard_config": "episodes/EP01/storyboard_config.json"
        }
      },
      "part_b": {
        "video_id": "DM-001-EP01-B",
        "label": "下",
        "duration": 15,
        "status": "script_ready",
        "files": {
          "dialogue": "episodes/EP01/dialogue.md",
          "storyboard_config": "episodes/EP01/storyboard_config.json"
        }
      }
    }
  ],
  "editing_guide": {
    "total_episodes": 25,
    "parts_per_episode": 2,
    "total_videos": 50,
    "duration_per_part_seconds": 15,
    "total_duration_seconds": 750,
    "grids_per_part": 6,
    "total_grids": 300,
    "recommended_export_format": "MP4 H.264",
    "recommended_resolution": "1920x1080",
    "recommended_fps": 24
  }
}
```

### 第六步：更新全局索引

更新 `/data/dongman/projects/index.json`：

```json
{
  "last_updated": "2026-02-14",
  "total_projects": 1,
  "next_id": "DM-002",
  "projects": [
    {
      "project_id": "DM-001",
      "project_name": "作品名称",
      "directory": "DM-001_xxxx/",
      "episodes": 25,
      "status": "scripted",
      "created_date": "2026-02-14",
      "video_count": 50
    }
  ]
}
```

---

## 编号规则

### 作品编号
- 格式：`DM-XXX`（XXX为三位数字，从001递增）
- 示例：`DM-001`, `DM-002`, `DM-003`

### 视频编号
- **上半部分**：`{作品编号}-EP{集数两位}-A`
  - 示例：`DM-001-EP01-A`, `DM-001-EP25-A`
- **下半部分**：`{作品编号}-EP{集数两位}-B`
  - 示例：`DM-001-EP01-B`, `DM-001-EP25-B`

### 集数编号
- 格式：`EP{两位数字}`，从 `EP01` 到 `EP25`

---

## 内容创作规范

### 剧本要求
1. **故事完整性**：25集需要有完整的起承转合
   - 第1-3集：世界观介绍、角色登场、引入冲突
   - 第4-8集：冲突升级、角色关系建立
   - 第9-15集：高潮前奏、多线叙事、伏笔布局
   - 第16-20集：高潮阶段、转折、揭示
   - 第21-24集：最终决战、情感爆发
   - 第25集：结局、余韵
2. **每集30秒约束**：每集聚焦一个核心场景/事件，信息密度高
3. **上下结构**：每集上半部分（15s）铺垫/展开，下半部分（15s）高潮/转折
4. 每集结尾留悬念或情感钩子

### 对话要求
1. **语言**：所有对话必须为中文
2. **风格**：符合角色性格，简洁有力（每句不超过15字为佳）
3. **无字幕**：对话通过配音传达，不添加任何字幕
4. 每集对话控制在3-6句（上下各1-3句）

### 6宫格分镜要求
1. **时长**：每部分固定15秒
2. **格数**：固定6格（2×3布局）
3. 每格 **2.5秒**
4. 6格之间需要有视觉连续性和叙事逻辑
5. 每格必须包含：画面描述、镜头类型、对话（如有）、氛围描述
6. 上半部分和下半部分各有独立的整体氛围描述
7. 每部分附带完整的 **视频生成提示词**（`video_prompt`，英文）

### 故事板配置要求
1. JSON格式，可被程序直接解析
2. 包含 `part_a` 和 `part_b` 两个完整部分
3. 每部分包含：氛围、6宫格分镜、视频生成提示词
4. 包含AI图像/视频生成的英文Prompt
5. `subtitle` 字段始终为 `false`

---

## 运行指令

用户可以通过以下方式触发本技能：
- "制作一部短剧"
- "生成短剧作品"
- "produce short drama"
- "创建新短剧"
- "开始制作短剧"
- "运行"（在技能上下文中）

可附带可选参数：
- **题材/类型**：如 "制作一部科幻短剧"、"生成一部校园恋爱短剧"
- **视觉风格**：如 "港风复古"、"Vintage Hong Kong"、"风格7"（指定 visual_styles.json 中的预设）
- **风格**：如 "赛博朋克风格"、"中国风"
- **角色数量**：如 "主角3人"

如用户未指定题材，则随机选择一个有趣的原创题材。
如用户未指定视觉风格，则使用 `visual_styles.json` 中 `default_style_id` 对应的默认风格。

---

## 执行检查清单

完成生成后，自查以下内容：
- [ ] `index.json` 全局索引已更新
- [ ] `metadata.json` 作品元数据已创建
- [ ] `full_script.md` 完整剧本已生成（含25集概要）
- [ ] `character_bible.md` 角色设计已完成
- [ ] EP01-EP25 所有25个集目录均已创建
- [ ] 每集包含3个文件：`dialogue.md`, `storyboard_config.json`, `seedance_tasks.json`
- [ ] 每集的 `storyboard_config.json` 包含 `part_a` 和 `part_b`
- [ ] 每部分包含6宫格分镜 + 视频生成提示词
- [ ] 每集 `seedance_tasks.json` 含 12 条任务（每分镜1条）
- [ ] 项目根目录 `seedance_project_tasks.json` 已生成（总计300条任务）
- [ ] 所有视频编号遵循命名规则（`-A` / `-B` 后缀）
- [ ] `video_index.json` 已生成且包含50条视频记录（25集×2部分）
- [ ] 所有对话为中文
- [ ] 所有配置标注 `subtitle: false`
- [ ] 每集剧情有起承转合的衔接

---

## 输出示例

生成完成后，向用户报告：

```
✅ 短剧作品生成完成！

📋 作品信息
- 作品编号：DM-001
- 作品名称：《xxxxx》
- 视觉风格：Cinematic Film（电影质感）
- 类型：xxxxx
- 总集数：25集（每集上下两部分）

📁 项目目录：/data/dongman/projects/DM-001_xxxx/

📊 生成内容统计
- 完整剧本：1份
- 角色设定：X个角色
- 对话脚本：25份（每集1份，覆盖上下两部分）
- 故事板配置：25份（每集1份，含上下两部分6宫格+视频提示词）
- Seedance任务文件：25份（每集1份，每份12条）
- 全剧任务汇总：1份（300条）
- 视频总数：50个（25集 × 上下2部分）
- 总分镜格数：300格（50个视频 × 6格）

🎬 视频编号范围
- 上半部分：DM-001-EP01-A ~ DM-001-EP25-A
- 下半部分：DM-001-EP01-B ~ DM-001-EP25-B

📂 每集文件（3个）
- dialogue.md        → 对话脚本
- storyboard_config.json → 故事板配置
- seedance_tasks.json   → 分镜提交任务（12条）
```