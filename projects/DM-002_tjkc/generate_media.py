#!/usr/bin/env python3
"""
短剧媒体生成脚本
Phase 1: 生成角色参考图 (single configured image model)
Phase 2: 参考角色图生成分镜图片 (single configured image model)
Phase 3: 参考分镜图生成视频 (Veo)
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

    config_path = Path("/data/dongman/.config/api_keys.json")
    if config_path.exists():
        with open(config_path) as f:
            config = json.load(f)
        api_key = config.get("gemini_api_key")
        # 兼容两种字段名
        base_url = config.get("gemini_base_url") or config.get("base_url")
        image_model = config.get("gemini_image_model", image_model)

    # 环境变量优先
    api_key = os.environ.get("GEMINI_API_KEY", api_key)
    base_url = os.environ.get("GEMINI_BASE_URL", base_url)
    image_model = os.environ.get("GEMINI_IMAGE_MODEL", image_model)

    # 去掉 base_url 中的 API 版本路径（如 /v1beta2），SDK 会自动拼接
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

    # 主要角色: ### 角色X：名字（英文名）
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

    # 次要角色: AI关键词：
    secondary_blocks = re.findall(
        r'###\s+.*?——(.*?)\n(.*?)(?=###|\Z)', content, re.DOTALL
    )
    for sec_name_raw, sec_block in secondary_blocks:
        sec_name = sec_name_raw.strip().split('（')[0].strip()
        # 去掉角色X格式的（已经被上面捕获）
        if re.match(r'角色\d+', sec_name):
            continue
        prompt_match = re.search(r'\*{0,2}AI关键词\*{0,2}[：:]\s*(.+)', sec_block)
        if prompt_match:
            characters.append({
                "name": sec_name,
                "ai_prompt": prompt_match.group(1).strip()
            })

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
                "Generate anime character reference sheets. "
                f"Return exactly {len(batch)} separate images in the same order as the numbered list below.\n"
                "Each image: 16:9 landscape, white background, left side face close-up, right side full-body views(front/side/back), clean lineart.\n\n"
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


def generate_episode_storyboards(ep_dir: Path, config: dict, char_uploaded: dict) -> dict:
    """逐个部分生成6宫格关键帧图片，每次只传本部分涉及角色的参考图"""
    results = {"images": 0, "failed": 0}

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

        # 汇总6格描述
        grids = part.get("storyboard_6grid", [])
        grid_descs = []
        for g in grids:
            prompt = g.get("ai_image_prompt", "")
            if prompt:
                grid_descs.append(f"Panel {g['grid_number']}: {prompt}")

        # 收集本部分涉及的角色
        part_chars = set()
        for g in grids:
            for c in g.get("characters", []):
                if c.get("name"):
                    part_chars.add(c["name"])

        # 构建 contents：角色参考图（带标注） + prompt
        content_parts = []
        ref_names = []
        for char_name in part_chars:
            if char_name in char_uploaded and char_uploaded[char_name]:
                content_parts.append(
                    types.Part(text=f"[Character reference: {char_name}]")
                )
                for part_obj in char_uploaded[char_name]:
                    content_parts.append(part_obj)
                ref_names.append(char_name)

        grid_text = "\n".join(grid_descs)
        prompt_text = (
            f"Create a single composite image showing a 2x3 grid (2 columns, 3 rows) "
            f"of anime keyframes. Each panel shows one scene:\n{grid_text}\n\n"
            f"9:16 aspect ratio, high quality anime style, cinematic, consistent character design."
        )

        if ref_names:
            prompt_text += (
                f"\n\nIMPORTANT: Use the character reference images above for: {', '.join(ref_names)}. "
                f"Keep character appearances, clothing, and colors consistent with the references."
            )

        content_parts.append(types.Part(text=prompt_text))

        print(f"  🎨 生成{part_label}半部分分镜图（参考角色: {', '.join(ref_names) if ref_names else '无'}）...")

        try:
            images = generate_images_with_model(
                content_parts,
                request_tag=f"storyboard_single_{part.get('video_id', part_label)}",
            )

            if images:
                image = Image.open(io.BytesIO(images[0].inline_data.data))
                image.save(str(img_path))
                print(f"  ✅ {part_label}半部分分镜图: {img_path.name}")
                results["images"] += 1
            else:
                print(f"  ⚠️ {part_label}半部分分镜图未生成")
                results["failed"] += 1

        except Exception as e:
            print(f"  ❌ {part_label}半部分分镜图生成失败: {e}")
            results["failed"] += 1

        # 间隔避免限频
        time.sleep(2)

    return results


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

            grids = part.get("storyboard_6grid", [])
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
                f"2x3 grid (2 columns, 3 rows), anime style, 9:16, cinematic.\n"
                f"Scenes:\n{"\n".join(grid_descs)}"
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


# ========== Phase 3: 视频生成（使用 REST API 直接调用） ==========

def _video_api_request(method: str, path: str, body: dict = None) -> dict:
    """直接通过 REST API 调用视频生成接口"""
    api_base = base_url.rstrip("/") if base_url else "https://generativelanguage.googleapis.com"
    url = f"{api_base}/v1beta/models/{path}"
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key,
    }
    if method == "post":
        resp = requests.post(url, json=body, headers=headers, timeout=60)
    else:
        resp = requests.get(url, headers=headers, timeout=60)
    resp.raise_for_status()
    return resp.json()


def _poll_operation(op_name: str, max_wait: int = 600) -> dict:
    """轮询 LRO 操作直到完成"""
    api_base = base_url.rstrip("/") if base_url else "https://generativelanguage.googleapis.com"
    url = f"{api_base}/v1beta/{op_name}"
    headers = {"x-goog-api-key": api_key}
    elapsed = 0
    while elapsed < max_wait:
        resp = requests.get(url, headers=headers, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        if data.get("done"):
            return data
        time.sleep(15)
        elapsed += 15
        print(f"  ⏳ 视频生成中... ({elapsed}s)")
    return {"done": False, "error": "timeout"}


def _download_video(video_uri: str, output_path: str) -> bool:
    """下载生成的视频文件"""
    try:
        # video_uri 可能是 files/xxx 格式，需要拼出完整下载 URL
        api_base = base_url.rstrip("/") if base_url else "https://generativelanguage.googleapis.com"
        if video_uri.startswith("http"):
            download_url = video_uri
        else:
            # 使用 files API 下载
            download_url = f"{api_base}/v1beta/{video_uri}:download?alt=media"
        headers = {"x-goog-api-key": api_key}
        resp = requests.get(download_url, headers=headers, timeout=300, stream=True)
        resp.raise_for_status()
        with open(output_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"  ⚠️ 视频下载失败: {e}")
        # 尝试用 SDK 下载
        try:
            from google.genai.types import FileData
            client.files.download(file=video_uri, download_path=output_path)
            return True
        except Exception as e2:
            print(f"  ⚠️ SDK 下载也失败: {e2}")
            return False


def generate_video(prompt: str, output_path: str) -> bool:
    """调用 Veo 生成视频（纯文本） - 使用 REST API"""
    try:
        body = {
            "instances": [{"prompt": prompt}],
            "parameters": {
                "aspectRatio": "9:16",
                "personGeneration": "allow_adult",
            }
        }
        result = _video_api_request("post", "veo3.1-components:predictLongRunning", body)

        op_name = result.get("name")
        if not op_name:
            print(f"  ⚠️ 未获取到操作 ID: {json.dumps(result, ensure_ascii=False)[:200]}")
            return False

        print(f"  📋 操作: {op_name}")
        data = _poll_operation(op_name)

        if not data.get("done"):
            print(f"  ⏳ 视频超时: {Path(output_path).name}")
            return False

        # 提取视频
        response = data.get("response", {})
        videos = response.get("generateVideoResponse", {}).get("generatedSamples", [])
        if not videos:
            videos = response.get("generatedVideos", [])
        if not videos:
            print(f"  ⚠️ 视频无结果: {json.dumps(data, ensure_ascii=False)[:300]}")
            return False

        video_uri = videos[0].get("video", {}).get("uri", "") or videos[0].get("video", {}).get("name", "")
        if not video_uri:
            print(f"  ⚠️ 无视频 URI: {json.dumps(videos[0], ensure_ascii=False)[:200]}")
            return False

        if _download_video(video_uri, output_path):
            print(f"  ✅ 视频已保存: {Path(output_path).name}")
            return True
        return False

    except requests.HTTPError as e:
        print(f"  ❌ 视频 API 错误: {e.response.status_code} - {e.response.text[:300]}")
        return False
    except Exception as e:
        print(f"  ❌ 视频失败: {e}")
        return False


def generate_video_with_image(prompt: str, image_path: str, output_path: str) -> bool:
    """调用 Veo 使用参考图生成视频（图生视频） - 使用 REST API"""
    try:
        with open(image_path, "rb") as fh:
            file_bytes = fh.read()
        img_b64 = base64.b64encode(file_bytes).decode("utf-8")

        body = {
            "instances": [{
                "prompt": prompt,
                "image": {
                    "bytesBase64Encoded": img_b64,
                    "mimeType": "image/png"
                }
            }],
            "parameters": {
                "aspectRatio": "9:16",
                "personGeneration": "allow_adult",
            }
        }
        result = _video_api_request("post", "veo3.1-components:predictLongRunning", body)

        op_name = result.get("name")
        if not op_name:
            print(f"  ⚠️ 未获取到操作 ID: {json.dumps(result, ensure_ascii=False)[:200]}")
            return False

        print(f"  📋 操作: {op_name}")
        data = _poll_operation(op_name)

        if not data.get("done"):
            print(f"  ⏳ 图生视频超时: {Path(output_path).name}")
            return False

        response = data.get("response", {})
        videos = response.get("generateVideoResponse", {}).get("generatedSamples", [])
        if not videos:
            videos = response.get("generatedVideos", [])
        if not videos:
            print(f"  ⚠️ 图生视频无结果: {json.dumps(data, ensure_ascii=False)[:300]}")
            return False

        video_uri = videos[0].get("video", {}).get("uri", "") or videos[0].get("video", {}).get("name", "")
        if not video_uri:
            print(f"  ⚠️ 无视频 URI: {json.dumps(videos[0], ensure_ascii=False)[:200]}")
            return False

        if _download_video(video_uri, output_path):
            print(f"  ✅ 图生视频: {Path(output_path).name}")
            return True
        return False

    except requests.HTTPError as e:
        print(f"  ❌ 图生视频 API 错误: {e.response.status_code} - {e.response.text[:300]}")
        return False
    except Exception as e:
        print(f"  ❌ 图生视频失败: {e}")
        return False


# ========== 逐集处理 ==========

def process_episode_pair(ep_payloads: list, char_uploaded: dict, skip_video: bool = False):
    """处理两集（或不足两集）：分镜图一次批量生成，视频仍按集处理"""
    if not ep_payloads:
        return None

    labels = [f"{ep_num}:{cfg.get('episode_title', '未知')}" for _, ep_num, cfg in ep_payloads]
    print(f"\n{'='*50}")
    print(f"📺 批次处理 {' | '.join(labels)}")
    print(f"{'='*50}")

    results = {"images": 0, "videos": 0, "failed": 0}

    # Phase 2: 两集一批
    sb_results = generate_storyboards_for_two_episodes(ep_payloads, char_uploaded)
    results["images"] += sb_results["images"]
    results["failed"] += sb_results["failed"]

    # Phase 3: 逐集逐部分视频
    if skip_video:
        return results

    for ep_dir, ep_num, config in ep_payloads:
        for part_key, part_label in [("part_a", "上"), ("part_b", "下")]:
            part = config.get(part_key)
            if not part:
                continue

            video_id = part["video_id"]
            video_prompt = part.get("video_prompt", "")
            if not video_prompt:
                continue

            video_filename = f"{video_id}.mp4"
            video_path = str(ep_dir / video_filename)

            if os.path.exists(video_path):
                print(f"  ⏭️ 视频已存在: {video_filename}")
                results["videos"] += 1
                continue

            storyboard_path = str(ep_dir / f"{video_id}_storyboard.png")
            if os.path.exists(storyboard_path):
                print(f"  🎬 {ep_num}-{part_label}: 使用分镜图参考生成视频...")
                if generate_video_with_image(video_prompt, storyboard_path, video_path):
                    results["videos"] += 1
                else:
                    print("  🔄 降级为纯文本生成...")
                    if generate_video(video_prompt, video_path):
                        results["videos"] += 1
                    else:
                        results["failed"] += 1
            else:
                print(f"  🎬 {ep_num}-{part_label}: 纯文本生成视频...")
                if generate_video(video_prompt, video_path):
                    results["videos"] += 1
                else:
                    results["failed"] += 1

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
    skip_video = "--skip-video" in sys.argv
    only_chars = "--only-chars" in sys.argv

    print(f"🎬 短剧媒体生成")
    print(f"📁 项目: {PROJECT_DIR}")
    print(f"📺 范围: EP{start_ep:02d} - EP{end_ep:02d}")

    # ===== Phase 1: 角色参考图 =====
    if skip_chars:
        print("\n⏭️ 跳过角色参考图生成（使用已有）")
        ref_index_path = CHARACTERS_DIR / "ref_index.json"
        if ref_index_path.exists():
            with open(ref_index_path) as f:
                char_ref_map = json.load(f)
        else:
            char_ref_map = {}
    else:
        char_ref_map = phase1_generate_characters()

    # ===== 加载角色参考图（inline data，不依赖 files.upload API） =====
    if only_chars:
        print("\n⏹️ 仅角色模式：跳过分镜与视频生成")
        print(f"\n{'='*60}")
        print(f"🏁 角色生成完成!")
        print(f"🎨 角色参考图: {sum(len(v) for v in char_ref_map.values())} 张")
        print(f"{'='*60}")
        return

    print("\n📎 加载角色参考图（inline data）...")
    char_uploaded = load_character_refs_inline(char_ref_map) if char_ref_map else {}
    print(f"   已加载 {sum(len(v) for v in char_uploaded.values())} 张角色参考图")

    # ===== Phase 2 & 3: 两集一批生成分镜，视频按原逻辑 =====
    total = {"images": 0, "videos": 0, "failed": 0}

    ep_payloads = []
    for ep in range(start_ep, end_ep + 1):
        ep_num = f"EP{ep:02d}"
        ep_dir = EPISODES_DIR / ep_num
        config_path = ep_dir / "storyboard_config.json"
        if not ep_dir.exists() or not config_path.exists():
            print(f"⚠️ {ep_num} 不存在或缺少 storyboard_config.json，跳过")
            continue
        with open(config_path) as f:
            config = json.load(f)
        ep_payloads.append((ep_dir, ep_num, config))

    for i in range(0, len(ep_payloads), 2):
        pair = ep_payloads[i:i + 2]
        result = process_episode_pair(pair, char_uploaded, skip_video)
        if result:
            for k in total:
                total[k] += result[k]

    # ===== 媒体索引 =====
    generate_media_index(start_ep, end_ep)

    print(f"\n{'='*60}")
    print(f"🏁 全部完成!")
    print(f"🎨 角色参考图: {sum(len(v) for v in char_ref_map.values())} 张")
    print(f"🖼️ 分镜图片: {total['images']} 张")
    print(f"🎬 视频: {total['videos']} 个")
    print(f"❌ 失败: {total['failed']} 个")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
