---
name: review-drama-package
description: >
  对已完成前期制作的短剧作品包进行全面 QA 审查，
  检查所有前期产物的完整性、格式合规性和一致性。
  适用于 Stage 1（scripted）阶段的质量验收，不依赖媒体文件。
category: review
version: "1.0"
---

# review-drama-package

## Purpose

在 `generate-media` 运行之前，对前期制作产物进行全面检查，提前发现并报告可能导致后续
流程阻断的问题。本技能是**只读检查工具**，不修改任何文件，只输出审查报告。

审查范围：
- 目录结构完整性
- `metadata.json` 格式合规
- `full_script.md` 内容完整性
- `character_bible.md`、`scene_bible.md`、`prop_bible.md` 格式和 ID 一致性
- 25集 `dialogue.md` 和 `storyboard_config.json` 完整性
- `video_index.json` 格式和内容合规
- 跨文件 ID 引用一致性

---

## When to Use

- `video_index.json` 的 `status = "scripted"` 时，运行 `generate-media` 之前
- 用户请求质量验收（"帮我检查 DM-XXX 的前期制作"）
- 任何 `storyboard_config.json` 或圣经文件被手动修改后
- `build-episode-pack` 完成后的自动 QA 步骤

---

## When Not to Use

- 检查媒体生成产物（参考图、分镜图）——使用 `stage-gate-checker` 代替
- 检查 `seedance_project_tasks.json`——使用 `artifact-contract-enforcer` 代替

---

## Inputs

| 输入 | 路径 | 必填 |
|------|------|------|
| `metadata.json` | 项目根目录 | 是 |
| `script/full_script.md` | 项目根目录 | 是 |
| `characters/character_bible.md` | 项目根目录 | 是 |
| `scenes/scene_bible.md` | 项目根目录 | 是 |
| `props/prop_bible.md` | 项目根目录 | 是 |
| `episodes/EPxx/dialogue.md` × 25 | 项目根目录 | 是 |
| `episodes/EPxx/storyboard_config.json` × 25 | 项目根目录 | 是 |
| `video_index.json` | 项目根目录 | 是 |

---

## Outputs

本技能不写入任何文件，仅输出审查报告（控制台输出或 markdown 格式）。

### 报告格式

```markdown
# 审查报告：{project_id} - {project_name}
审查时间：{timestamp}
审查阶段：Stage 1 (scripted)

## 摘要
- 通过检查：{N} 项
- 阻断性问题：{N} 项
- 警告：{N} 项

## 阻断性问题（BLOCKING）
[B1] ...
[B2] ...

## 警告（WARNING）
[W1] ...

## 通过项
✅ metadata.json 格式合规
✅ 25集 dialogue.md 全部存在
...
```

---

## Constraints

本技能**只读**，不修改任何文件。
所有发现的问题通过报告输出，最终修复由用户或相应技能执行。

---

## Workflow

### Step 1：目录结构检查

- [ ] `projects/{project_id}_{slug}/` 目录存在
- [ ] `script/`、`characters/`、`scenes/`、`props/`、`episodes/` 子目录存在
- [ ] EP01–EP25 共 25 个 episode 子目录存在

### Step 2：metadata.json 检查

- [ ] 文件存在且可解析为合法 JSON
- [ ] 必填字段存在：`project_id`、`project_name`、`total_episodes`（=25）、`visual_style`
- [ ] `visual_style` 对象含 `prompt_suffix` 字段且非空
- [ ] `total_episodes = 25`
- [ ] `video_count = 50`
- [ ] `created_date` 为合法日期格式

### Step 3：full_script.md 检查

- [ ] 文件存在且非空
- [ ] 含"各集概要"章节
- [ ] 各集概要包含 EP01–EP25 共 25 集

### Step 4：制作圣经检查

**character_bible.md**：
- [ ] 文件存在且非空
- [ ] 至少一个角色已定义
- [ ] 每个角色含 `AI绘图关键词（英文）` 字段且非空

**scene_bible.md**：
- [ ] 文件存在
- [ ] 每个场景有 `scene_id`（格式 `scene_XX`）
- [ ] 每个场景含 `AI绘图关键词（英文）` 字段

**prop_bible.md**：
- [ ] 文件存在（允许为空）
- [ ] 若有道具，每个道具有 `prop_id`（格式 `prop_XX`）
- [ ] 若有道具，每个道具含 `AI绘图关键词（英文）` 字段

### Step 5：dialogue.md 检查（EP01–EP25）

对每一集：
- [ ] 文件存在且非空
- [ ] 含"上半部分"和"下半部分"两个章节
- [ ] 对话内容为中文（无英文对话）
- [ ] 视频编号格式正确（`{project_id}-EPxx-A/B`）

### Step 6：storyboard_config.json 检查（EP01–EP25）

对每一集：
- [ ] 文件存在且可解析为合法 JSON
- [ ] `subtitle = false`
- [ ] `visual_style` 对象存在且含 `prompt_suffix`
- [ ] `part_a` 和 `part_b` 均存在
- [ ] `part_a.video_id` 格式为 `{project_id}-EPxx-A`
- [ ] `part_b.video_id` 格式为 `{project_id}-EPxx-B`
- [ ] `part_a.storyboard_9grid` 恰好有 9 个元素（`grid_number` 1–9）
- [ ] `part_b.storyboard_9grid` 恰好有 9 个元素（`grid_number` 1–9）
- [ ] 每个 GridItem 的 `ai_image_prompt` 为英文且非空
- [ ] `ai_image_prompt` 不含 `visual_style.prompt_suffix` 的内容

### Step 7：video_index.json 检查

- [ ] 文件存在且可解析为合法 JSON
- [ ] `status = "scripted"`
- [ ] `videos` 数组恰好有 25 条记录
- [ ] 每条记录含 `part_a.video_id` 和 `part_b.video_id`
- [ ] 所有 `video_id` 格式符合 `{project_id}-EPxx-A/B` 规范

### Step 8：跨文件 ID 一致性检查

- [ ] `storyboard_config.json` 中的 `scene_refs` 引用的 `scene_id` 均在 `scene_bible.md` 中定义
- [ ] `storyboard_config.json` 中的 `prop_refs` 引用的 `prop_id` 均在 `prop_bible.md` 中定义
- [ ] 所有文件中的 `project_id` 与 `metadata.json` 一致
- [ ] `storyboard_config.json` 中的 `visual_style` 与 `metadata.json` 中的一致

---

## Checklist

执行本技能时，按 Step 1–8 顺序逐项核对，汇总所有 BLOCKING 和 WARNING，最终输出审查报告。

---

## Failure Modes

| 错误场景 | 处理方式 |
|---------|---------|
| `metadata.json` 不存在 | 报告为阻断性问题，后续检查仍继续（跳过需要 metadata 的检查项） |
| 某集 `storyboard_config.json` 无法解析 JSON | 报告为阻断性问题，跳过该集的详细检查 |
| `video_index.json` 不存在 | 报告为阻断性问题 |
| 检查过程中遇到文件读取权限问题 | 报告错误，继续检查其他文件 |
