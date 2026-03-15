# Skill 映射文档

> **版本**：v1.0
> **日期**：2026-03-15
> **目的**：记录 legacy `produce-anime` SKILL.md 各章节到新 skill 文件的迁移关系，
> 确保重构可追溯、无内容遗漏。

---

## 一、Legacy 技能概览

| Legacy 技能文件 | 职责 | 问题 |
|---------------|------|------|
| `.claude/skills/produce-anime/SKILL.md` | Stage 1（步骤1-6）+ Stage 3（步骤7） | God Skill，阶段边界混淆 |
| `.claude/skills/submit-anime-project/SKILL.md` | Stage 4 任务提交 | 职责单一，保留 |
| `.claude/skills/generate-media/SKILL.md` | Stage 2 媒体生成 | 职责单一，保留 |

---

## 二、Legacy 章节 → 新 Skill 映射表

### produce-anime/SKILL.md 各章节迁移

| Legacy 章节 | 行范围（约） | 迁移到新 Skill | 备注 |
|------------|-----------|--------------|------|
| **第一步：初始化项目**（目录创建、编号分配） | 61–88 | `skills/project/init-drama-project.md` | 步骤1 完整迁移 |
| **视觉风格预设**（visual_styles.json 读取规则） | 29–55 | `skills/project/init-drama-project.md` | 风格选择属于初始化阶段 |
| **第六步：更新全局索引**（projects/index.json 更新） | 441–462 | `skills/project/init-drama-project.md` | 合并到初始化流程 |
| **第二步：剧本编写**（full_script.md 结构） | 90–119 | `skills/story/build-story-bible.md` | 完整迁移 |
| **内容创作规范 - 剧本要求**（叙事结构约束） | 570–581 | `skills/story/build-story-bible.md` | 叙事弧度约束迁移 |
| **第三步：角色设计**（character_bible.md 结构） | 121–154 | `skills/production/build-production-bibles.md` | 步骤3 完整迁移 |
| **第三步B：场景设计**（scene_bible.md 结构） | 156–175 | `skills/production/build-production-bibles.md` | 步骤3B 完整迁移，含3集门槛规则 |
| **第三步C：道具设计**（prop_bible.md 结构） | 177–194 | `skills/production/build-production-bibles.md` | 步骤3C 完整迁移 |
| **第四步：逐集生成内容**（dialogue.md 格式） | 196–228 | `skills/episode/build-episode-pack.md` | 对话格式迁移 |
| **第四步：逐集生成内容**（storyboard_config.json 完整结构） | 228–370 | `skills/episode/build-episode-pack.md` | 9宫格分镜格式完整迁移 |
| **第五步：生成视频编号管理索引**（video_index.json 结构） | 389–439 | `skills/episode/build-episode-pack.md` | 步骤5 迁移，含 status="scripted" 写入规则 |
| **9宫格分镜布局说明**（时间区间定义） | 374–386 | `skills/episode/build-episode-pack.md` | 9格时间分配表迁移 |
| **内容创作规范 - 对话要求** | 582–587 | `skills/episode/build-episode-pack.md` | 对话约束迁移 |
| **内容创作规范 - 9宫格分镜要求** | 588–597 | `skills/episode/build-episode-pack.md` | 分镜约束迁移 |
| **第七步：生成 Seedance 任务**（完整 Step 7 逻辑） | 464–548 | `skills/delivery/build-seedance-project-tasks.md` | 步骤7 完整迁移（核心拆分点） |
| **7.1 seedance_project_tasks.json 格式** | 474–508 | `skills/delivery/build-seedance-project-tasks.md` | 任务格式迁移 |
| **7.2 prompt 构建规则**（5条规则） | 512–543 | `skills/delivery/build-seedance-project-tasks.md` | Prompt 构建完整迁移 |
| **编号规则**（DM-XXX, EPxx, video_id 格式） | 551–564 | `skills/project/init-drama-project.md` + `skills/episode/build-episode-pack.md` | 编号规则分发到各相关 skill |
| **执行检查清单 - 阶段1** | 630–645 | `skills/review/review-drama-package.md` | 迁移为 QA review 技能的检查步骤 |
| **执行检查清单 - 阶段3** | 647–657 | `skills/delivery/build-seedance-project-tasks.md` | 迁移为任务组装技能的 checklist |
| **运行指令**（触发词列表） | 607–623 | 保留在 legacy SKILL.md（用于触发词匹配） | 不迁移，legacy 继续维护触发词 |
| **输出示例** | 663–699 | 保留在 legacy SKILL.md（参考） | 示例不迁移 |

### submit-anime-project/SKILL.md 迁移

| Legacy 章节 | 迁移到新 Skill | 备注 |
|------------|--------------|------|
| Gate 检查逻辑 | `skills/governance/stage-gate-checker.md` | submit-project Gate 条件提取 |
| base64 展开逻辑 | **保留在原 SKILL.md** | 提交技能的核心逻辑，不迁移 |
| submission_report.json 格式 | **保留在原 SKILL.md** | 提交技能专有产物 |

