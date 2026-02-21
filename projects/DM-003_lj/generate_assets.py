#!/usr/bin/env python3
"""
场景四宫格 + 道具三视图 + 角色参考图 生成脚本 — DM-003《绿迹》

每个资产只调用一次 API，返回一张合成图：
  - 场景：2×2 四宫格（正面/左侧/右侧/背面）合成到一张图
  - 道具：1×3 三视图（正面/侧面/俯视）合成到一张图
  - 角色：每人一张参考图（正面+侧面+全身多视角合成）

用法:
    python generate_assets.py                    # 生成全部
    python generate_assets.py --only-scenes      # 仅场景
    python generate_assets.py --only-props       # 仅道具
    python generate_assets.py --only-chars       # 仅角色
"""
import os
import re
import io
import json
import time
import sys
from pathlib import Path

from google import genai
from google.genai import types
from PIL import Image

# ========== 配置 ==========
PROJECT_DIR = Path(__file__).parent
SCENES_DIR = PROJECT_DIR / "scenes"
PROPS_DIR = PROJECT_DIR / "props"
CHARACTERS_DIR = PROJECT_DIR / "characters"
DEFAULT_IMAGE_MODEL = "gemini-2.5-flash-image-preview"
ALLOWED_IMAGE_MODELS = {
    "gemini-2.5-flash-image-preview",
    "gemini-3-pro-image-preview",
}

# 视觉风格 — Dark Thriller（暗黑悬疑）
STYLE_SUFFIX = (
    "shot on ARRI ALEXA 65, Kodak Vision3 500T, dark thriller atmosphere, "
    "high contrast chiaroscuro lighting, desaturated cold tones, noir shadows, tension"
)


# ========== API 配置 ==========
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
        base_url = urlunparse((parsed.scheme, parsed.netloc, '/', '', '', ''))

    if not api_key:
        raise RuntimeError("未找到 GEMINI_API_KEY")
    if image_model not in ALLOWED_IMAGE_MODELS:
        raise RuntimeError(f"不支持的图片模型: {image_model}")

    return api_key, base_url, image_model


api_key, base_url, image_model = load_api_config()
http_options = types.HttpOptions(base_url=base_url) if base_url else None
client = genai.Client(api_key=api_key, http_options=http_options)
print(f"🔑 API 已配置 | Base URL: {base_url or '默认'}")
print(f"🖼️ 图片模型: {image_model}")
print(f"🎨 视觉风格: Dark Thriller（暗黑悬疑）")


def extract_inline_images(response) -> list:
    images = []
    if not response or not response.candidates:
        return images
    for part in response.candidates[0].content.parts:
        if part.inline_data and part.inline_data.mime_type.startswith("image/"):
            images.append(part)
    return images


def generate_images(contents, tag: str) -> list:
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
        print(f"  ❌ 生成失败 [{tag}]: {e}")
        return []


# ========== 解析 Bible 文件 ==========

def parse_scene_bible(bible_path: Path) -> list:
    """解析 scene_bible.md"""
    with open(bible_path, encoding="utf-8") as f:
        content = f.read()

    scenes = []
    blocks = re.split(r'## 场景\d+[：:]', content)
    names = re.findall(r'## 场景\d+[：:]\s*(.+)', content)

    for i, block in enumerate(blocks[1:]):
        name = names[i].strip() if i < len(names) else f"场景{i+1}"

        id_match = re.search(r'\*{0,2}场景ID\*{0,2}[：:]\s*(\S+)', block)
        scene_id = id_match.group(1).strip() if id_match else f"scene_{i+1:02d}"

        prompt_match = re.search(r'\*{0,2}AI绘图关键词[（(]英文[）)]\*{0,2}[：:]\s*(.+)', block)
        if not prompt_match:
            continue
        ai_prompt = prompt_match.group(1).strip()

        scenes.append({"name": name, "id": scene_id, "ai_prompt": ai_prompt})

    return scenes


