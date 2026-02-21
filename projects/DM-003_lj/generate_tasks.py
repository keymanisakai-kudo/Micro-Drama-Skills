#!/usr/bin/env python3
"""
生成 seedance_project_tasks.json — DM-003《绿迹》
读取所有 25 集 storyboard_config.json，构建 50 条 Seedance 任务。
"""
import json
import os
from pathlib import Path

PROJECT_DIR = Path(__file__).parent
EPISODES_DIR = PROJECT_DIR / "episodes"
CHARACTERS_DIR = PROJECT_DIR / "characters"
PROJECT_ID = "DM-003"
PROJECT_NAME = "绿迹"

# 标准排除指令（每个 prompt 必须包含）
EXCLUSION_BLOCK = (
    "从镜头1开始，不要展示多宫格分镜参考图片。"
    "分镜图制作成电影级别的高清影视级别的视频。"
    "严禁参考图出现在画面中。"
    "每个画面为单一画幅，独立展示，没有任何分割线或多宫格效果画面。"
    "(Exclusions); Do not show speech bubbles, do not show comic panels, "
    "remove all text, full technicolor."
    "排除项: No speech bubbles(无对话气泡),No text(无文字), "
    "No comic panels(无漫画分镜),No split screen(无分屏),"
    "No monochrome(非单色/黑白),No manga effects(无漫画特效线)."
    "正向替代:Fullscreen(全屏),Single continuous scene(单一连续场景)."
    "表情、嘴型、呼吸、台词严格同步。"
    "去掉图片中的水印，不要出现任何水印。没有任何字幕。"
)

# 角色名映射：storyboard 中的名字 → 实际 ref 文件名前缀
CHAR_NAME_MAP = {
    "厂长助理小周": "厂长助理",
}

# 实际存在的角色 ref 列表（无 ref 的角色不加入 referenceFiles）
EXISTING_CHAR_REFS = {"林宇", "赵建国", "苏娜", "童童", "厂长助理"}

MODEL_CONFIG = {
    "model": "Seedance 2.0 Fast",
    "referenceMode": "全能参考",
    "aspectRatio": "16:9",
    "duration": "15s"
}


def normalize_char_name(name):
    """将 storyboard 中的角色名映射到 ref 文件名前缀"""
    return CHAR_NAME_MAP.get(name, name)


def collect_part_characters(grids):
    """收集一个 part 所有 grid 中出场的角色名（去重、保序、映射后）"""
    seen = set()
    chars = []
    for g in grids:
        for c in g.get("characters", []):
            raw_name = c.get("name", "")
            name = normalize_char_name(raw_name)
            if name and name not in seen:
                seen.add(name)
                chars.append(name)
    return chars


def build_shot_line(ep_num, part_label, grid, part_chars):
    """构建单个镜头的描述行"""
    gn = grid["grid_number"]
    ts = grid.get("time_start", 0)
    te = grid.get("time_end", 0)
    sd = grid.get("scene_description", "")
    cam = grid.get("camera", {})
    cam_desc = f"{cam.get('movement', '')}{cam.get('type', '')}{cam.get('angle', '')}"
    atmo = grid.get("atmosphere", "")
    sfx = grid.get("sfx", "")

    line = f"镜头{gn}({ts}s-{te}s): 第{ep_num}集{part_label}半第{gn}格：{sd}。"
    if cam_desc.strip():
        line += f" {cam_desc}。"
    if atmo:
        line += f" {atmo}。"
    if sfx:
        line += f" 音效:{sfx}。"

    # 角色描述
    for c in grid.get("characters", []):
        raw_name = c.get("name", "")
        name = normalize_char_name(raw_name)
        if not name:
            continue
        action = c.get("action", "")
        expr = c.get("expression", "")
        if name in EXISTING_CHAR_REFS:
            line += f" (@{name}_ref.png){name}{action}，表情{expr}。"
        else:
            line += f" {name}{action}，表情{expr}。"

    # 对话
    dlg = grid.get("dialogue", {})
    speaker = dlg.get("speaker")
    text = dlg.get("text")
    emotion = dlg.get("emotion", "")

    if speaker and text:
        sp = normalize_char_name(speaker)
        if sp in ("旁白", "画外音") or "(画外音)" in (speaker or ""):
            line += f' 旁白，{emotion}：\\"{text}\\"（{emotion}）'
        elif sp in EXISTING_CHAR_REFS:
            line += f' (@{sp}_ref.png){sp}说：\\"{text}\\"（{emotion}）'
        else:
            line += f' {sp}说：\\"{text}\\"（{emotion}）'
    elif text and not speaker:
        # Narration without explicit speaker
        if emotion:
            line += f' 旁白，{emotion}：\\"{text}\\"（{emotion}）'

    return line


