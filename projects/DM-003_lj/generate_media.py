#!/usr/bin/env python3
"""
短剧媒体生成脚本 — DM-003《绿迹》
Phase 1: 生成角色参考图 (single configured image model)
Phase 2: 参考角色图生成分镜图片 (single configured image model)
"""
import os
import re
import io
import json
import time
import sys
import base64
from pathlib import Path
from urllib.parse import urljoin

import requests
from google import genai
from google.genai import types
from PIL import Image

# ========== 配置 ==========
PROJECT_DIR = Path(__file__).parent
EPISODES_DIR = PROJECT_DIR / "episodes"
CHARACTERS_DIR = PROJECT_DIR / "characters"
DEFAULT_IMAGE_MODEL = "gemini-2.5-flash-image-preview"
ALLOWED_IMAGE_MODELS = {
    "gemini-2.5-flash-image-preview",
    "gemini-3-pro-image-preview",
}

# API 配置
def load_api_config():
    """从配置文件和环境变量加载 API Key、Base URL、图片模型"""
    api_key = None
    base_url = None
    image_model = DEFAULT_IMAGE_MODEL

    config_path = PROJECT_DIR.parent.parent / ".config" / "api_keys.json"
    if config_path.exists():
        with open(config_path, encoding="utf-8") as f:
            config = json.load(f)
        api_key = config.get("gemini_api_key")
        base_url = config.get("gemini_base_url") or config.get("base_url")
        image_model = config.get("gemini_image_model", image_model)

    # 环境变量优先
    api_key = os.environ.get("GEMINI_API_KEY", api_key)
    base_url = os.environ.get("GEMINI_BASE_URL", base_url)
    image_model = os.environ.get("GEMINI_IMAGE_MODEL", image_model)

    # 去掉 base_url 中的 API 版本路径，SDK 会自动拼接
    if base_url:
        from urllib.parse import urlparse, urlunparse
        parsed = urlparse(base_url)
        base_url = urlunparse((parsed.scheme, parsed.netloc, '/', '', '', ''))

    if not api_key:
        raise RuntimeError("未找到 GEMINI_API_KEY，请配置 api_keys.json 或设置环境变量")

    if image_model not in ALLOWED_IMAGE_MODELS:
        raise RuntimeError(
            f"不支持的图片模型: {image_model}，请在 api_keys.json 设置 gemini_image_model 为 "
            "gemini-2.5-flash-image-preview 或 gemini-3-pro-image-preview"
        )

    return api_key, base_url, image_model


api_key, base_url, image_model = load_api_config()

http_options = types.HttpOptions(base_url=base_url) if base_url else None
client = genai.Client(api_key=api_key, http_options=http_options)
print(f"🔑 API 已配置 | Base URL: {base_url or '默认'}")
print(f"🖼️ 图片模型: {image_model}")


def extract_inline_images(response) -> list:
    """从 Gemini generate_content 响应中提取图片 part 列表"""
    images = []
    if not response or not response.candidates:
        return images
    for part in response.candidates[0].content.parts:
        if part.inline_data and part.inline_data.mime_type.startswith("image/"):
            images.append(part)
    return images


def generate_images_with_model(contents, request_tag: str) -> list:
    """统一图像生成入口：全局仅使用一个配置模型"""
    try:
        response = client.models.generate_content(
            model=image_model,
            contents=contents,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
            ),
        )
        return extract_inline_images(response)
    except Exception as e:
        print(f"  ❌ 图像生成失败 [{request_tag}] | model={image_model} | {e}")
        return []


# ========== Phase 1: 角色参考图生成 ==========

def parse_character_bible(bible_path: str) -> list:
    """解析 character_bible.md，提取角色名和 AI 绘图关键词"""
    with open(bible_path, "r", encoding="utf-8") as f:
        content = f.read()

    characters = []

    blocks = re.split(r'### 角色\d+[：:]', content)
    names_pattern = re.findall(r'### 角色\d+[：:]\s*(.+)', content)

    for i, block in enumerate(blocks[1:]):
        raw_name = names_pattern[i].strip() if i < len(names_pattern) else f"角色{i+1}"
        name = raw_name.split('（')[0].strip()

        prompt_match = re.search(r'\*{0,2}AI绘图关键词[（(]英文[）)]\*{0,2}[：:]\s*(.+)', block)
        if prompt_match:
            ai_prompt = prompt_match.group(1).strip()
        else:
            continue

        characters.append({"name": name, "ai_prompt": ai_prompt})

    return characters


