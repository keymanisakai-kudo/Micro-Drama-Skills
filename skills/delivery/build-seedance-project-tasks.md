---
name: build-seedance-project-tasks
description: >
  读取全部25集的 storyboard_config.json 和 dialogue.md，结合已生成的媒体文件
  （角色/场景/道具参考图、9宫格分镜图），组装 seedance_project_tasks.json（50条任务）。
  对应 produce-anime 的 Step 7（生成 Seedance 任务）。
  此技能必须在 generate-media 完成后（status = "media_ready"）才能执行。
category: delivery
version: "1.0"
---

# build-seedance-project-tasks

## Purpose

读取前期制作产物 + 媒体生成产物，按固定规则构建 50 条 Seedance 视频生成任务，
写入项目根目录的 `seedance_project_tasks.json`。

每条任务包含：
- 完整的 `prompt`（4段固定结构，含标准排除指令和9条逐镜头描述）
- `referenceFiles`（相对路径字符串数组，不含 base64）
- `modelConfig`（默认为 Seedance 2.0 Fast）
- `tags`、`realSubmit`、`priority` 等元数据

---

## When to Use

- `video_index.json` 的 `status = "media_ready"`（通过 `stage-gate-checker` 验证）
- `media_index.json` 存在且所有 50 张分镜图均 `exists = true`
- 需要重新组装任务（用户确认覆盖后）

---

## When Not to Use

- `video_index.json` 的 `status` 为 `"scripted"` 或 `"media_pending"`（媒体尚未生成）
- `media_index.json` 不存在
- 任何分镜图缺失（`media_index.json` 中有 `exists: false` 条目）

---

## Inputs

### 必须存在的文件（缺失则阻断执行）

| 文件 | 路径 | 说明 |
|------|------|------|
| `video_index.json` | 项目根目录 | `status` 必须为 `"media_ready"` |
| `media_index.json` | 项目根目录 | 所有 50 张分镜图 `exists = true` |
| `storyboard_config.json` × 25 | `episodes/EPxx/` | 9宫格分镜配置 |
| `dialogue.md` × 25 | `episodes/EPxx/` | 对话脚本 |
| 角色参考图 | `characters/{角色名}_ref.png` | 每角色1张 |
| 分镜参考图 | `episodes/EPxx/{video_id}_storyboard.png` | 共50张 |
| `characters/ref_index.json` | `characters/` | 角色名 → 图片路径映射 |

### 可选存在的文件（缺失则降级处理）

| 文件 | 路径 | 缺失时行为 |
|------|------|-----------|
| 场景参考图 | `scenes/{scene_id}_ref.png` | 警告，相关集的场景引用降级为纯文字 |
| 道具参考图 | `props/{prop_id}_ref.png` | 警告，相关集的道具引用降级为纯文字 |

---

## Outputs

| 产物 | 路径 | 说明 |
|------|------|------|
| `seedance_project_tasks.json` | 项目根目录 | 50条任务，`total_tasks = 50` |
| `video_index.json`（状态更新） | 项目根目录 | `status` 更新为 `"tasks_assembled"` 或 `"ready_to_submit"` |

### seedance_project_tasks.json 结构

```json
{
  "project_id": "DM-001",
  "project_name": "作品名称",
  "total_tasks": 50,
  "created_date": "YYYY-MM-DD",
  "tasks": [
    {
      "prompt": "...",
      "description": "DM-001 EP01 Part-A 「集标题」上半部分 9宫格分镜→视频",
      "modelConfig": {
        "model": "Seedance 2.0 Fast",
        "referenceMode": "全能参考",
        "aspectRatio": "16:9",
        "duration": "15s"
      },
      "referenceFiles": [
        "episodes/EP01/DM-001-EP01-A_storyboard.png",
        "characters/角色A_ref.png",
        "characters/角色B_ref.png"
      ],
      "realSubmit": false,
      "priority": 1,
      "tags": ["DM-001", "EP01", "A"]
    }
  ]
}
```

**任务排列顺序**：EP01-A, EP01-B, EP02-A, EP02-B, ..., EP25-A, EP25-B（共50条）

---

## Constraints

### Gate 检查（阻断性，任意一项失败则立即中止）