def build_task(ep_num, ep_config, part_key, part_label_cn):
    """为一集的一个 part 构建完整 task 对象"""
    part = ep_config.get(part_key)
    if not part:
        return None

    video_id = part["video_id"]
    ep_title = ep_config.get("episode_title", "")
    synopsis = ep_config.get("synopsis", "")
    # 优先读取 9grid，兼容旧版 6grid
    grids = part.get("storyboard_9grid", part.get("storyboard_6grid", []))
    grid_count = len(grids)
    grid_label = f"{grid_count}宫格" if grid_count else "6宫格"
    atmosphere = part.get("atmosphere", {})
    overall_mood = atmosphere.get("overall_mood", "")

    # 收集本 part 的场景和道具引用
    scene_refs = part.get("scene_refs", [])
    prop_refs = part.get("prop_refs", [])

    # 收集本 part 出场角色
    part_chars = collect_part_characters(grids)

    # === 构建 prompt ===
    # 1. 头部声明（分镜图 + 角色参考）
    storyboard_file = f"{video_id}_storyboard.png"
    header_lines = [f"(@{storyboard_file}) 为{grid_label}分镜参考图"]
    # 只为有实际 ref 文件的角色添加头部声明
    ref_chars = [c for c in part_chars if c in EXISTING_CHAR_REFS]
    for char_name in ref_chars:
        header_lines.append(f"(@{char_name}_ref.png) 为角色「{char_name}」的参考形象")
    # 注：场景/道具参考图不在头部声明，在后文需要时直接以 (@xx_ref.png) 内联引用
    header = "，".join(header_lines) + "。"

    # 2. 标准排除指令
    # 3. 集信息行
    ep_info = f"{video_id} 第{ep_num}集「{ep_title}」{part_label_cn}半部分。{synopsis} 氛围：{overall_mood}。"

    # 3.5 场景/道具参考行（内联引用，紧跟在剧情氛围之后、镜头描述之前）
    ref_context_parts = []
    if scene_refs:
        scene_mentions = " ".join(f"(@{sid}_ref.png)" for sid in scene_refs)
        ref_context_parts.append(f"场景参考 {scene_mentions}")
    if prop_refs:
        prop_mentions = " ".join(f"(@{pid}_ref.png)" for pid in prop_refs)
        ref_context_parts.append(f"道具参考 {prop_mentions}")
    ref_context_line = "。".join(ref_context_parts) + "。" if ref_context_parts else ""

    # 4. 逐镜头描述
    shot_lines = []
    for grid in grids:
        shot_lines.append(build_shot_line(ep_num, part_label_cn, grid, part_chars))

    prompt = header + "\\n\\n" + EXCLUSION_BLOCK + "\\n\\n" + ep_info
    if ref_context_line:
        prompt += " " + ref_context_line
    prompt += "\\n\\n" + "\\n".join(shot_lines)

    # === referenceFiles（相对路径），只含实际存在的文件 ===
    ep_code = f"EP{ep_num:02d}"
    ref_files = [f"episodes/{ep_code}/{storyboard_file}"]
    for char_name in ref_chars:
        ref_path = f"characters/{char_name}_ref.png"
        if ref_path not in ref_files:
            ref_files.append(ref_path)
    # 场景参考图
    for scene_id in scene_refs:
        ref_path = f"scenes/{scene_id}_ref.png"
        if ref_path not in ref_files:
            ref_files.append(ref_path)
    # 道具参考图
    for prop_id in prop_refs:
        ref_path = f"props/{prop_id}_ref.png"
        if ref_path not in ref_files:
            ref_files.append(ref_path)

    # === 构建 task ===
    part_letter = "A" if part_key == "part_a" else "B"
    task = {
        "prompt": prompt,
        "description": f"{PROJECT_ID} EP{ep_num:02d} Part-{part_letter} 「{ep_title}」{part_label_cn}半部分 {grid_label}分镜→视频",
        "modelConfig": MODEL_CONFIG.copy(),
        "referenceFiles": ref_files,
        "realSubmit": False,
        "priority": 1,
        "tags": [PROJECT_ID, ep_code, part_letter]
    }

    return task


def main():
    tasks = []
    for ep in range(1, 26):
        ep_code = f"EP{ep:02d}"
        config_path = EPISODES_DIR / ep_code / "storyboard_config.json"
        if not config_path.exists():
            print(f"⚠️ {ep_code}: storyboard_config.json 不存在，跳过")
            continue

        with open(config_path, encoding="utf-8") as f:
            config = json.load(f)

        # Part A
        task_a = build_task(ep, config, "part_a", "上")
        if task_a:
            tasks.append(task_a)

        # Part B
        task_b = build_task(ep, config, "part_b", "下")
        if task_b:
            tasks.append(task_b)

        print(f"✅ {ep_code}「{config.get('episode_title', '')}」→ {2 if task_a and task_b else 1} 条任务")

    # 输出
    output = {
        "project_id": PROJECT_ID,
        "project_name": PROJECT_NAME,
        "total_tasks": len(tasks),
        "created_date": "2026-02-21",
        "tasks": tasks
    }

    output_path = PROJECT_DIR / "seedance_project_tasks.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"✅ seedance_project_tasks.json 已生成")
    print(f"📋 总任务数: {len(tasks)}")
    print(f"📁 文件: {output_path}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
