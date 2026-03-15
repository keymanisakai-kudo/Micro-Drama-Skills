---
name: build-production-bibles
description: >
  基于剧本，设计并生成角色设定集、场景设定集、道具设定集，
  每个设定均包含 AI 绘图关键词（英文）。
  对应 produce-anime 的 Step 3（角色设计）、Step 3B（场景设计）、Step 3C（道具设计）。
category: production
version: "1.0"
---

# build-production-bibles

## Purpose

读取已编写的剧本 `full_script.md`，生成三份"制作圣经"文件：

1. **`characters/character_bible.md`**：所有主要/次要角色的外貌、性格、背景故事、AI绘图关键词
2. **`scenes/scene_bible.md`**：全剧反复出现的核心场景（3集以上），含 AI 绘图关键词
3. **`props/prop_bible.md`**：具有剧情意义的核心道具，含 AI 绘图关键词

这三份文件是 `generate-media` 技能的直接输入，决定了 AI 生成的参考图质量和一致性。

---

## When to Use

- `full_script.md` 已存在，三份圣经文件尚未创建
- 需要根据已修改的剧本重新生成某份圣经文件

---

## When Not to Use

- `full_script.md` 尚不存在，请先执行 `build-story-bible`
- 仅修改某个角色的某个字段（使用文本编辑工具直接修改更合适）

---

## Inputs

| 输入 | 来源 | 必填 |
|------|------|------|
| `full_script.md` | `projects/{id}/script/full_script.md` | 是 |
| `metadata.json` | `projects/{id}/metadata.json` | 是（获取 `visual_style`） |
| 用户补充信息（如"女主是红发"） | 用户请求 | 否 |

---

## Outputs

| 产物 | 路径 | 说明 |
|------|------|------|
| `character_bible.md` | `projects/{id}/characters/character_bible.md` | 所有角色设定 |
| `scene_bible.md` | `projects/{id}/scenes/scene_bible.md` | 核心场景设定（3集以上） |
| `prop_bible.md` | `projects/{id}/props/prop_bible.md` | 核心道具设定 |

### character_bible.md 结构

```markdown
# 角色设定集

## 主要角色

### 角色1：[名字]
- **全名**：
- **年龄**：
- **性别**：
- **身高/体重**：
- **外貌特征**：
  - 发型/发色：
  - 瞳色：
  - 体型：
  - 标志性特征：
- **服装设计**：
  - 日常服装：
  - 战斗/特殊服装：（如有）
- **性格特点**：
- **口头禅**：
- **背景故事**：[100字]
- **角色弧光**：[在25集中的成长变化]
- **AI绘图关键词（英文）**：[用于生成角色一致性的 Prompt，仅描述外貌特征，不含风格后缀]

## 次要角色
...

## 角色关系图
[文字描述角色间的关系网络]
```

### scene_bible.md 结构

```markdown
# 场景设定集

## 场景1：[场景名称]
- **场景ID**：scene_01
- **场景描述**：[50-100字，描述物理空间、装饰、氛围]
- **出现集数**：EP01, EP02, EP05...
- **关键视觉元素**：[标志性物件、色调、灯光]
- **AI绘图关键词（英文）**：[空间布局、光影、陈设风格，不含风格后缀]

## 场景2：...
```

### prop_bible.md 结构

```markdown
# 道具设定集

## 道具1：[道具名称]
- **道具ID**：prop_01
- **道具描述**：[30-50字，描述外观、材质、尺寸]
- **出现集数**：EP10, EP12, EP25...
- **剧情意义**：[此道具的象征/功能意义]
- **AI绘图关键词（英文）**：[材质、颜色、形状、细节，不含风格后缀]

## 道具2：...
```

---

## Constraints

### 角色设定约束

1. **AI 绘图关键词必须为英文**，描述外貌特征和服装，不包含 `visual_style.prompt_suffix`
2. **角色 ID 命名**：使用角色中文名（不使用 ID 编号），与 `referenceFiles` 路径一致（`characters/{角色名}_ref.png`）
3. **主次角色分层**：主要角色（贯穿全剧）与次要角色（仅在特定集出现）分开列写