| # | 检查项 | 失败消息 |
|---|--------|---------|
| B1 | `video_index.json` 必须存在 | `[BLOCK] video_index.json 不存在，请先运行 produce-anime 完成前期制作` |
| B2 | `video_index.json.status` 必须为 `"media_ready"` | `[BLOCK] 当前状态为 "{status}"，需要 status = "media_ready"，请先运行 generate-media` |
| B3 | `media_index.json` 必须存在 | `[BLOCK] media_index.json 不存在，请先运行 generate-media` |
| B4 | 所有50张分镜图 `exists = true` | `[BLOCK] {N}张分镜图缺失：{list}，请重新运行 generate-media` |
| B5 | 角色参考图全部存在 | `[BLOCK] 以下角色参考图缺失：{list}，请重新运行 generate-media` |
| B6 | 所有25个 `storyboard_config.json` 存在 | `[BLOCK] {N}个 storyboard_config.json 缺失` |
| B7 | 所有25个 `dialogue.md` 存在 | `[BLOCK] {N}个 dialogue.md 缺失` |

### 警告检查（不阻断，但标记受影响任务）

| # | 检查项 | 警告消息 | 处理方式 |
|---|--------|---------|---------|
| W1 | 场景参考图是否全部存在 | `[WARN] 场景参考图缺失：{list}` | 相关集 prompt 降级为纯文字描述 |
| W2 | 道具参考图是否全部存在 | `[WARN] 道具参考图缺失：{list}` | 相关集 prompt 降级为纯文字描述 |
| W3 | `seedance_project_tasks.json` 是否已存在 | `[WARN] 已存在 tasks 文件（创建于 {date}），将被覆盖` | 等待确认后覆盖 |

受警告影响的任务，在 `tags` 数组中追加 `"incomplete_refs"` 标记。

### prompt 构建规则（4段固定顺序）

**Segment 1：头部声明**（仅分镜图和角色参考图，不含场景/道具）
```
(@{project_id}-EPxx-{A|B}_storyboard.png) 为9宫格分镜参考图，(@{角色名}_ref.png) 为角色「{角色名}」的参考形象，...
```
- 仅列出本 Part 出场的角色（基于 `storyboard_9grid` 中的 `characters` 字段去重）
- 场景和道具参考图**不在头部声明**，在 Segment 3 内联

**Segment 2：标准排除指令**（固定文本，一字不差）
```
从镜头1开始，不要展示多宫格分镜参考图片。分镜图制作成电影级别的高清影视级别的视频。严禁参考图出现在画面中。每个画面为单一画幅，独立展示，没有任何分割线或多宫格效果画面。(Exclusions); Do not show speech bubbles, do not show comic panels, remove all text, full technicolor.排除项: No speech bubbles(无对话气泡),No text(无文字), No comic panels(无漫画分镜),No split screen(无分屏),No monochrome(非单色/黑白),No manga effects(无漫画特效线).正向替代:Fullscreen(全屏),Single continuous scene(单一连续场景).表情、嘴型、呼吸、台词严格同步。去掉图片中的水印，不要出现任何水印。没有任何字幕。
```

**Segment 3：集信息行 + 场景/道具内联引用**
```
{video_id} 第X集「{episode_title}」{上/下}半部分。{synopsis}。 氛围：{atmosphere.overall_mood}。 场景参考 (@{scene_id}_ref.png)。道具参考 (@{prop_id}_ref.png)。
```
- 有场景参考图时：`(@{scene_id}_ref.png)` 内联
- 无场景参考图时：省略场景参考段
- 场景/道具不需要额外说明"为XXX的参考图"

**Segment 4：逐镜头描述**（基于 `storyboard_9grid` 的9条 GridItem）
```
镜头N(time_start-time_end): 第X集{上/下}半第N格：{scene_description}。{camera.movement}{camera.type}{camera.angle}。{atmosphere}。 音效:{sfx}。 (@{角色名}_ref.png){角色名}{action}，表情{expression}。 (@{角色名}_ref.png){角色名}说："{dialogue.text}"（{dialogue.emotion}）
```
- 每个出场角色前缀 `(@{角色名}_ref.png)`
- 旁白格式：`旁白，{emotion}："{text}"`
- 无对话的角色仅描述动作和表情

