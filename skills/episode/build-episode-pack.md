---
name: build-episode-pack
description: >
  为指定集（或全部25集）生成两个文件：对话脚本 dialogue.md 和
  故事板配置 storyboard_config.json（含 Part A/B 各9宫格分镜）。
  同时在全部25集生成后写入 video_index.json，将状态置为 "scripted"。
  对应 produce-anime 的 Step 4（逐集生成内容）和 Step 5（生成视频编号管理索引）。
category: episode
version: "1.0"
---

# build-episode-pack

## Purpose

为每一集生成：
1. `dialogue.md`：上下两部分的中文对话脚本（各 1-3 句，共 3-6 句）
2. `storyboard_config.json`：Part A（0-15s）和 Part B（15-30s）各含 9 宫格分镜，每格含镜头/角色/对话/氛围/AI绘图关键词等完整信息

所有 25 集生成后，写入 `video_index.json`（`status = "scripted"`），标志前期制作完成。

---

## When to Use

- 角色/场景/道具设计已完成（三份圣经文件均存在）
- 需要生成指定集的内容文件（支持单集/范围/全部25集）
- 需要更新 `video_index.json` 为最终索引

---

## When Not to Use

- 任一圣经文件（`character_bible.md`、`scene_bible.md`、`prop_bible.md`）尚不存在
- 需要修改已生成的分镜格式（请直接编辑文件）

---

## Inputs

| 输入 | 来源 | 必填 |
|------|------|------|
| `full_script.md` | `script/full_script.md` | 是 |
| `character_bible.md` | `characters/character_bible.md` | 是 |
| `scene_bible.md` | `scenes/scene_bible.md` | 是 |
| `prop_bible.md` | `props/prop_bible.md` | 是 |
| `metadata.json` | `metadata.json` | 是（获取 `project_id`, `visual_style`） |
| 目标集数 | 用户请求 | 否（默认全部25集） |

---

## Outputs

| 产物 | 路径 | 说明 |
|------|------|------|
| `dialogue.md` | `episodes/EPxx/dialogue.md` | 每集1份，含上下两部分对话 |
| `storyboard_config.json` | `episodes/EPxx/storyboard_config.json` | 每集1份，含 Part A/B 各9宫格 |
| `video_index.json` | 项目根目录 | 全部25集完成后写入，`status = "scripted"` |

### dialogue.md 结构

```markdown
# 第X集：[标题] 对话脚本

## 注意：本集视频不带字幕，对话通过配音传达

## 上半部分（Part A：00:00-00:15）
## 视频编号：{project_id}-EPxx-A

| 序号 | 时间 | 角色 | 对话内容（中文） | 语气/情感 | 备注 |
|------|------|------|----------------|----------|------|
| 1 | 00:02 | 角色A | 「对话内容」 | 坚定 | — |

## 下半部分（Part B：00:15-00:30）
## 视频编号：{project_id}-EPxx-B

| 序号 | 时间 | 角色 | 对话内容（中文） | 语气/情感 | 备注 |
|------|------|------|----------------|----------|------|
| 4 | 00:17 | 角色B | 「对话内容」 | 低沉 | — |
```

### storyboard_config.json 完整结构

```json
{
  "video_id_prefix": "{project_id}-EPxx",
  "episode": 1,
  "episode_title": "集标题",
  "total_duration_seconds": 30,
  "fps": 24,
  "resolution": "1920x1080",
  "aspect_ratio": "16:9",
  "style": "short_drama",
  "visual_style": {
    "style_id": 1,
    "style_name": "...",
    "camera": "...",
    "film_stock": "...",
    "filter": "...",
    "focal_length": "...",
    "aperture": "...",
    "prompt_suffix": "..."
  },
  "subtitle": false,
  "synopsis": "本集剧情概要（100字）",
  "emotion_tone": "情感基调",
  "connection": {
    "from_previous": "与上集的衔接",
    "to_next": "为下集的铺垫"
  },
  "part_a": {
    "video_id": "{project_id}-EPxx-A",
    "label": "上",
    "time_range": "00:00-00:15",
    "duration_seconds": 15,
    "scene_refs": ["scene_01"],
    "prop_refs": [],
    "atmosphere": {
      "overall_mood": "上半部分氛围总描述",
      "color_palette": ["#色值1", "#色值2", "#色值3"],
      "lighting": "光影描述",
      "weather": "天气/环境"
    },
    "video_prompt": "English prompt for Part A (15s), 16:9. No subtitles.",
    "bgm": {
      "description": "背景音乐描述",
      "mood": "音乐情绪关键词"
    },
    "storyboard_9grid": [
      {
        "grid_number": 1,
        "time_start": 0.0,
        "time_end": 1.67,
        "scene_description": "画面描述（50字）",
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
          "speaker": "角色名或null",
          "text": "中文对话内容",
          "emotion": "语气/情感"
        },
        "atmosphere": "本格氛围描述",
        "sfx": "音效描述",
        "ai_image_prompt": "English prompt for this grid: character, composition, lighting, mood, 16:9. [DO NOT include prompt_suffix here]"
      }
      // grid_number 2–9 结构相同
    ]
  },
  "part_b": {
    // 结构与 part_a 完全相同，video_id 后缀为 -B
  }
}
```

### video_index.json 结构（25集全部完成后写入）