def phase1_generate_characters():
    """Phase 1: 角色参考图多图生成（单次请求最多7张）"""
    bible_path = CHARACTERS_DIR / "character_bible.md"
    if not bible_path.exists():
        print("❌ character_bible.md 不存在，跳过角色参考图生成")
        return {}

    print("\n" + "=" * 60)
    print("🎨 Phase 1: 生成角色参考图")
    print("=" * 60)

    characters = parse_character_bible(str(bible_path))
    print(f"📋 发现 {len(characters)} 个角色")

    # 检查哪些角色已有图片
    char_ref_map = {}
    need_generate = []
    for char in characters:
        filename = f"{char['name']}_ref.png"
        output_path = CHARACTERS_DIR / filename
        if output_path.exists():
            print(f"  ⏭️ 角色图已存在: {filename}")
            char_ref_map[char["name"]] = [str(output_path)]
        else:
            need_generate.append(char)

    if not need_generate:
        print("  所有角色图已存在，跳过生成")
    else:
        max_images_per_request = 7
        if len(need_generate) <= max_images_per_request:
            batches = [need_generate]
        else:
            batches = [
                need_generate[i:i + max_images_per_request]
                for i in range(0, len(need_generate), max_images_per_request)
            ]

        for i, batch in enumerate(batches, start=1):
            if len(batches) == 1:
                print(f"\n  🎨 单次请求生成角色图：{len(batch)} 张")
            else:
                print(f"\n  🎨 单次请求生成角色图：第 {i}/{len(batches)} 批（{len(batch)} 张）")

            numbered_specs = []
            for idx, char in enumerate(batch, start=1):
                numbered_specs.append(f"{idx}. {char['name']}: {char['ai_prompt']}")

            prompt = (
                "Generate character reference sheets. "
                f"Return exactly {len(batch)} separate images in the same order as the numbered list below.\n"
                "Each image: 16:9 landscape, white background, left side face close-up, "
                "right side full-body views(front/side/back), clean lineart, "
                "cinematic realistic style.\n\n"
                "Character list:\n" + "\n".join(numbered_specs)
            )

            try:
                generated_parts = generate_images_with_model(
                    prompt,
                    request_tag=f"characters_batch_{i}",
                )

                for idx, part_img in enumerate(generated_parts):
                    if idx >= len(batch):
                        break
                    char = batch[idx]
                    filename = f"{char['name']}_ref.png"
                    output_path = CHARACTERS_DIR / filename
                    image = Image.open(io.BytesIO(part_img.inline_data.data))
                    image.save(str(output_path))
                    char_ref_map[char["name"]] = [str(output_path)]
                    print(f"  ✅ {filename}")

                if len(generated_parts) < len(batch):
                    print(f"  ⚠️ 本次请求仅返回 {len(generated_parts)}/{len(batch)} 张；按要求不做单张兜底")
                    for char in batch[len(generated_parts):]:
                        char_ref_map[char["name"]] = []

            except Exception as e:
                print(f"  ❌ 批量生成失败（不做单张兜底）: {e}")
                for char in batch:
                    char_ref_map[char["name"]] = []

            if i < len(batches):
                time.sleep(2)

    # 保存角色参考图索引
    ref_index = {name: paths for name, paths in char_ref_map.items()}
    index_path = CHARACTERS_DIR / "ref_index.json"
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(ref_index, f, ensure_ascii=False, indent=2)
    print(f"\n📋 角色参考图索引: {index_path}")

    return char_ref_map


# ========== Phase 2: 分镜图片生成（参考角色图） ==========

def load_character_refs_inline(char_ref_map: dict) -> dict:
    """加载角色参考图为 inline Part 对象（避免使用 files.upload API）"""
    loaded = {}
    for name, paths in char_ref_map.items():
        parts = []
        for p in paths:
            if os.path.exists(p):
                try:
                    with open(p, "rb") as fh:
                        file_bytes = fh.read()
                    part = types.Part(
                        inline_data=types.Blob(
                            mime_type="image/png",
                            data=file_bytes
                        )
                    )
                    parts.append(part)
                    print(f"  📎 已加载: {Path(p).name} ({len(file_bytes)//1024}KB)")
                except Exception as e:
                    print(f"  ⚠️ 加载 {Path(p).name} 失败: {e}")
        loaded[name] = parts
    return loaded


