#!/usr/bin/env python3
"""
短剧媒体生成脚本（优化版）
目标修复：
1. 角色参考图必须按单角色单请求生成，尽量稳定输出“左侧脸部特写 + 右侧全身 front/side/back”单图多视角版式
2. storyboard 强制按 part 输出一张 9 宫格图，不再回退到 6 宫格
3. storyboard 角色引用改为 panel 级声明，并加入角色名 normalize 与注入日志
"""
import io
import json
import os
import re
import sys
import time
from pathlib import Path

from google import genai
from google.genai import types
from PIL import Image

PROJECT_DIR = Path(__file__).parent
EPISODES_DIR = PROJECT_DIR / "episodes"
CHARACTERS_DIR = PROJECT_DIR / "characters"
DEFAULT_IMAGE_MODEL = "gemini-2.5-flash-image"
ALLOWED_IMAGE_MODELS = {
    "gemini-2.5-flash-image",
    "gemini-3-pro-image-preview",
}


def normalize_name(name: str) -> str:
    if not name:
        return ""
    name = re.sub(r"\s+", "", str(name)).strip()
    name = name.replace("（", "(").replace("）", ")")
    name = re.sub(r"\(.*?\)", "", name).strip()
    return name


def load_api_config():
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

    api_key = os.environ.get("GEMINI_API_KEY", api_key)
    base_url = os.environ.get("GEMINI_BASE_URL", base_url)
    image_model = os.environ.get("GEMINI_IMAGE_MODEL", image_model)

    if base_url:
        from urllib.parse import urlparse, urlunparse
        parsed = urlparse(base_url)
        base_url = urlunparse((parsed.scheme, parsed.netloc, "/", "", "", ""))

    if not api_key:
        raise RuntimeError("未找到 GEMINI_API_KEY，请配置 api_keys.json 或环境变量")
    if image_model not in ALLOWED_IMAGE_MODELS:
        raise RuntimeError(f"不支持的图片模型: {image_model}")

    return api_key, base_url, image_model


api_key, base_url, image_model = load_api_config()
http_options = types.HttpOptions(base_url=base_url) if base_url else None
client = genai.Client(api_key=api_key, http_options=http_options)


# -------------------------
# Gemini helpers
# -------------------------
def extract_inline_images(response) -> list:
    images = []
    if not response or not getattr(response, "candidates", None):
        return images
    first = response.candidates[0]
    if not getattr(first, "content", None):
        return images
    for part in first.content.parts:
        if getattr(part, "inline_data", None) and part.inline_data.mime_type.startswith("image/"):
            images.append(part)
    return images


def generate_images_with_model(contents, request_tag: str) -> list:
    try:
        response = client.models.generate_content(
            model=image_model,
            contents=contents,
            config=types.GenerateContentConfig(response_modalities=["IMAGE", "TEXT"]),
        )
        return extract_inline_images(response)
    except Exception as e:
        print(f"  ❌ 图像生成失败 [{request_tag}] | model={image_model} | {e}")
        return []


# -------------------------
# Character phase
# -------------------------
def parse_character_bible(bible_path: str) -> list:
    with open(bible_path, "r", encoding="utf-8") as f:
        content = f.read()

    characters = []
    blocks = re.split(r'### 角色\d+[：:]', content)
    names_pattern = re.findall(r'### 角色\d+[：:]\s*(.+)', content)

    for i, block in enumerate(blocks[1:]):
        raw_name = names_pattern[i].strip() if i < len(names_pattern) else f"角色{i+1}"
        name = normalize_name(raw_name.split('（')[0].strip())
        prompt_match = re.search(r'\*{0,2}AI绘图关键词[（(]英文[）)]\*{0,2}[：:]\s*(.+)', block)
        if not prompt_match:
            continue
        ai_prompt = prompt_match.group(1).strip()
        characters.append({"name": name, "ai_prompt": ai_prompt, "raw_name": raw_name})
    return characters