def parse_prop_bible(bible_path: Path) -> list:
    """解析 prop_bible.md"""
    with open(bible_path, encoding="utf-8") as f:
        content = f.read()

    props = []
    blocks = re.split(r'## 道具\d+[：:]', content)
    names = re.findall(r'## 道具\d+[：:]\s*(.+)', content)

    for i, block in enumerate(blocks[1:]):
        name = names[i].strip() if i < len(names) else f"道具{i+1}"

        id_match = re.search(r'\*{0,2}道具ID\*{0,2}[：:]\s*(\S+)', block)
        prop_id = id_match.group(1).strip() if id_match else f"prop_{i+1:02d}"

        prompt_match = re.search(r'\*{0,2}AI绘图关键词[（(]英文[）)]\*{0,2}[：:]\s*(.+)', block)
        if not prompt_match:
            continue
        ai_prompt = prompt_match.group(1).strip()

        props.append({"name": name, "id": prop_id, "ai_prompt": ai_prompt})

    return props


def parse_character_bible(bible_path: Path) -> list:
    """解析 character_bible.md"""
    with open(bible_path, encoding="utf-8") as f:
        content = f.read()

    characters = []
    blocks = re.split(r'### 角色\d+[：:]', content)
    names = re.findall(r'### 角色\d+[：:]\s*(.+)', content)

    for i, block in enumerate(blocks[1:]):
        name = names[i].strip() if i < len(names) else f"角色{i+1}"

        prompt_match = re.search(r'\*{0,2}AI绘图关键词[（(]英文[）)]\*{0,2}[：:]\s*(.+)', block)
        if not prompt_match:
            continue
        ai_prompt = prompt_match.group(1).strip()

        characters.append({"name": name, "ai_prompt": ai_prompt})

    return characters


# ========== 生成逻辑 ==========

def generate_scene_composite(scene_id, scene_name, ai_prompt, output_dir):
    """为一个场景生成四宫格合成图（正面/左侧/右侧/背面 → 一张图）"""
    filename = f"{scene_id}_ref.png"
    output_path = output_dir / filename

    if output_path.exists():
        print(f"  ⏭️ 已存在: {filename}")
        return str(output_path)

    prompt = (
        f"Generate a single image containing a 2x2 grid (four panels) showing the same scene "
        f"from 4 different camera angles. All four panels must depict the SAME location/environment "
        f"with consistent design, furniture, and lighting.\n\n"
        f"Layout (2 rows × 2 columns):\n"
        f"  Top-Left: FRONT VIEW — face-on establishing shot, eye level, wide angle\n"
        f"  Top-Right: LEFT 45° — three-quarter view from the left side, showing depth\n"
        f"  Bottom-Left: RIGHT 45° — three-quarter view from the right side, showing details\n"
        f"  Bottom-Right: REAR/DISTANT VIEW — from behind or far away establishing shot\n\n"
        f"Scene description: {ai_prompt}\n"
        f"Visual style: {STYLE_SUFFIX}\n\n"
        f"Requirements: 16:9 overall aspect ratio, thin white dividing lines between panels, "
        f"each panel is a cinematic high-quality render, consistent color palette across all 4 views. "
        f"Small white labels in each panel corner: 'Front', 'Left 45°', 'Right 45°', 'Rear'."
    )

    print(f"  🎨 请求生成四宫格合成图...")
    parts = generate_images(prompt, tag=f"{scene_id}_4grid")

    if parts:
        try:
            img = Image.open(io.BytesIO(parts[0].inline_data.data))
            img.save(str(output_path))
            print(f"  ✅ 四宫格: {filename} ({output_path.stat().st_size // 1024}KB)")
            return str(output_path)
        except Exception as e:
            print(f"  ❌ 保存失败: {e}")
    else:
        print(f"  ❌ 无返回结果")
    return None