def generate_storyboards_for_two_episodes(ep_payloads: list, char_uploaded: dict) -> dict:
    """一次生成两集分镜图（每集A/B各1张，共最多4张）"""
    results = {"images": 0, "failed": 0}
    jobs = []

    for ep_dir, ep_num, config in ep_payloads:
        for part_key, part_label in [("part_a", "上"), ("part_b", "下")]:
            part = config.get(part_key)
            if not part:
                continue

            video_id = part["video_id"]
            img_filename = f"{video_id}_storyboard.png"
            img_path = ep_dir / img_filename

            if img_path.exists():
                print(f"  ⏭️ 已存在: {img_filename}")
                results["images"] += 1
                continue

            grids = part.get("storyboard_9grid", part.get("storyboard_6grid", []))
            grid_descs = []
            part_chars = set()
            for g in grids:
                prompt = g.get("ai_image_prompt", "")
                if prompt:
                    grid_descs.append(f"Panel {g['grid_number']}: {prompt}")
                for c in g.get("characters", []):
                    if c.get("name"):
                        part_chars.add(c["name"])

            prompt_text = (
                f"Create ONE composite storyboard image for {ep_num} {part_label} half. "
                f"3x3 grid (3 columns, 3 rows), cinematic realistic style, 16:9 aspect ratio, cinematic.\n"
                f"Scenes:\n" + "\n".join(grid_descs)
            )

            jobs.append({
                "ep_dir": ep_dir,
                "ep_num": ep_num,
                "config": config,
                "part_label": part_label,
                "img_path": img_path,
                "prompt_text": prompt_text,
                "part_chars": sorted(part_chars),
            })

    if not jobs:
        return results

    print(f"  🎨 批量生成分镜图：{len(jobs)} 张（两集一批）")

    # 构建统一内容：参考图 + 多任务文本
    content_parts = []
    all_chars = sorted({name for j in jobs for name in j["part_chars"]})
    for char_name in all_chars:
        parts = char_uploaded.get(char_name, [])
        if not parts:
            continue
        content_parts.append(types.Part(text=f"[Character reference: {char_name}]"))
        content_parts.extend(parts)

    task_lines = []
    for idx, job in enumerate(jobs, start=1):
        char_text = ", ".join(job["part_chars"]) if job["part_chars"] else "none"
        task_lines.append(
            f"Task {idx} | {job['ep_num']}-{job['part_label']} | use chars: {char_text}\n{job['prompt_text']}"
        )

    multi_prompt = (
        f"Generate exactly {len(jobs)} separate storyboard images in order Task1..Task{len(jobs)}. "
        f"Each output corresponds to one task below, keep character consistency with references.\n\n"
        + "\n\n".join(task_lines)
    )
    content_parts.append(types.Part(text=multi_prompt))

    saved_idx = set()
    try:
        images = generate_images_with_model(
            content_parts,
            request_tag="storyboard_two_episodes",
        )

        for idx, part_img in enumerate(images):
            if idx >= len(jobs):
                break
            job = jobs[idx]
            image = Image.open(io.BytesIO(part_img.inline_data.data))
            image.save(str(job["img_path"]))
            print(f"  ✅ {job['img_path'].name}")
            results["images"] += 1
            saved_idx.add(idx)

        if len(images) < len(jobs):
            print(f"  ⚠️ 批量返回 {len(images)}/{len(jobs)} 张；按要求不做单张兜底")
            for idx in range(len(images), len(jobs)):
                print(f"  ❌ 未生成: {jobs[idx]['img_path'].name}")
            results["failed"] += len(jobs) - len(images)

    except Exception as e:
        print(f"  ❌ 两集批量生成失败（不做单张兜底）: {e}")
        results["failed"] += len(jobs)

    return results


# ========== 逐集处理 ==========