### 场景设定约束

1. **筛选门槛**：只收录在 **3集以上** 反复出现的场景；一次性场景不建参考图
2. **场景 ID 格式**：`scene_01`, `scene_02`…，两位数字，与 `storyboard_config.json` 中的 `scene_refs` 保持一致
3. **AI 绘图关键词必须为英文**，不包含 `prompt_suffix`
4. **通常数量**：一部 25 集短剧有 3-6 个核心场景

### 道具设定约束

1. **筛选原则**：只收录具有剧情推动或象征意义的道具（信物、关键文件、标志性物品），不收录日常物件
2. **道具 ID 格式**：`prop_01`, `prop_02`…，两位数字，与 `storyboard_config.json` 中的 `prop_refs` 保持一致
3. **AI 绘图关键词必须为英文**，不包含 `prompt_suffix`
4. **允许为空**：若剧情无核心道具，`prop_bible.md` 可只含标题和空说明
5. **通常数量**：一部 25 集短剧有 2-5 个核心道具

### 所有圣经文件的共同约束

- `AI绘图关键词（英文）` 字段必须存在且非空
- 关键词不包含 `visual_style.prompt_suffix`（风格后缀由 `generate-media` 在生成时注入）

---

## Workflow

### Step 1：读取输入文件

读取 `full_script.md` 和 `metadata.json`，分析剧情结构、角色列表、场景列表、道具列表。

### Step 2：角色设计

1. 从剧本中提取所有出场角色（含次要角色）
2. 为每个角色生成完整设定（外貌、性格、背景、弧光）
3. 为每个角色撰写英文 AI 绘图关键词
4. 生成角色关系图（文字描述）
5. 写入 `characters/character_bible.md`

### Step 3：场景设计

1. 从剧本中统计各场景的出现集数
2. 筛选出现 3 集以上的核心场景
3. 为每个场景分配 `scene_id`（scene_01 起）
4. 撰写英文 AI 绘图关键词（强调空间构成、光影特征）
5. 写入 `scenes/scene_bible.md`

### Step 4：道具设计

1. 从剧本中识别具有剧情意义的道具
2. 为每个道具分配 `prop_id`（prop_01 起）
3. 撰写英文 AI 绘图关键词（强调材质、细节）
4. 写入 `props/prop_bible.md`（若无道具，写空文件）

---

## Checklist

- [ ] `full_script.md` 已读取
- [ ] `metadata.json` 已读取（获取 `visual_style` 供上下文参考）
- [ ] 所有主要/次要角色均已在 `character_bible.md` 中定义
- [ ] 每个角色均有 `AI绘图关键词（英文）` 字段
- [ ] 场景已按出现频次筛选（≥3集才收录）
- [ ] 每个场景均有 `scene_id`（格式 `scene_XX`）和 AI 绘图关键词
- [ ] 道具已按剧情意义筛选
- [ ] 每个道具均有 `prop_id`（格式 `prop_XX`）和 AI 绘图关键词
- [ ] `prop_bible.md` 已创建（即使为空也必须存在）
- [ ] 所有 AI 绘图关键词均为英文，不含 `prompt_suffix` 风格后缀

---

## Failure Modes

| 错误场景 | 处理方式 |
|---------|---------|
| `full_script.md` 不存在 | **阻断执行**，提示先运行 `build-story-bible` |
| `metadata.json` 不存在 | **阻断执行**，提示先运行 `init-drama-project` |
| 某角色缺少 AI 绘图关键词 | 自动补全，警告用户检查质量 |
| 场景 ID 与已有 `storyboard_config.json` 冲突 | 警告用户，建议以 `scene_bible.md` 中的 ID 为准 |
| 道具圣经已存在 | 警告将覆盖，等待确认 |
| 角色数量为0 | **阻断执行**，剧本中必须至少定义1个角色 |
