# Skill 文档统一模板标准

> **版本**：v1.0
> **日期**：2026-03-15
> **适用范围**：`skills/**` 目录下所有新建的 markdown skill 文件

---

## 一、Frontmatter 规范

所有 skill 文件必须以 YAML frontmatter 开头，包含以下 **4 个必填字段**：

```yaml
---
name: skill-name-in-kebab-case
description: >
  一句话到三句话概括该技能的职责。
  使用中文。如涉及 legacy 技能的迁移来源，在此注明。
category: <见合法值表>
version: "1.0"
---
```

### 字段说明

| 字段 | 类型 | 合法值 / 格式规则 |
|------|------|-----------------|
| `name` | string | kebab-case，与文件名一致（不含 `.md`） |
| `description` | multiline string | 中文，使用 YAML `>` 折叠标量，简洁描述职责 |
| `category` | string | 见下表 |
| `version` | string | 带引号的语义版本，如 `"1.0"`、`"1.1"` |

### category 合法值

| 值 | 说明 | 对应目录 |
|----|------|---------|
| `project` | 项目初始化类技能 | `skills/project/` |
| `story` | 剧本/叙事创作类技能 | `skills/story/` |
| `production` | 角色/场景/道具设计类技能 | `skills/production/` |
| `episode` | 集内容生成类技能 | `skills/episode/` |
| `delivery` | 任务组装/交付类技能 | `skills/delivery/` |
| `review` | QA 审查类技能 | `skills/review/` |
| `governance` | 治理/验证类技能 | `skills/governance/` |

---

## 二、正文结构规范

Frontmatter 之后，正文必须按以下**固定顺序**排列 9 个二级章节：

```markdown
# {技能可读名称（中文或英文均可，与 name 字段对应）}

## Purpose

## When to Use

## When Not to Use

## Inputs

## Outputs

## Constraints

## Workflow

## Checklist

## Failure Modes
```

### 章节命名规则

- 使用**英文 Title Case**（首字母大写）
- 不使用下划线或小写（`## purpose` / `## when_to_use` 均为**错误**格式）
- 章节之间以 `---` 水平分隔线隔开（可选，建议保留以增强可读性）

---

## 三、各章节内容规范

### `## Purpose`

**必填。** 1-5 句话说明该技能的核心职责和价值。

要点：
- 明确该技能**做什么**，以及**产出什么**
- 可列出主要输出产物
- 如果该技能是只读（不写文件），必须在此明确说明

示例：
```markdown
## Purpose

基于已初始化的项目元数据，生成 `script/full_script.md`，建立整部作品的叙事基础。
本技能产出是后续角色设计和集内容生成的唯一叙事来源。
```

---

### `## When to Use`

**必填。** 列举触发该技能的典型场景（bullet list）。

要点：
- 列出 2-5 个具体触发条件
- 可包含用户自然语言触发词，和/或前置状态条件

---

### `## When Not to Use`

**必填。** 列举不应触发该技能的情况（bullet list）。

要点：
- 明确排除场景，避免误用
- 如有替代技能，在此指引（"请使用 `xxx` 代替"）

---

### `## Inputs`

**必填。** 以表格列出所有输入项。

**标准表格格式**：

```markdown
| 输入 | 来源 | 必填 |
|------|------|------|
| `metadata.json` | 文件系统 | 是 |
| 用户描述（类型/风格） | 用户请求 | 否 |
```

要点：
- 区分「文件系统输入」和「用户交互输入」
- 必填列明确标注"是"或"否（默认值说明）"

---

### `## Outputs`

**必填。** 以表格列出所有输出产物，并提供结构示例。

**标准表格格式**：

```markdown
| 产物 | 路径 | 说明 |
|------|------|------|
| `metadata.json` | `projects/{id}/metadata.json` | 作品元数据 |
```

要点：
- 路径使用相对路径（相对于项目根目录或 skills 根目录）
- 对于复杂结构，在表格下方附上 JSON/Markdown 结构示例（使用 ` ```json ` 代码块）
- 只读技能（不写文件）：明确写"本技能不写入任何文件，仅输出报告至控制台"

---

### `## Constraints`

**必填。** 列出执行该技能时必须遵守的所有约束规则。

建议按类别分组（`### 约束类别名称`），每条约束编号或加粗以便引用。

要点：
- 业务约束（如"25集"、"subtitle 必须为 false"）
- 格式约束（如"ai_image_prompt 必须为英文"）
- Gate 检查约束（如有，列出 BLOCKING 和 WARNING 的表格）

---

### `## Workflow`

**必填。** 按步骤列出执行流程（`### Step N：步骤名称`）。

要点：
- 每个 Step 有独立的 `### Step N` 子标题
- 每步包含具体操作，不要只写"处理数据"这类模糊描述
- 如有条件分支，用 bullet list + 缩进表达