def process_episode_pair(ep_payloads: list, char_uploaded: dict):
    """处理两集（或不足两集）：分镜图一次批量生成"""
    if not ep_payloads:
        return None

    labels = [f"{ep_num}:{cfg.get('episode_title', '未知')}" for _, ep_num, cfg in ep_payloads]
    print(f"\n{'='*50}")
    print(f"📺 批次处理 {' | '.join(labels)}")
    print(f"{'='*50}")

    results = {"images": 0, "failed": 0}

    # Phase 2: 两集一批
    sb_results = generate_storyboards_for_two_episodes(ep_payloads, char_uploaded)
    results["images"] += sb_results["images"]
    results["failed"] += sb_results["failed"]

    return results


# ========== 媒体索引 ==========

def generate_media_index(start_ep, end_ep):
    """生成媒体文件索引"""
    index = {"characters": [], "episodes": []}

    for f in sorted(CHARACTERS_DIR.iterdir()):
        if f.suffix == ".png":
            index["characters"].append({
                "filename": f.name,
                "size_bytes": f.stat().st_size
            })

    for ep in range(start_ep, end_ep + 1):
        ep_num = f"EP{ep:02d}"
        ep_dir = EPISODES_DIR / ep_num
        if not ep_dir.exists():
            continue
        ep_entry = {"episode": ep_num, "files": []}
        for f in sorted(ep_dir.iterdir()):
            if f.suffix in (".png", ".mp4"):
                ep_entry["files"].append({
                    "filename": f.name,
                    "type": "image" if f.suffix == ".png" else "video",
                    "size_bytes": f.stat().st_size
                })
        index["episodes"].append(ep_entry)

    index_path = PROJECT_DIR / "media_index.json"
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    print(f"\n📋 媒体索引: {index_path}")


# ========== 主流程 ==========

def main():
    start_ep = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    end_ep = int(sys.argv[2]) if len(sys.argv) > 2 else 25
    skip_chars = "--skip-chars" in sys.argv
    only_chars = "--only-chars" in sys.argv

    print(f"🎬 短剧媒体生成 — DM-003《绿迹》")
    print(f"📁 项目: {PROJECT_DIR}")
    print(f"📺 范围: EP{start_ep:02d} - EP{end_ep:02d}")

    # ===== Phase 1: 角色参考图 =====
    if skip_chars:
        print("\n⏭️ 跳过角色参考图生成（使用已有）")
        ref_index_path = CHARACTERS_DIR / "ref_index.json"
        if ref_index_path.exists():
            with open(ref_index_path, encoding="utf-8") as f:
                char_ref_map = json.load(f)
        else:
            char_ref_map = {}
    else:
        char_ref_map = phase1_generate_characters()

    if only_chars:
        print("\n⏹️ 仅角色模式：跳过分镜生成")
        print(f"\n{'='*60}")
        print(f"🏁 角色生成完成!")
        print(f"🎨 角色参考图: {sum(len(v) for v in char_ref_map.values())} 张")
        print(f"{'='*60}")
        return

    # ===== 加载角色参考图（inline data） =====
    print("\n📎 加载角色参考图（inline data）...")
    char_uploaded = load_character_refs_inline(char_ref_map) if char_ref_map else {}
    print(f"   已加载 {sum(len(v) for v in char_uploaded.values())} 张角色参考图")

    # ===== Phase 2: 两集一批生成分镜 =====
    total = {"images": 0, "failed": 0}

    ep_payloads = []
    for ep in range(start_ep, end_ep + 1):
        ep_num = f"EP{ep:02d}"
        ep_dir = EPISODES_DIR / ep_num
        config_path = ep_dir / "storyboard_config.json"
        if not ep_dir.exists() or not config_path.exists():
            print(f"⚠️ {ep_num} 不存在或缺少 storyboard_config.json，跳过")
            continue
        with open(config_path, encoding="utf-8") as f:
            config = json.load(f)
        ep_payloads.append((ep_dir, ep_num, config))

    for i in range(0, len(ep_payloads), 2):
        pair = ep_payloads[i:i + 2]
        result = process_episode_pair(pair, char_uploaded)
        if result:
            for k in total:
                total[k] += result[k]

    # ===== 媒体索引 =====
    generate_media_index(start_ep, end_ep)

    print(f"\n{'='*60}")
    print(f"🏁 全部完成!")
    print(f"🎨 角色参考图: {sum(len(v) for v in char_ref_map.values())} 张")
    print(f"🖼️ 分镜图片: {total['images']} 张")
    print(f"❌ 失败: {total['failed']} 个")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
