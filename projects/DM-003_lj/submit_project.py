#!/usr/bin/env python3
"""
提交 DM-003《绿迹》全部 Seedance 视频任务

用法:
    python submit_project.py               # 模拟提交（realSubmit=false）
    python submit_project.py --real        # 真实提交（realSubmit=true）
    python submit_project.py --batch 10    # 设置批次大小（默认 25）
    python submit_project.py --ep 1-5      # 只提交指定集数
"""
import json
import base64
import os
import sys
import mimetypes
from datetime import datetime, timezone

import requests

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
API_BASE = "http://localhost:3456"
DEFAULT_BATCH_SIZE = 25
TASKS_FILE = os.path.join(PROJECT_DIR, "seedance_project_tasks.json")


def expand_reference_files(ref_paths, project_dir):
    """将相对路径列表展开为 base64 对象列表"""
    result = []
    for rel_path in ref_paths:
        abs_path = os.path.join(project_dir, rel_path)
        file_name = os.path.basename(rel_path)
        mime_type = mimetypes.guess_type(abs_path)[0] or "image/png"
        if not os.path.exists(abs_path):
            print(f"  ⚠️ 文件不存在: {abs_path}")
            continue
        with open(abs_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        result.append({
            "fileName": file_name,
            "base64": f"data:{mime_type};base64,{b64}",
            "fileType": mime_type,
        })
    return result


def filter_by_episodes(tasks, ep_range):
    """按集数过滤任务"""
    if not ep_range:
        return tasks
    ep_codes = {f"EP{e:02d}" for e in ep_range}
    return [t for t in tasks if any(tag in ep_codes for tag in t.get("tags", []))]


def parse_ep_range(arg):
    """解析集数范围: '1', '01', '1-5'"""
    if "-" in arg:
        s, e = arg.split("-", 1)
        return list(range(int(s), int(e) + 1))
    return [int(arg)]


def submit_batch(batch_tasks, batch_idx, real_submit):
    """提交一个批次的任务"""
    payload_tasks = []
    for task in batch_tasks:
        payload = {
            "prompt": task["prompt"],
            "description": task.get("description", ""),
            "modelConfig": task.get("modelConfig", {}),
            "referenceFiles": expand_reference_files(task["referenceFiles"], PROJECT_DIR),
            "realSubmit": real_submit,
            "priority": task.get("priority", 1),
            "tags": task.get("tags", []),
        }
        payload_tasks.append(payload)

    desc_list = [t.get("description", "?")[:30] for t in batch_tasks]
    print(f"\n📤 批次 {batch_idx}: {len(payload_tasks)} 条任务")
    for d in desc_list:
        print(f"   - {d}")

    try:
        resp = requests.post(
            f"{API_BASE}/api/tasks/push",
            json={"tasks": payload_tasks},
            timeout=120
        )
        result = resp.json()
        if resp.status_code == 200 and result.get("success"):
            codes = result.get("taskCodes", [])
            print(f"   ✅ 成功 → {len(codes)} 个 taskCode")
            return True, codes, None
        else:
            err = result.get("error", str(result))
            print(f"   ❌ 失败: {err}")
            return False, [], err
    except Exception as ex:
        print(f"   ❌ 请求异常: {ex}")
        return False, [], str(ex)


def main():
    # 解析参数
    real_submit = "--real" in sys.argv
    batch_size = DEFAULT_BATCH_SIZE
    ep_range = None

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--batch" and i + 1 < len(args):
            batch_size = int(args[i + 1])
            i += 2
        elif args[i] == "--ep" and i + 1 < len(args):
            ep_range = parse_ep_range(args[i + 1])
            i += 2
        else:
            i += 1

    # 加载任务
    if not os.path.exists(TASKS_FILE):
        print(f"❌ {TASKS_FILE} 不存在")
        sys.exit(1)

    with open(TASKS_FILE, encoding="utf-8") as f:
        data = json.load(f)

    tasks = data.get("tasks", [])
    project_id = data.get("project_id", "DM-003")
    project_name = data.get("project_name", "")

    # 过滤
    tasks = filter_by_episodes(tasks, ep_range)

    print(f"{'='*60}")
    print(f"📦 项目: {project_id} 《{project_name}》")
    print(f"📋 任务数: {len(tasks)}")
    print(f"📦 批次大小: {batch_size}")
    print(f"🔗 API: {API_BASE}")
    print(f"🎯 realSubmit: {real_submit}")
    if ep_range:
        print(f"🎬 指定集数: EP{ep_range[0]:02d}-EP{ep_range[-1]:02d}")
    print(f"{'='*60}")

    if not tasks:
        print("⚠️ 无可提交任务")
        return

    # 按批次提交
    all_codes = []
    failed_items = []
    total_batches = (len(tasks) + batch_size - 1) // batch_size

    for bi in range(total_batches):
        start = bi * batch_size
        end = min(start + batch_size, len(tasks))
        batch = tasks[start:end]
        ok, codes, err = submit_batch(batch, bi + 1, real_submit)
        if ok:
            all_codes.extend(codes)
        else:
            for t in batch:
                failed_items.append({
                    "description": t.get("description", ""),
                    "error": err
                })

    # 汇总
    print(f"\n{'='*60}")
    print(f"✅ 提交完成")
    print(f"   总任务: {len(tasks)}")
    print(f"   成功: {len(all_codes)}")
    print(f"   失败: {len(failed_items)}")
    if all_codes:
        print(f"   TaskCodes: {len(all_codes)} 个")
    print(f"{'='*60}")

    # 生成提交报告
    report = {
        "project_id": project_id,
        "project_name": project_name,
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "api_base": API_BASE,
        "real_submit": real_submit,
        "total_tasks": len(tasks),
        "submitted_tasks": len(all_codes),
        "failed_tasks": len(failed_items),
        "task_codes": all_codes,
        "failed_items": failed_items,
    }

    report_path = os.path.join(PROJECT_DIR, "submission_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n📄 报告: {report_path}")


if __name__ == "__main__":
    main()