### referenceFiles 构建规则

```
[
  "episodes/EPxx/{project_id}-EPxx-{A|B}_storyboard.png",  // 必须放第一位
  "characters/{角色名}_ref.png",  // 本Part出场的角色，按出场顺序，去重
  "scenes/{scene_id}_ref.png",  // 本Part涉及且图片存在的场景参考图
  "props/{prop_id}_ref.png"  // 本Part涉及且图片存在的道具参考图
]
```

**关键约束**：`referenceFiles` 中的所有条目必须是**相对路径字符串**，不得是 base64 对象。base64 展开由 `submit-project` 在提交时负责。

---

## Workflow

### Step 1：执行 Gate 检查（B1-B7）

按顺序执行所有阻断检查，任意一项失败则立即输出错误消息并停止。

### Step 2：执行警告检查（W1-W3）

输出所有警告，但继续执行。

### Step 3：逐集组装任务（EP01-EP25，每集生成 A 和 B 两条）

对每集每个 Part：
1. 读取 `storyboard_config.json` 的对应 Part 数据
2. 确定本 Part 出场角色列表（从 `storyboard_9grid` 的 `characters` 字段去重）
3. 构建 `referenceFiles` 数组（分镜图 → 角色图 → 场景图 → 道具图）
4. 构建 `prompt`（4段顺序：头部声明 → 排除指令 → 集信息行 → 9条镜头描述）
5. 写入 Task 对象（`realSubmit: false` 为默认值）

### Step 4：验证路径完整性（4b 子步骤）

遍历所有 50 条任务的 `referenceFiles`，检查每条路径是否真实存在于磁盘。

### Step 5：写入 seedance_project_tasks.json

写入项目根目录，`total_tasks = 50`，任务顺序为 EP01-A, EP01-B, ..., EP25-A, EP25-B。

### Step 6：更新 video_index.json status

- 路径完整性验证**全部通过**：`status = "ready_to_submit"`
- 路径完整性验证**存在失败**：`status = "tasks_assembled"`，在报告中列出失败条目

---

## Checklist

- [ ] `video_index.json` 存在且 `status = "media_ready"`
- [ ] `media_index.json` 存在，所有50条 `exists = true`
- [ ] 25个 `storyboard_config.json` 均存在
- [ ] 25个 `dialogue.md` 均存在
- [ ] 角色参考图全部存在（验证 `characters/ref_index.json`）
- [ ] 警告检查（场景/道具图）已执行并输出
- [ ] 所有50条任务已组装（EP01-A到EP25-B，顺序正确）
- [ ] 每条任务的 `prompt` 含标准排除指令（含关键短语 `No speech bubbles`）
- [ ] 每条任务的 `prompt` 含9条逐镜头描述（`镜头1`到`镜头9`）
- [ ] 每条任务的 `referenceFiles` 均为相对路径字符串（不含 base64）
- [ ] `referenceFiles` 路径完整性验证已执行
- [ ] `seedance_project_tasks.json` 已写入，`total_tasks = 50`
- [ ] `video_index.json` 的 `status` 已更新（`ready_to_submit` 或 `tasks_assembled`）

---

## Failure Modes

| 错误场景 | 处理方式 |
|---------|---------|
| `status ≠ "media_ready"` | **阻断执行**，显示当前状态和需要的状态 |
| 分镜图缺失 | **阻断执行**，列出所有缺失文件 |
| 角色参考图缺失 | **阻断执行**，列出所有缺失角色 |
| 场景/道具图缺失 | 警告，降级处理（不阻断） |
| `referenceFiles` 路径不存在（4b验证失败） | `status = "tasks_assembled"`，列出失败条目，不晋升到 `ready_to_submit` |
| `storyboard_9grid` 不足9条 | 警告，该集的 `prompt` 只生成实际存在的镜头数，并标记 `"incomplete_refs"` |
| 已存在 `seedance_project_tasks.json` | 警告，等待用户确认后覆盖 |
| 覆盖时当前 `status = "ready_to_submit"` | 额外警告，临时回退 `status = "tasks_assembled"`，覆盖完成后重新验证 |