def generate_prop_composite(prop_id, prop_name, ai_prompt, output_dir):
    """为一个道具生成三视图合成图（正面/侧面/俯视 → 一张图）"""
    filename = f"{prop_id}_ref.png"
    output_path = output_dir / filename

    if output_path.exists():
        print(f"  ⏭️ 已存在: {filename}")
        return str(output_path)

    prompt = (
        f"Generate a single image containing a 1×3 horizontal triptych showing the same object "
        f"from 3 different angles. All three panels must depict the EXACT same object.\n\n"
        f"Layout (1 row × 3 columns, left to right):\n"
        f"  Left: FRONT VIEW — centered, facing camera directly\n"
        f"  Center: SIDE VIEW — profile angle, showing thickness and depth\n"
        f"  Right: TOP VIEW — overhead bird's-eye, looking straight down\n\n"
        f"Object description: {ai_prompt}\n"
        f"Visual style: {STYLE_SUFFIX}\n\n"
        f"Requirements: 16:9 overall aspect ratio, white background in each panel, "
        f"thin white dividing lines between panels, product photography lighting, "
        f"clean studio style, consistent object across all 3 views. "
        f"Small white labels: 'Front', 'Side', 'Top'."
    )

    print(f"  🎨 请求生成三视图合成图...")
    parts = generate_images(prompt, tag=f"{prop_id}_triview")

    if parts:
        try:
            img = Image.open(io.BytesIO(parts[0].inline_data.data))
            img.save(str(output_path))
            print(f"  ✅ 三视图: {filename} ({output_path.stat().st_size // 1024}KB)")
            return str(output_path)
        except Exception as e:
            print(f"  ❌ 保存失败: {e}")
    else:
        print(f"  ❌ 无返回结果")
    return None


def generate_char_composite(char_name, ai_prompt, output_dir):
    """为一个角色生成多视角参考合成图（正面特写+正面全身+侧面+背面 → 一张图）"""
    filename = f"{char_name}_ref.png"
    output_path = output_dir / filename

    if output_path.exists():
        print(f"  ⏭️ 已存在: {filename}")
        return str(output_path)

    prompt = (
        f"Generate a single character reference sheet image with a 2×2 grid layout "
        f"showing the SAME character from 4 angles. Consistent appearance across all panels.\n\n"
        f"Layout (2 rows × 2 columns):\n"
        f"  Top-Left: FACE CLOSE-UP — front-facing portrait, head and shoulders, detailed facial features\n"
        f"  Top-Right: FRONT FULL BODY — standing pose, full body visible, facing camera\n"
        f"  Bottom-Left: SIDE VIEW — three-quarter or profile, upper body\n"
        f"  Bottom-Right: BACK VIEW — from behind, showing outfit and hair from rear\n\n"
        f"Character description: {ai_prompt}\n"
        f"Visual style: {STYLE_SUFFIX}\n\n"
        f"Requirements: 16:9 overall aspect ratio, clean neutral background, thin white dividing lines, "
        f"cinematic realistic style, consistent clothing/hair/features across all views. "
        f"Small white labels: 'Face', 'Front', 'Side', 'Back'."
    )

    print(f"  🎨 请求生成角色四宫格参考图...")
    parts = generate_images(prompt, tag=f"char_{char_name}")

    if parts:
        try:
            img = Image.open(io.BytesIO(parts[0].inline_data.data))
            img.save(str(output_path))
            print(f"  ✅ 角色参考: {filename} ({output_path.stat().st_size // 1024}KB)")
            return str(output_path)
        except Exception as e:
            print(f"  ❌ 保存失败: {e}")
    else:
        print(f"  ❌ 无返回结果")
    return None


def phase_scenes():
    """Phase 1B: 生成场景四宫格图（每场景一张合成图）"""
    bible_path = SCENES_DIR / "scene_bible.md"
    if not bible_path.exists():
        print("\n⚠️ scenes/scene_bible.md 不存在，跳过场景生成")
        return {}

    print("\n" + "=" * 60)
    print("🏙️ Phase 1B: 生成场景四宫格图")
    print("=" * 60)

    scenes = parse_scene_bible(bible_path)
    print(f"📋 发现 {len(scenes)} 个场景")

    scene_ref_map = {}
    for scene in scenes:
        print(f"\n🏠 场景: {scene['name']} ({scene['id']})")
        ref = generate_scene_composite(
            scene["id"], scene["name"], scene["ai_prompt"], SCENES_DIR
        )
        scene_ref_map[scene["id"]] = {"name": scene["name"], "file": ref}
        time.sleep(3)

    index_path = SCENES_DIR / "ref_index.json"
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(scene_ref_map, f, ensure_ascii=False, indent=2)
    print(f"\n📋 场景索引: {index_path}")
    return scene_ref_map