---

## 三、新 Skill 文件清单

| 新 Skill 文件 | 对应阶段 | 来源 |
|-------------|---------|------|
| `skills/project/init-drama-project.md` | Stage 1 初始化 | produce-anime 步骤1、6 |
| `skills/story/build-story-bible.md` | Stage 1 剧本 | produce-anime 步骤2 |
| `skills/production/build-production-bibles.md` | Stage 1 设计 | produce-anime 步骤3、3B、3C |
| `skills/episode/build-episode-pack.md` | Stage 1 集内容 | produce-anime 步骤4、5 |
| `skills/delivery/build-seedance-project-tasks.md` | Stage 3 任务组装 | produce-anime 步骤7（核心拆分） |
| `skills/review/review-drama-package.md` | QA（Stage 1 后） | produce-anime 阶段1检查清单 |
| `skills/governance/stage-gate-checker.md` | 治理（Gate 验证） | stage-model.md Gate 条件 |
| `skills/governance/artifact-contract-enforcer.md` | 治理（格式验证） | artifact-contracts.md 契约 |

---

## 四、关键拆分决策说明

### 拆分点1：步骤7 从 produce-anime 分离

**原因**：步骤7（生成 `seedance_project_tasks.json`）在逻辑上属于 Stage 3，但在 legacy 中
被嵌入 Stage 1 的技能文件。这创造了隐含的时序依赖：用户必须记住"在 generate-media 之后
运行 produce-anime 的步骤7"，且无任何机制防止在媒体未生成时触发步骤7。

**解决方案**：提取为独立的 `build-seedance-project-tasks` 技能，将 `media_ready` 状态
检查作为 Gate 条件，彻底消除时序歧义。

### 拆分点2：引入治理技能层

`review-drama-package`、`stage-gate-checker`、`artifact-contract-enforcer` 均为
新引入的治理类技能，在 legacy 系统中没有直接对应的章节，但其验收标准来自：
- `produce-anime` 的执行检查清单（Stage 1 自查部分）
- `docs/stage-model.md` 的 Gate 条件定义
- `docs/artifact-contracts.md` 的契约规范

### 拆分点3：步骤1 和步骤6 合并

步骤6（更新全局索引）在逻辑上是初始化的完成标志，因此合并到
`init-drama-project` 中，而非单独保留为一个步骤。

---

## 五、Legacy Skill 的处置

| Legacy 文件 | 处置方式 |
|------------|---------|
| `.claude/skills/produce-anime/SKILL.md` | **保留不删除**。legacy 触发词仍有效；步骤7 内容标注为 `(Deprecated: 使用 build-seedance-project-tasks 代替)` |
| `.claude/skills/generate-media/SKILL.md` | **保留不变**，职责单一 |
| `.claude/skills/submit-anime-project/SKILL.md` | **保留不变**，职责单一 |
| `.claude/skills/produce-mv/SKILL.md` | **保留不变**，后续迭代中与本次拆分对齐 |

---

## 六、覆盖完整性验证

| produce-anime 原始步骤 | 新 Skill 覆盖 | 覆盖状态 |
|---------------------|------------|---------|
| 步骤1：初始化项目 | `init-drama-project` | ✅ 完整覆盖 |
| 步骤2：剧本编写 | `build-story-bible` | ✅ 完整覆盖 |
| 步骤3：角色设计 | `build-production-bibles` | ✅ 完整覆盖 |
| 步骤3B：场景设计 | `build-production-bibles` | ✅ 完整覆盖 |
| 步骤3C：道具设计 | `build-production-bibles` | ✅ 完整覆盖 |
| 步骤4：逐集生成内容 | `build-episode-pack` | ✅ 完整覆盖 |
| 步骤5：视频编号索引 | `build-episode-pack` | ✅ 完整覆盖 |
| 步骤6：更新全局索引 | `init-drama-project` | ✅ 完整覆盖（合并） |
| 步骤7：Seedance 任务生成 | `build-seedance-project-tasks` | ✅ 完整覆盖（核心拆分） |
| 执行检查清单（Stage 1） | `review-drama-package` | ✅ 完整覆盖 |
| 执行检查清单（Stage 3） | `build-seedance-project-tasks` | ✅ 完整覆盖 |
| 编号规则 | `init-drama-project` + `build-episode-pack` | ✅ 分发覆盖 |
| 叙事结构约束 | `build-story-bible` | ✅ 完整覆盖 |
| 9宫格分镜格式约束 | `build-episode-pack` | ✅ 完整覆盖 |
| Prompt 构建规则（7.2） | `build-seedance-project-tasks` | ✅ 完整覆盖 |
| Gate 条件（stage-model.md） | `stage-gate-checker` | ✅ 完整覆盖 |
| Artifact Contracts | `artifact-contract-enforcer` | ✅ 完整覆盖 |