def load_visual_style() -> str:
    candidates = [
        PROJECT_DIR / "visual_style.json",
        PROJECT_DIR / "visual_style.txt",
        PROJECT_DIR / "style.json",
    ]
    for p in candidates:
        if not p.exists():
            continue
        try:
            if p.suffix == ".json":
                data = json.loads(p.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    return json.dumps(data, ensure_ascii=False)
                return str(data)
            return p.read_text(encoding="utf-8").strip()
        except Exception:
            pass
    return "cinematic realistic style, consistent lighting, grounded composition"


VISUAL_STYLE = load_visual_style()


def build_character_sheet_prompt(char_name: str, ai_prompt: str) -> str:
    return (
        "Create exactly ONE character reference sheet image. "
        "Single image only, do not return multiple separate images. "
        "16:9 landscape canvas, pure white clean background, structured layout. "
        "Left side: one large face close-up portrait. "
        "Right side: three full-body views of the SAME character in a vertical or clean editorial arrangement: front view, side view, back view. "
        "All views must depict the same person with fully consistent face, hair, clothing, age, body shape, and color palette. "
        "Do not replace the sheet with posters, mood boards, or multiple characters. "
        f"Visual style: {VISUAL_STYLE}. "
        f"Character name: {char_name}. "
        f"Character design keywords: {ai_prompt}."
    )



def phase1_generate_characters() -> dict:
    bible_path = CHARACTERS_DIR / "character_bible.md"
    if not bible_path.exists():
        print("❌ character_bible.md 不存在，跳过角色参考图生成")
        return {}

    print("\n" + "=" * 60)
    print("🎨 Phase 1: 生成角色参考图（优化版）")
    print("=" * 60)

    characters = parse_character_bible(str(bible_path))
    print(f"📋 发现 {len(characters)} 个角色")

    char_ref_map = {}
    for char in characters:
        filename = f"{char['name']}_ref.png"
        output_path = CHARACTERS_DIR / filename
        if output_path.exists():
            print(f"  ⏭️ 已存在: {filename}")
            char_ref_map[char["name"]] = [str(output_path)]
            continue

        prompt = build_character_sheet_prompt(char["name"], char["ai_prompt"])
        parts = generate_images_with_model(prompt, request_tag=f"character_{char['name']}")
        if not parts:
            print(f"  ❌ 失败: {filename}")
            char_ref_map[char["name"]] = []
            continue

        try:
            image = Image.open(io.BytesIO(parts[0].inline_data.data))
            image.save(str(output_path))
            char_ref_map[char["name"]] = [str(output_path)]
            print(f"  ✅ {filename}")
        except Exception as e:
            print(f"  ❌ 保存失败 {filename}: {e}")
            char_ref_map[char["name"]] = []

        time.sleep(1)

    index_path = CHARACTERS_DIR / "ref_index.json"
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(char_ref_map, f, ensure_ascii=False, indent=2)
    print(f"\n📋 角色参考图索引: {index_path}")
    return char_ref_map


# -------------------------
# Storyboard phase
# -------------------------
def load_character_refs_inline(char_ref_map: dict) -> dict:
    loaded = {}
    for name, paths in char_ref_map.items():
        norm_name = normalize_name(name)
        parts = []
        for p in paths:
            p = str(p)
            if os.path.exists(p):
                try:
                    with open(p, "rb") as fh:
                        file_bytes = fh.read()
                    parts.append(types.Part(inline_data=types.Blob(mime_type="image/png", data=file_bytes)))
                except Exception as e:
                    print(f"  ⚠️ 加载角色参考图失败 {p}: {e}")
        loaded[norm_name] = parts
    return loaded



def get_storyboard_panels(part: dict) -> list:
    panels = part.get("storyboard_9grid") or []
    if not isinstance(panels, list):
        panels = []

    # 强制 9 格；不足则补位，避免退回 6 格
    normalized = []
    for idx in range(1, 10):
        raw = next((x for x in panels if int(x.get("grid_number", 0) or 0) == idx), None)
        if raw:
            normalized.append(raw)
        else:
            normalized.append({
                "grid_number": idx,
                "ai_image_prompt": "Quiet transition beat, cinematic environmental continuation, no dramatic new action.",
                "characters": [],
            })
    return normalized



def build_storyboard_9grid_prompt(ep_num: str, part_label: str, panels: list) -> str:
    panel_lines = []
    for panel in panels:
        char_names = [normalize_name(c.get("name", "")) for c in panel.get("characters", []) if c.get("name")]
        char_names = [c for c in char_names if c]
        char_text = ", ".join(char_names) if char_names else "none"
        prompt_text = panel.get("ai_image_prompt", "").strip()
        panel_lines.append(
            f"Panel {panel['grid_number']} | characters: {char_text} | shot: {prompt_text}"
        )

    return (
        "Create exactly ONE storyboard image only. "
        "The output must be a strict 3x3 storyboard grid with exactly 9 panels in a single composite image. "
        "Do not return 9 separate images. Do not omit panels. Do not merge panels. "
        "Each panel must correspond to the numbered panel description below in order from Panel 1 to Panel 9. "
        "All recurring characters must remain visually consistent with the provided references. "
        "Overall image should feel like a professional previsualization storyboard sheet. "
        f"Visual style: {VISUAL_STYLE}. "
        f"Episode: {ep_num}, part: {part_label}.\n\n"
        + "\n".join(panel_lines)
    )



def build_storyboard_request(job: dict, char_uploaded: dict):
    contents = []
    injected = []
    for name in job["part_chars"]:
        ref_parts = char_uploaded.get(name, [])
        if not ref_parts:
            continue
        contents.append(types.Part(text=f"[Character reference: {name}]") )
        contents.extend(ref_parts)
        injected.append(name)
    contents.append(types.Part(text=job["prompt_text"]))
    return contents, injected



def generate_storyboards_for_episodes(ep_payloads: list, char_uploaded: dict) -> dict:
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

            panels = get_storyboard_panels(part)
            part_chars = set()
            for panel in panels:
                for c in panel.get("characters", []):
                    n = normalize_name(c.get("name", ""))
                    if n:
                        part_chars.add(n)

            prompt_text = build_storyboard_9grid_prompt(ep_num, part_label, panels)
            jobs.append({
                "ep_num": ep_num,
                "ep_dir": ep_dir,
                "part_key": part_key,
                "part_label": part_label,
                "img_path": img_path,
                "prompt_text": prompt_text,
                "panels": panels,
                "part_chars": sorted(part_chars),
            })

    if not jobs:
        return results

    print(f"  🎞️ 开始生成 storyboard：{len(jobs)} 张")
    for job in jobs:
        contents, injected = build_storyboard_request(job, char_uploaded)
        print(f"  📎 {job['img_path'].name} 引用角色: {', '.join(injected) if injected else 'none'}")
        parts = generate_images_with_model(contents, request_tag=job["img_path"].stem)
        if not parts:
            print(f"  ❌ 未生成: {job['img_path'].name}")
            results["failed"] += 1
            continue
        try:
            image = Image.open(io.BytesIO(parts[0].inline_data.data))
            image.save(str(job["img_path"]))
            print(f"  ✅ {job['img_path'].name}")
            results["images"] += 1
        except Exception as e:
            print(f"  ❌ 保存失败 {job['img_path'].name}: {e}")
            results["failed"] += 1
        time.sleep(1)
    return results


# -------------------------
# Media index + main
# -------------------------
def generate_media_index(start_ep, end_ep):
    index = {"characters": [], "episodes": []}
    if CHARACTERS_DIR.exists():
        for f in sorted(CHARACTERS_DIR.iterdir()):
            if f.suffix == ".png":
                index["characters"].append({"filename": f.name, "size_bytes": f.stat().st_size})

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
                    "size_bytes": f.stat().st_size,
                })
        index["episodes"].append(ep_entry)

    index_path = PROJECT_DIR / "media_index.json"
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    print(f"\n📋 媒体索引: {index_path}")



