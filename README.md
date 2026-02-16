# Micro-Drama-Skills 🎬

AI 驱动的短剧全流程自动化制作系统。通过 Claude Skills 实现从剧本编写、角色设计、分镜生成到视频提交的完整工作流。

## 项目概述

本项目提供一套 **Claude 技能（Skills）**，用于自动化生成短剧作品。每部作品包含 25 集（每集 30 秒），系统自动生成剧本、角色设定、6 宫格分镜图、故事板配置，并可调用 AI API 生成图片/视频，最终提交到 Seedance 视频生成流水线。

### 核心能力

| 技能 | 功能 | 触发指令示例 |
|------|------|-------------|
| **produce-anime** | 生成完整短剧（剧本+角色+分镜+故事板） | "制作一部科幻短剧" |
| **generate-media** | 调用 Gemini API 生成角色图/分镜图/视频 | "生成 DM-002 的图片" |
| **submit-anime-project** | 批量提交任务到 Seedance 视频生成 | "提交 DM-002 到 Seedance" |

## 目录结构

```
.
├── .claude/skills/                  # Claude 技能定义
│   ├── produce-anime/SKILL.md       # 短剧制作技能
│   ├── generate-media/SKILL.md      # 媒体生成技能
│   └── submit-anime-project/SKILL.md # 任务提交技能
├── .config/
│   ├── api_keys.sample.json         # API 配置示例
│   ├── api_keys.json                # API 配置（需自行创建，已 gitignore）
│   └── visual_styles.json           # 视觉风格预设（10 种）
├── projects/
│   ├── index.json                   # 全局作品索引
│   ├── DM-001_dhgt/                 # 《灯火归途》
│   └── DM-002_tjkc/                 # 《碳金狂潮》
└── README.md
```

### 单部作品目录结构

```
DM-002_tjkc/
├── metadata.json                    # 作品元数据
├── script/full_script.md            # 完整剧本（25 集）
├── characters/
│   ├── character_bible.md           # 角色设定集
│   ├── ref_index.json               # 角色参考图索引
│   ├── 林策_ref.png                  # 角色参考图（gitignore）
│   └── ...
├── episodes/
│   ├── EP01/
│   │   ├── dialogue.md              # 对话脚本
│   │   ├── storyboard_config.json   # 故事板配置（6 宫格 × 上下两部分）
│   │   ├── seedance_tasks.json      # Seedance 提交任务
│   │   ├── DM-002-EP01-A_storyboard.png  # 上半分镜图（gitignore）
│   │   └── DM-002-EP01-B_storyboard.png  # 下半分镜图（gitignore）
│   └── ... (EP01-EP25)
├── seedance_project_tasks.json      # 全剧任务汇总（50 条）
├── video_index.json                 # 视频编号索引
└── generate_media.py                # 媒体生成脚本
```

## 快速开始

### 1. 配置 API

复制示例配置并填入你的 API Key：

```bash
cp .config/api_keys.sample.json .config/api_keys.json
```

编辑 `.config/api_keys.json`：

```json
{
  "gemini_api_key": "YOUR_GEMINI_API_KEY",
  "base_url": "https://generativelanguage.googleapis.com/",
  "gemini_image_model": "gemini-2.5-flash-image-preview"
}
```

### 2. 安装依赖

```bash
python -m venv .venv
source .venv/bin/activate
pip install google-genai Pillow requests
```

### 3. 使用 Claude 技能

在支持 Claude Skills 的工具（如 Claude Code、OpenClaw 等）中打开本项目，技能会自动加载。

**制作短剧：**
```
> 制作一部港风复古短剧
> 制作一部赛博朋克风格的校园短剧
```

**生成媒体：**
```
> 生成 DM-002 的分镜图片
> 生成第 1 到第 5 集的图片
```

**提交任务：**
```
> 提交 DM-002 到 Seedance（模拟模式）
```

## 视觉风格预设

系统内置 10 种电影级视觉风格，制作时可通过名称、ID 或中文名指定：

| ID | 英文名 | 中文名 | 摄影机/特征 |
|----|--------|--------|------------|
| 1 | Cinematic Film | 电影质感 | Panavision Sphero 65, Vision3 500T (**默认**) |
| 2 | Anime Classic | 经典动漫 | Studio Ghibli 手绘风 |
| 3 | Cyberpunk Neon | 赛博朋克 | RED Monstro 8K, 霓虹高对比 |
| 4 | Chinese Ink Painting | 水墨国风 | ARRI ALEXA Mini LF, 水墨渲染 |
| 5 | Korean Drama | 韩剧氛围 | Sony VENICE 2, 暖色浅景深 |
| 6 | Dark Thriller | 暗黑悬疑 | ARRI ALEXA 65, 明暗法 |
| 7 | Vintage Hong Kong | 港风复古 | Kodak Vision3, Cooke Anamorphic |
| 8 | Wuxia Epic | 武侠大片 | Panavision DXL2, 大场面雾气 |
| 9 | Soft Romance | 甜蜜恋爱 | Canon C500, 柔焦暖色 |
| 10 | Documentary Real | 纪实写实 | Sony FX6, 手持自然光 |

每种风格的 `prompt_suffix` 会自动追加到所有 AI 生成提示词末尾。可在 `.config/visual_styles.json` 中自定义或新增风格。

## Seedance 任务提交

系统将每张分镜图（A/B 各 1 张）映射为 1 个 Seedance 任务，每集 2 个任务，全剧 50 个任务。

### 任务 Prompt 结构

```
(@DM-002-EP01-A_storyboard.png) 为6宫格分镜参考图，
(@林策_ref.png) 为角色「林策」的参考形象，(@沈璃_ref.png) 为角色「沈璃」...

从镜头1开始，不要展示多宫格分镜参考图片。分镜图制作成电影级别的高清影视...

DM-002-EP01-A 第1集「呼吸税时代」上半部分。剧情概要。氛围。

镜头1(0.0s-2.5s): 场景描述。(@林策_ref.png)林策动作... 林策说："台词"（情感）
镜头2(2.5s-5.0s): ...
...
镜头6(12.5s-15.0s): ...
```

### Seedance API

- 服务地址：`http://localhost:3456`
- 核心接口：`POST /api/tasks/push`
- 支持批量提交（`tasks` 数组）
- `realSubmit: false` 为模拟模式，`true` 为真实提交

## 技术栈

- **AI 技能平台**：Claude Skills（`.claude/skills/`）
- **图片生成**：Google Gemini（`gemini-2.5-flash-image-preview` / `gemini-3-pro-image-preview`）
- **视频生成**：Google Veo 2（`veo-2.0-generate-001`）
- **任务提交**：Seedance 视频生成流水线（HTTP REST API）
- **运行环境**：Python 3.13+，`google-genai` SDK

## 已有作品

| 编号 | 名称 | 类型 | 状态 |
|------|------|------|------|
| DM-001 | 《灯火归途》 | — | 已编剧 |
| DM-002 | 《碳金狂潮》 | 科幻/金融/悬疑 | 已编剧 + 分镜图 + 任务已生成 |

## License

MIT