```json
{
  "project_id": "DM-001",
  "project_name": "作品名称",
  "total_episodes": 25,
  "created_date": "YYYY-MM-DD",
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
    // 共25条
  ],
  "editing_guide": {
    "total_episodes": 25,
    "parts_per_episode": 2,
    "total_videos": 50,
    "duration_per_part_seconds": 15,
    "total_duration_seconds": 750,
    "grids_per_part": 9,
    "total_grids": 450
  }
}
```

---

## Constraints

### 视频编号约束

| 字段 | 规则 |
|------|------|
| Part A video_id | `{project_id}-EP{两位数字}-A`，如 `DM-001-EP01-A` |
| Part B video_id | `{project_id}-EP{两位数字}-B`，如 `DM-001-EP01-B` |
| `video_id_prefix` | `{project_id}-EP{两位数字}`，如 `DM-001-EP01` |

### 9宫格分镜约束

| 参数 | 要求 |
|------|------|
| 每 Part 格数 | 固定 **9** 格（3×3布局） |
| 每格时长 | 约 **1.67秒**（15 ÷ 9） |
| 格1 时间区间 | `time_start: 0.0`, `time_end: 1.67` |
| 格2 时间区间 | `time_start: 1.67`, `time_end: 3.33` |
| 格3 | `3.33–5.0` |
| 格4 | `5.0–6.67` |
| 格5 | `6.67–8.33` |
| 格6 | `8.33–10.0` |
| 格7 | `10.0–11.67` |
| 格8 | `11.67–13.33` |
| 格9 | `13.33–15.0` |
| `grid_number` | 整数，1–9，不得缺少或重复 |
| `ai_image_prompt` | 英文，**不得包含** `visual_style.prompt_suffix` |

### 对话约束

1. **语言**：所有对话必须为中文
2. **长度**：每句不超过 15 字为佳
3. **数量**：每集 3-6 句（Part A 1-3 句，Part B 1-3 句）
4. **字幕禁止**：`subtitle` 字段始终为 `false`

### 场景/道具引用约束

- `scene_refs` 必须引用 `scene_bible.md` 中存在的 `scene_id`（格式 `scene_XX`）
- `prop_refs` 必须引用 `prop_bible.md` 中存在的 `prop_id`（格式 `prop_XX`）
- 一次性出现的场景不在 `scene_refs` 中引用（无需参考图）

### video_index.json 约束

- 必须在全部 25 集的内容文件均生成后写入
- `status` 必须为 `"scripted"`
- `videos` 数组必须包含 25 条（每集一条，含 `part_a` 和 `part_b`）

---

## Workflow

### Step 1：准备工作

读取 `metadata.json`、`full_script.md`、`character_bible.md`、`scene_bible.md`、`prop_bible.md`。
确定要生成的集数范围（默认 EP01–EP25）。

### Step 2：逐集生成内容（循环 EP01–EP25）

对每一集：
1. 从 `full_script.md` 读取本集概要、情感基调、关键事件
2. **生成 `dialogue.md`**：根据概要编写 3-6 句中文对话，分配到 Part A/B

3. **生成 `storyboard_config.json`**：
   - 确定本集引用的场景（`scene_refs`）和道具（`prop_refs`）
   - 为 Part A 和 Part B 各生成 9 个 `GridItem`
   - 每格 `ai_image_prompt` 须为英文，不含 `prompt_suffix`
   - `visual_style` 对象从 `metadata.json` 原样复制
   - `subtitle` 固定为 `false`

### Step 3：写入 video_index.json（所有集完成后）

按 outputs 中定义的结构写入，`status = "scripted"`，`videos` 数组含 25 条。

---

## Checklist

- [ ] 所有4个输入文件均已读取（`full_script.md`、三份圣经文件）
- [ ] 每集生成 2 个文件：`dialogue.md`、`storyboard_config.json`
- [ ] 每集的对话为中文，3-6句，无字幕（`subtitle: false`）
- [ ] 每集 Part A/B 各含 9 格分镜（`grid_number` 1–9 完整）
- [ ] 所有 `ai_image_prompt` 为英文，不含 `prompt_suffix`
- [ ] `scene_refs` 引用的所有 `scene_id` 在 `scene_bible.md` 中存在
- [ ] `prop_refs` 引用的所有 `prop_id` 在 `prop_bible.md` 中存在
- [ ] `video_id` 格式正确（`{project_id}-EPxx-A/B`）
- [ ] EP01–EP25 所有 25 集均已生成
- [ ] `video_index.json` 已写入，`status = "scripted"`，`videos` 数组有 25 条

---

## Failure Modes

| 错误场景 | 处理方式 |
|---------|---------|
| 任一圣经文件不存在 | **阻断执行**，提示先运行 `build-production-bibles` |
| 某集 `storyboard_9grid` 不足 9 格 | **阻断执行**，该集重新生成直到达到 9 格 |
| `ai_image_prompt` 含有 `prompt_suffix` 内容 | 警告并自动移除 `prompt_suffix` 部分 |
| `scene_refs` 引用了不存在的 `scene_id` | 警告，提示用户检查 `scene_bible.md` |
| `dialogue.md` 对话包含英文 | 警告，对话须为中文 |
| 单集生成失败（中途中断） | 记录失败集数，支持断点续传（重新运行时跳过已完成的集） |
| `video_index.json` 在不足 25 集时被要求写入 | **拒绝写入**，等待所有 25 集完成 |