示例：
```markdown
### Step 1：读取元数据

读取 `metadata.json`，确认 `project_id`、`visual_style`。

### Step 2：生成内容

- 若用户指定了集数范围，仅处理指定范围
- 若未指定，处理 EP01–EP25 全部 25 集
```

---

### `## Checklist`

**必填。** 以 GitHub Flavored Markdown 任务列表格式列出完成前的自查清单。

```markdown
## Checklist

- [ ] `metadata.json` 已读取，`project_id` 已确认
- [ ] 所有 25 集 `dialogue.md` 已生成
- [ ] `video_index.json` 的 `status = "scripted"`
```

要点：
- 每条以 `- [ ]` 开头（使用空白任务框，表示待检查状态）
- 项目数量：5-15 项为宜，不要过于简略也不要过于细碎
- 顺序与 Workflow 步骤对应

---

### `## Failure Modes`

**必填。** 以表格列出已知失败场景及其处理方式。

**标准表格格式**：

```markdown
| 错误场景 | 处理方式 |
|---------|---------|
| `metadata.json` 不存在 | **阻断执行**，提示先运行 `init-drama-project` |
| 某集 `storyboard_9grid` 不足 9 格 | **阻断执行**，该集重新生成直到达到 9 格 |
| 场景参考图缺失 | 警告，降级为纯文字描述（不阻断） |
```

要点：
- 区分**阻断性**（粗体 `**阻断执行**`）和**警告性**（"警告，…"）处理
- 覆盖该技能特有的失败场景，通用错误（如文件权限）可忽略

---

## 四、文件命名规范

| 规则 | 示例 |
|------|------|
| kebab-case，全小写 | `build-story-bible.md` ✅ |
| 单词间用连字符 `-` | `init-drama-project.md` ✅ |
| 不用下划线 | `build_story_bible.md` ❌ |
| 不用驼峰 | `buildStoryBible.md` ❌ |
| 动词开头（动作明确） | `build-`、`init-`、`review-`、`stage-gate-` ✅ |

---

## 五、完整模板示例

以下为一个符合规范的最小完整 skill 文件：

````markdown
---
name: example-skill
description: >
  示例技能，展示标准模板格式。
category: project
version: "1.0"
---

# example-skill

## Purpose

本技能用于演示统一 skill 文档格式。执行后生成 `example_output.json`。

---

## When to Use

- 用户请求执行示例任务时
- `prerequisite.json` 已存在且 `status = "ready"`

---

## When Not to Use

- `prerequisite.json` 尚不存在，请先运行 `init-example`

---

## Inputs

| 输入 | 来源 | 必填 |
|------|------|------|
| `prerequisite.json` | 文件系统 | 是 |
| 用户参数 | 用户请求 | 否 |

---

## Outputs

| 产物 | 路径 | 说明 |
|------|------|------|
| `example_output.json` | 项目根目录 | 示例输出文件 |

---

## Constraints

1. **输入文件必须存在**：`prerequisite.json` 缺失时阻断执行
2. **输出格式**：必须为合法 JSON

---

## Workflow

### Step 1：读取输入

读取 `prerequisite.json`，验证格式。

### Step 2：生成输出

按约束生成 `example_output.json`。

---

## Checklist

- [ ] `prerequisite.json` 已读取并验证
- [ ] `example_output.json` 已写入
- [ ] 输出格式为合法 JSON

---

## Failure Modes

| 错误场景 | 处理方式 |
|---------|---------|
| `prerequisite.json` 不存在 | **阻断执行**，提示先运行 `init-example` |
| 输出 JSON 格式非法 | **阻断执行**，重新生成 |
````

---

## 六、版本管理

- `version: "1.0"`：新建技能的起始版本
- `version: "1.1"`：内容修订但接口兼容（新增字段、扩展约束等）
- `version: "2.0"`：接口破坏性变更（输入/输出字段重命名、流程重构等）

---

## 七、当前 Skill 文件清单

> 最后更新：2026-03-15

| 文件 | name | category | version |
|------|------|---------|---------|
| `skills/project/init-drama-project.md` | `init-drama-project` | `project` | `1.0` |
| `skills/story/build-story-bible.md` | `build-story-bible` | `story` | `1.0` |
| `skills/production/build-production-bibles.md` | `build-production-bibles` | `production` | `1.0` |
| `skills/episode/build-episode-pack.md` | `build-episode-pack` | `episode` | `1.0` |
| `skills/delivery/build-seedance-project-tasks.md` | `build-seedance-project-tasks` | `delivery` | `1.0` |
| `skills/review/review-drama-package.md` | `review-drama-package` | `review` | `1.0` |
| `skills/governance/stage-gate-checker.md` | `stage-gate-checker` | `governance` | `1.0` |
| `skills/governance/artifact-contract-enforcer.md` | `artifact-contract-enforcer` | `governance` | `1.0` |
