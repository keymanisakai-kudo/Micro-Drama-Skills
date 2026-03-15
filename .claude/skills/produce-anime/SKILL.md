---
name: produce-anime
description: 短剧制作总调度器。自动按阶段执行完整短剧制作流水线：项目初始化→剧本→角色/场景/道具设计→25集分镜→QA验收→媒体生成→阶段门验证→任务组装→提交。关键词：短剧、影视、drama、剧本、分镜、storyboard、制作、角色设计。
---

# 短剧制作总调度器 (Produce Short Drama)

## 概述

本技能是短剧制作流水线的**总调度器**，按阶段自动调用各子技能完成完整制作流程。
每次运行生成 **1部完整作品**（25集，每集30秒，共50个视频片段）。

## 流水线架构

| 阶段 | 子技能 | 产出 | 自动/确认 |
|------|--------|------|----------|
| Stage 1-1 | `init-drama-project` | 项目目录 + metadata.json | 自动（风格选择除外） |
| Stage 1-2 | `build-story-bible` | script/full_script.md | 自动 |
| Stage 1-3 | `build-production-bibles` | character/scene/prop bible | 自动 |
| Stage 1-4 | `build-episode-pack` | 25集 dialogue.md + storyboard_config.json + video_index.json | 自动 |
| Stage 1-5 | `review-drama-package` | QA 审查报告 | 自动，BLOCKING 时暂停 |
| Stage 2 | `generate-media` | 角色图 + 场景图 + 道具图 + 分镜图 | **需用户确认** |
| Stage 3-1 | `stage-gate-checker` | 媒体完整性验证报告 | 自动 |
| Stage 3-2 | `build-seedance-project-tasks` | seedance_project_tasks.json（50条） | 自动 |
| Stage 4 | `submit-anime-project` | 提交到 Seedance API | **需用户确认 realSubmit** |

---

## 调度流程

### ▶ Stage 1：前期制作（全自动）

按以下顺序逐步调用子技能，每步完成后验证产物再继续：

**Step 1 → 调用 `init-drama-project`**
- 完成标志：`projects/{id}/metadata.json` 存在
- 包含：分配项目编号（DM-XXX）、确认视觉风格、创建目录结构、写入 metadata.json、更新 index.json

**Step 2 → 调用 `build-story-bible`**
- 完成标志：`script/full_script.md` 存在
- 包含：世界观（200-300字）+ 故事大纲（500字）+ 25集概要

**Step 3 → 调用 `build-production-bibles`**
- 完成标志：`characters/character_bible.md`、`scenes/scene_bible.md`、`props/prop_bible.md` 均存在
- 包含：角色设定（含英文 AI 绘图关键词）+ 核心场景（≥3集出现）+ 核心道具

**Step 4 → 调用 `build-episode-pack`（生成全部25集）**
- 完成标志：`video_index.json` 存在且 `status = "scripted"`
- 包含：每集 dialogue.md（中文对话）+ storyboard_config.json（Part A/B 各9宫格分镜）

**Step 5 → 调用 `review-drama-package`（QA 验收）**
- BLOCKING 问题存在：**暂停**，向用户输出审查报告，等待修复后重新调用 `review-drama-package`
- QA 全部通过：向用户输出 Stage 1 完成摘要，进入 Stage 2 确认

---

### ▶ Stage 2：媒体生成（需用户确认）

Stage 1 完成后，向用户展示确认信息：

```
✅ Stage 1 前期制作已完成！

📋 作品概要：{project_id} 《{project_name}》
📁 项目目录：projects/{project_id}_{slug}/
📊 待生成媒体：
   - 角色参考图：{N} 张
   - 场景四宫格图：{N} 张
   - 道具三视图：{N} 张
   - 分镜图：50 张（25集 × A/B）

⏭️ 下一步：运行 generate-media（需调用 Google Gemini API）
是否继续？
```

用户确认后 → **调用 `generate-media`**

---

### ▶ Stage 3：任务组装（全自动）

媒体生成完成后自动执行：

**Step 1 → 调用 `stage-gate-checker`**（assemble-tasks Gate）
- BLOCKED：向用户报告所有缺失文件，等待修复后重试
- PASS → 继续

**Step 2 → 调用 `build-seedance-project-tasks`**
- 完成标志：`seedance_project_tasks.json` 存在且 `total_tasks = 50`
- 包含：50条任务，每条含完整 prompt（9条逐镜头描述）+ referenceFiles（相对路径）

---

### ▶ Stage 4：提交（需用户确认）

Stage 3 完成后，向用户确认：

```
✅ Stage 3 任务组装已完成！共 50 条任务。

⚠️  提交参数确认：
   - realSubmit = false（仅预览，不产生实际提交）
   - realSubmit = true（真实提交到 Seedance，产生费用）

请选择提交模式：
```

用户确认后 → **调用 `submit-anime-project`**

---

## 断点续传

如项目已存在，根据 `video_index.json.status` 自动从中断点恢复：

| status | 恢复入口 |
|--------|---------|
| 不存在 | 从 Stage 1-1（`init-drama-project`）开始 |
| `scripted` | 从 Stage 2（`generate-media`）确认开始 |
| `media_pending` | 继续 Stage 2（`generate-media`） |
| `media_ready` | 从 Stage 3-1（`stage-gate-checker`）开始 |
| `tasks_assembled` | 从 Stage 4（`submit-anime-project`）确认开始 |
| `ready_to_submit` | 从 Stage 4（`submit-anime-project`）确认开始 |

---

## 运行指令

- "制作一部短剧"
- "生成短剧作品"
- "produce short drama"
- "创建新短剧"
- "开始制作短剧"

可附带参数：
- **题材/类型**：如 "制作一部科幻短剧"、"校园恋爱"
- **视觉风格**：如 "港风复古"、"Cinematic Film"、"风格7"
- **角色数量**：如 "主角3人"

如用户未指定题材，随机选择原创题材。
如用户未指定视觉风格，在 `init-drama-project` 阶段通过交互选择。

---

## 子技能说明

各子技能可**独立调用**，适用于重跑某阶段或针对已有项目的局部修改：

| 子技能 | 独立调用示例 |
|--------|-------------|
| `init-drama-project` | "初始化一个新短剧项目" |
| `build-story-bible` | "为 DM-003 重写剧本" |
| `build-production-bibles` | "重新设计 DM-003 的角色和场景" |
| `build-episode-pack` | "重新生成 DM-003 的第5集分镜" |
| `review-drama-package` | "帮我检查 DM-003 的前期制作质量" |
| `generate-media` | "生成 DM-003 的参考图和分镜图" |
| `stage-gate-checker` | "检查 DM-003 是否可以组装任务" |
| `build-seedance-project-tasks` | "为 DM-003 组装 Seedance 任务" |
| `artifact-contract-enforcer` | "验证 DM-003 的 storyboard_config.json 格式" |
| `submit-anime-project` | "提交 DM-003 的任务到 Seedance" |