def main():
    start_ep = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    end_ep = int(sys.argv[2]) if len(sys.argv) > 2 else 25
    skip_chars = "--skip-chars" in sys.argv
    only_chars = "--only-chars" in sys.argv

    print("🎬 短剧媒体生成（优化版）")
    print(f"📁 项目: {PROJECT_DIR}")
    print(f"📺 范围: EP{start_ep:02d} - EP{end_ep:02d}")
    print(f"🖼️ 图片模型: {image_model}")

    if skip_chars:
        ref_index_path = CHARACTERS_DIR / "ref_index.json"
        if ref_index_path.exists():
            with open(ref_index_path, encoding="utf-8") as f:
                char_ref_map = json.load(f)
        else:
            char_ref_map = {}
    else:
        char_ref_map = phase1_generate_characters()

    if only_chars:
        print("\n⏹️ 仅角色模式完成")
        return

    print("\n📎 加载角色参考图...")
    char_uploaded = load_character_refs_inline(char_ref_map) if char_ref_map else {}
    print(f"   已加载 {sum(len(v) for v in char_uploaded.values())} 张角色参考图")

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

    total = generate_storyboards_for_episodes(ep_payloads, char_uploaded)
    generate_media_index(start_ep, end_ep)

    print("\n" + "=" * 60)
    print("🏁 全部完成")
    print(f"🎨 角色参考图: {sum(len(v) for v in char_ref_map.values())} 张")
    print(f"🖼️ 分镜图片: {total['images']} 张")
    print(f"❌ 失败: {total['failed']} 个")
    print("=" * 60)


if __name__ == "__main__":
    main()
