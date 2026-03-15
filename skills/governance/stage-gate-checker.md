---
name: stage-gate-checker
description: >
  在执行 assemble-tasks 或 submit-project 之前，验证项目是否满足进入下一阶段的所有
  Gate 条件（Blocking + Warning）。对应 docs/stage-model.md 中定义的阶段守门规则。
category: governance
version: "1.0"
---

# stage-gate-checker

## Purpose

作为流水线中的"守门员"，在关键阶段转换之前执行结构化验证：

1. **assemble-tasks Gate**：验证项目是否满足从 `media_ready` → `tasks_assembled` 的所有条件
2. **submit-project Gate**：验证项目是否满足从 `ready_to_submit` → `submitted` 的所有条件

本技能**只执行检查，不修改任何文件**。检查结果以结构化报告形式输出，
决定是否允许目标技能继续执行。

---

## When to Use

- 在调用 `build-seedance-project-tasks`（assemble-tasks）之前自动触发
- 在调用 `submit-project` 之前自动触发
- 用户手动请求"检查 DM-XXX 是否可以组装任务"或"是否可以提交"

---

## When Not to Use

- Stage 1 的前期制作验收——使用 `review-drama-package` 代替
- 对单个文件的格式验证——使用 `artifact-contract-enforcer` 代替

---

## Inputs

根据目标 Gate 的不同，读取不同的文件集合：

### assemble-tasks Gate 所需输入

| 文件 | 路径 |
|------|------|
| `video_index.json` | 项目根目录 |
| `media_index.json` | 项目根目录 |
| `characters/ref_index.json` | `characters/` |
| `scenes/ref_index.json` | `scenes/`（可选） |
| `props/ref_index.json` | `props/`（可选） |
| `storyboard_config.json` × 25 | `episodes/EPxx/` |
| `dialogue.md` × 25 | `episodes/EPxx/` |

### submit-project Gate 所需输入

| 文件 | 路径 |
|------|------|
| `seedance_project_tasks.json` | 项目根目录 |
| `video_index.json` | 项目根目录 |
| 所有 `referenceFiles` 中列出的文件 | 各相对路径 |

---

## Outputs

结构化 Gate 报告（控制台输出，不写入文件）：

```
=== Stage Gate 检查报告 ===
目标操作：assemble-tasks / submit-project
项目：{project_id}
当前状态：{status}
检查时间：{timestamp}

BLOCKING 检查结果：
  [PASS] B1: video_index.json 存在
  [PASS] B2: status = "media_ready"
  [FAIL] B3: media_index.json 不存在

WARNING 检查结果：
  [WARN] W1: 场景参考图缺失：scene_02_ref.png, scene_03_ref.png

=== 结论 ===
❌ BLOCKED：存在 1 项阻断性问题，禁止继续执行 assemble-tasks
  → 修复方向：运行 generate-media 重新生成缺失的媒体文件
```

---

## Constraints

本技能**只读**，不修改任何文件，不更新 `video_index.json` 的 `status`。
状态写入由对应的目标技能负责。

---

## Workflow

### assemble-tasks Gate

按以下顺序执行，任意 BLOCKING 失败则立即标记，继续检查剩余项（全部检查完后汇总报告）：

#### BLOCKING 检查

| # | 检查项 | 检查方式 |
|---|--------|---------|
| B1 | `video_index.json` 必须存在 | 文件系统检查 |
| B2 | `video_index.json.status` 必须为 `"media_ready"` | 读取 status 字段 |
| B3 | `media_index.json` 必须存在 | 文件系统检查 |
| B4 | 所有50张分镜图 `exists = true` | 读取 `media_index.storyboards[].exists` |
| B5 | 所有角色参考图路径均存在于磁盘 | 读取 `characters/ref_index.json`，逐条检查 |
| B6 | 所有25个 `storyboard_config.json` 存在 | 检查 EP01–EP25 |
| B7 | 所有25个 `dialogue.md` 存在 | 检查 EP01–EP25 |

#### WARNING 检查

| # | 检查项 | 检查方式 |
|---|--------|---------|
| W1 | 所有场景参考图路径存在 | 读取 `scenes/ref_index.json`（若存在），逐条检查 |
| W2 | 所有道具参考图路径存在 | 读取 `props/ref_index.json`（若存在），逐条检查 |
| W3 | `seedance_project_tasks.json` 是否已存在（覆盖提醒） | 文件系统检查 |
| W4 | `media_index.json` 中是否有 `exists: false` 边缘条目 | 遍历所有字段 |

#### 结论输出

- 所有 B 检查通过：`PASS → 允许执行 assemble-tasks`
- 任意 B 检查失败：`BLOCKED → 禁止执行 assemble-tasks`，列出修复建议

---

### submit-project Gate

按以下顺序执行：

#### BLOCKING 检查

| # | 检查项 | 检查方式 |
|---|--------|---------|
| B1 | `seedance_project_tasks.json` 必须存在 | 文件系统检查 |
| B2 | `total_tasks` 必须等于 50 | 读取并比较字段值 |
| B3 | `video_index.json.status` 必须为 `"ready_to_submit"` | 读取 status 字段 |
| B4 | 所有任务的 `referenceFiles` 路径均真实存在 | 遍历50条任务的每个路径 |
| B5 | Seedance API 服务可达 | GET `{api_base}/api/config` 返回 200 |

#### WARNING 检查

| # | 检查项 | 检查方式 |
|---|--------|---------|
| W1 | 任意 task 的 `realSubmit = false` | 遍历50条任务 |
| W2 | `submission_report.json` 已存在（重复提交检测） | 文件系统检查 |
| W3 | 任意 task 的 `tags` 含 `"incomplete_refs"` | 遍历所有任务 |
| W4 | `total_tasks` 字段值与 `tasks` 数组实际长度不一致 | 比较字段值与数组长度 |

#### 结论输出

- 所有 B 检查通过：`PASS → 允许执行 submit-project`
- 任意 B 检查失败：`BLOCKED → 禁止执行 submit-project`，列出修复建议

---

## Checklist

### assemble-tasks Gate 使用此 checklist

- [ ] 已执行 B1–B7 全部阻断检查
- [ ] 已执行 W1–W4 全部警告检查
- [ ] 已输出结构化报告（含 PASS/FAIL 状态）
- [ ] 若全部 BLOCKING 通过，报告结论为 `PASS`
- [ ] 若任意 BLOCKING 失败，报告结论为 `BLOCKED` 并提供修复建议

### submit-project Gate 使用此 checklist

- [ ] 已执行 B1–B5 全部阻断检查
- [ ] 已执行 W1–W4 全部警告检查
- [ ] 已输出结构化报告
- [ ] 若全部 BLOCKING 通过，报告结论为 `PASS`
- [ ] 若任意 BLOCKING 失败，报告结论为 `BLOCKED` 并提供修复建议

---

## Failure Modes

| 错误场景 | 处理方式 |
|---------|---------|
| `video_index.json` 损坏（非法 JSON） | 报告为 B1/B2 失败，输出解析错误信息 |
| `media_index.json` 存在但 `storyboards` 数组不足50条 | 报告为 B4 失败，列出缺失的 video_id |
| `ref_index.json` 不存在 | B5 视为失败（无法验证路径），提示用户先运行 generate-media |
| Seedance API 检查超时（B5） | 报告为 BLOCKED，提示检查服务是否启动 |
| `total_tasks` 字段不存在 | B2 视为失败，报告格式异常 |