def phase_props():
    """Phase 1C: 生成道具三视图（每道具一张合成图）"""
    bible_path = PROPS_DIR / "prop_bible.md"
    if not bible_path.exists():
        print("\n⚠️ props/prop_bible.md 不存在，跳过道具生成")
        return {}

    print("\n" + "=" * 60)
    print("🔧 Phase 1C: 生成道具三视图")
    print("=" * 60)

    props = parse_prop_bible(bible_path)
    print(f"📋 发现 {len(props)} 个道具")

    prop_ref_map = {}
    for prop in props:
        print(f"\n🔩 道具: {prop['name']} ({prop['id']})")
        ref = generate_prop_composite(
            prop["id"], prop["name"], prop["ai_prompt"], PROPS_DIR
        )
        prop_ref_map[prop["id"]] = {"name": prop["name"], "file": ref}
        time.sleep(3)

    index_path = PROPS_DIR / "ref_index.json"
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(prop_ref_map, f, ensure_ascii=False, indent=2)
    print(f"\n📋 道具索引: {index_path}")
    return prop_ref_map


def phase_chars():
    """Phase 1A: 生成角色多视角参考图（每角色一张合成图）"""
    bible_path = CHARACTERS_DIR / "character_bible.md"
    if not bible_path.exists():
        print("\n⚠️ characters/character_bible.md 不存在，跳过角色生成")
        return {}

    print("\n" + "=" * 60)
    print("🎨 Phase 1A: 生成角色参考图")
    print("=" * 60)

    characters = parse_character_bible(bible_path)
    print(f"📋 发现 {len(characters)} 个角色")

    char_ref_map = {}
    for char in characters:
        print(f"\n👤 角色: {char['name']}")
        ref = generate_char_composite(
            char["name"], char["ai_prompt"], CHARACTERS_DIR
        )
        char_ref_map[char["name"]] = {"file": ref}
        time.sleep(3)

    index_path = CHARACTERS_DIR / "ref_index.json"
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(char_ref_map, f, ensure_ascii=False, indent=2)
    print(f"\n📋 角色索引: {index_path}")
    return char_ref_map


def main():
    only_scenes = "--only-scenes" in sys.argv
    only_props = "--only-props" in sys.argv
    only_chars = "--only-chars" in sys.argv
    run_all = not (only_scenes or only_props or only_chars)

    print(f"🎬 DM-003《绿迹》资产生成（合成图模式）")
    print(f"📁 项目: {PROJECT_DIR}")

    # 确保目录存在
    SCENES_DIR.mkdir(parents=True, exist_ok=True)
    PROPS_DIR.mkdir(parents=True, exist_ok=True)
    CHARACTERS_DIR.mkdir(parents=True, exist_ok=True)

    char_map = {}
    scene_map = {}
    prop_map = {}

    if run_all or only_chars:
        char_map = phase_chars()

    if run_all or only_scenes:
        scene_map = phase_scenes()

    if run_all or only_props:
        prop_map = phase_props()

    # 汇总
    char_ok = sum(1 for v in char_map.values() if v.get("file"))
    scene_ok = sum(1 for v in scene_map.values() if v.get("file"))
    prop_ok = sum(1 for v in prop_map.values() if v.get("file"))

    print(f"\n{'=' * 60}")
    print(f"🏁 资产生成完成!")
    if char_map:
        print(f"🎨 角色参考图: {char_ok}/{len(char_map)} 张（每张含四宫格多视角）")
    if scene_map:
        print(f"🏙️ 场景四宫格: {scene_ok}/{len(scene_map)} 张（每张含4视角合成）")
    if prop_map:
        print(f"🔧 道具三视图: {prop_ok}/{len(prop_map)} 张（每张含3视角合成）")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
