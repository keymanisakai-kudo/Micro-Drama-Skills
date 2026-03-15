---
name: init-drama-project
description: >
  初始化一个新的短剧项目目录结构，分配项目编号，写入元数据，并更新全局索引。
  对应 produce-anime 的 Step 1（初始化项目）和 Step 6（更新全局索引）。
---

# init-drama-project

## purpose

在 `projects/` 目录下为一部新短剧作品完成以下初始化工作：
1. 从 `projects/index.json` 获取并分配下一个 `DM-XXX` 编号
2. 创建标准项目目录结构（含所有子目录）
3. 写入 `metadata.json` 元数据
4. 向 `projects/index.json` 追加本作品条目，更新 `next_id` 和 `last_updated`

初始化完成后，项目处于「目录就绪、等待剧本编写」状态，`video_index.json` 尚未生成。

---

## when_to_use

- 用户首次发起制作新短剧请求（"制作一部短剧"、"创建新短剧"、"produce short drama"）
- 尚未存在对应项目目录时（`projects/DM-XXX_*` 不存在）

---

## when_not_to_use

- 项目目录已存在且 `metadata.json` 已写入时——此时应执行其他技能（如 `build-story-bible`）
- 用于重新初始化已有项目（会覆盖已有 metadata）

---

## inputs

| 输入 | 来源 | 必填 |
|------|------|------|
| 作品类型/题材 | 用户请求 | 否（未指定则随机选择） |
| 作品名称 | 用户请求 | 否（可由系统生成） |
| 视觉风格 | 用户请求或 `.config/visual_styles.json` | 否（未指定则使用 `default_style_id`） |
| `projects/index.json` | 文件系统 | 是（不存在则从 DM-001 开始） |
| `.config/visual_styles.json` | 文件系统 | 是（用于读取风格预设） |

---

## outputs

| 产物 | 路径 | 说明 |
|------|------|------|
| 项目目录 | `projects/{project_id}_{slug}/` | 含所有子目录 |
| `metadata.json` | `projects/{project_id}_{slug}/metadata.json` | 作品元数据 |
| `projects/index.json`（更新） | `projects/index.json` | 追加本作品条目 |

### metadata.json 结构

```json
{
  "project_id": "DM-001",
  "project_name": "作品名称",
  "project_name_en": "English Title",
  "directory": "DM-001_xxxx/",
  "genre": "类型（如 奇幻/悬疑/恋爱）",
  "style": "风格（如 热血/治愈）",
  "visual_style": {
    "style_id": 1,
    "style_name": "Cinematic Film",
    "camera": "...",
    "film_stock": "...",
    "filter": "...",
    "focal_length": "65mm",
    "aperture": "f/2.0",
    "prompt_suffix": "shot on ..."
  },
  "target_audience": "目标受众",
  "total_episodes": 25,
  "episode_duration_seconds": 30,
  "total_duration_seconds": 750,
  "core_theme": "一句话概括核心主题",
  "created_date": "YYYY-MM-DD",
  "video_count": 50
}
```

> **注意**：`metadata.json` 不包含 `status` 字段。项目阶段状态的唯一来源是 `video_index.json.status`（由后续技能写入）。

### projects/index.json 追加条目格式

```json
{
  "project_id": "DM-001",
  "project_name": "作品名称",
  "directory": "DM-001_xxxx/",
  "episodes": 25,
  "status": "scripted",
  "created_date": "YYYY-MM-DD",
  "video_count": 50
}
```

### 目录结构

```
projects/DM-001_xxxx/
├── metadata.json
├── script/
├── characters/
├── scenes/
├── props/
├── episodes/
│   ├── EP01/
│   ├── EP02/
│   ...
│   └── EP25/
```

---

## constraints

1. **编号格式**：`DM-XXX`，三位数字，从 `001` 递增，读取 `projects/index.json` 的 `next_id` 字段确定
2. **目录命名**：`{project_id}_{作品名称拼音缩写或英文slug}`，全小写，使用下划线分隔
3. **集数目录**：必须预创建 EP01–EP25 共 25 个子目录
4. **`visual_style` 对象**：必须来自 `.config/visual_styles.json`，不得手动构造
5. **风格选择交互**：若用户未指定视觉风格，必须列出所有可用风格让用户选择后再继续（不得静默使用默认值）
6. **`projects/index.json` 更新**：写入时必须更新 `next_id`（当前编号+1）、`last_updated`、`total_projects`
7. **`metadata.json` 不含 `status`**：状态由 `video_index.json` 管理，初始化阶段不写入该字段

---

## workflow

### Step 1：读取全局索引，确定项目编号

1. 检查 `projects/index.json` 是否存在
   - 不存在：`project_id = "DM-001"`, `next_id = "DM-002"`
   - 存在：读取 `next_id` 作为本次 `project_id`

### Step 2：确认视觉风格

1. 读取 `.config/visual_styles.json`，列出所有风格选项
2. 若用户已在请求中指定风格（名称/ID/中文名），直接选取对应预设
3. 若用户未指定，使用 `ask_questions` 工具列出所有风格，等待用户确认

### Step 3：创建项目目录结构

1. 生成目录名：`projects/{project_id}_{slug}/`
2. 创建根目录及所有子目录：`script/`, `characters/`, `scenes/`, `props/`, `episodes/EP01/`–`episodes/EP25/`

### Step 4：写入 metadata.json

按 outputs 中定义的结构写入 `projects/{project_id}_{slug}/metadata.json`。

### Step 5：更新 projects/index.json

追加本作品条目，更新 `next_id`, `last_updated`, `total_projects`。

---

## checklist

- [ ] `projects/index.json` 已读取，`project_id` 已确定
- [ ] 视觉风格已通过交互或指定方式确认（来自 `visual_styles.json`）
- [ ] 项目根目录已创建
- [ ] EP01–EP25 共 25 个子目录均已创建
- [ ] `metadata.json` 已写入，不含 `status` 字段
- [ ] `metadata.json` 中 `visual_style` 对象完整（含 `prompt_suffix`）
- [ ] `projects/index.json` 已更新：新条目已追加，`next_id` 已递增

---

## failure_modes

| 错误场景 | 处理方式 |
|---------|---------|
| `projects/index.json` 不存在 | 视为首个项目，从 DM-001 开始 |
| `.config/visual_styles.json` 不存在 | **阻断执行**，提示用户先创建视觉风格配置文件 |
| 目标目录已存在 | **阻断执行**，提示用户该编号已存在，询问是否继续或重新初始化 |
| 用户未选择视觉风格 | 等待用户响应，不得跳过风格选择步骤 |
| `next_id` 格式不符合 DM-XXX 规范 | 自动修复为下一个合法编号，并警告 |
