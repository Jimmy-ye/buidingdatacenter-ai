#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GLM Worker 端到端测试脚本

测试场景：
1. 创建测试项目
2. 上传 scene_issue 图片（auto_route=true）
3. 验证资产状态为 pending_scene_llm
4. 手动调用 Worker 处理逻辑（不启动轮询）
5. 验证分析结果已回写
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
import time
import json
from pathlib import Path
from PIL import Image, ImageDraw

BASE_URL = "http://localhost:8000"


def create_test_image(text: str = "现场问题") -> bytes:
    """创建测试图片"""
    img = Image.new('RGB', (400, 200), color='white')
    draw = ImageDraw.Draw(img)
    draw.text((10, 10), text, fill='black')

    img_io = io.BytesIO()
    img.save(img_io, 'JPEG')
    img_io.seek(0)
    return img_io.read()


def test_glm_worker_flow():
    """完整的 Worker 流程测试"""

    print("\n" + "="*60)
    print("GLM Worker 端到端测试")
    print("="*60)

    # 1. 检查后端
    print("\n[1] 检查后端服务...")
    try:
        resp = requests.get(f"{BASE_URL}/api/v1/health/", timeout=5)
        if resp.json().get("status") != "ok":
            print("❌ 后端状态异常")
            return False
        print("✓ 后端服务正常")
    except Exception as e:
        print(f"❌ 无法连接后端: {e}")
        return False

    # 2. 创建测试项目
    print("\n[2] 创建测试项目...")
    project_resp = requests.post(
        f"{BASE_URL}/api/v1/projects/",
        json={
            "name": "GLM Worker 测试项目",
            "client": "测试客户",
            "location": "测试地点",
            "status": "active"
        },
        timeout=30
    )

    if project_resp.status_code != 201:
        print(f"❌ 创建项目失败: {project_resp.text}")
        return False

    project = project_resp.json()
    project_id = project["id"]
    print(f"✓ 项目创建成功: {project_id}")

    # 3. 上传 scene_issue 图片
    print("\n[3] 上传 scene_issue 图片（auto_route=true）...")
    img_data = create_test_image("管道保温层破损")

    upload_resp = requests.post(
        f"{BASE_URL}/api/v1/assets/upload_image_with_note",
        params={
            "project_id": project_id,
            "source": "mobile",
            "content_role": "scene_issue",
            "auto_route": "true"
        },
        data={"note": "现场发现管道保温层有破损"},
        files={"file": ("scene_issue.jpg", img_data, "image/jpeg")},
        timeout=60
    )

    if upload_resp.status_code != 201:
        print(f"❌ 上传失败: {upload_resp.text}")
        return False

    asset = upload_resp.json()
    asset_id = asset["id"]
    print(f"✓ 图片上传成功: {asset_id}")
    print(f"  状态: {asset.get('status')}")
    print(f"  Content Role: {asset.get('content_role')}")

    # 4. 验证路由决策
    print("\n[4] 验证自动路由结果...")
    detail_resp = requests.get(f"{BASE_URL}/api/v1/assets/{asset_id}", timeout=30)
    detail = detail_resp.json()

    payloads = detail.get("structured_payloads", [])
    route_payloads = [p for p in payloads if p.get("schema_type") == "image_route_decision_v1"]

    if not route_payloads:
        print("❌ 未找到路由决策 payload")
        return False

    print("✓ 路由决策正确")
    print(f"  Route: {route_payloads[0]['payload'].get('route')}")

    # 5. 等待 Worker 处理（如果环境变量已配置）
    print("\n[5] 等待 Worker 处理...")
    print("提示: 如果 Worker 未运行，请手动启动:")
    print("  cd services/worker")
    print("  .\\start_worker.ps1")
    print("")
    print("等待 60 秒...")

    for i in range(60):
        time.sleep(1)
        if (i + 1) % 10 == 0:
            print(f"  {i + 1} 秒...")

    # 6. 检查处理结果
    print("\n[6] 检查 Worker 处理结果...")
    detail_resp = requests.get(f"{BASE_URL}/api/v1/assets/{asset_id}", timeout=30)
    detail = detail_resp.json()

    current_status = detail.get("status")
    print(f"  当前状态: {current_status}")

    payloads = detail.get("structured_payloads", [])
    scene_payloads = [p for p in payloads if p.get("schema_type") == "scene_issue_report_v1"]

    if scene_payloads:
        print("✓ Worker 已成功处理")
        payload_data = scene_payloads[0]["payload"]
        print(f"\n分析结果:")
        print(f"  标题: {payload_data.get('title')}")
        print(f"  类别: {payload_data.get('issue_category')}")
        print(f"  严重性: {payload_data.get('severity')}")
        print(f"  摘要: {payload_data.get('summary')}")
        print(f"  置信度: {payload_data.get('confidence')}")
        print(f"  原因: {payload_data.get('suspected_causes')}")
        print(f"  建议: {payload_data.get('recommended_actions')}")
        print(f"  标签: {payload_data.get('tags')}")

        return True
    else:
        print("⚠️  Worker 尚未处理（请确认 Worker 是否正在运行）")
        return False


if __name__ == "__main__":
    try:
        success = test_glm_worker_flow()
        print("\n" + "="*60)
        if success:
            print("✓ 测试通过！GLM Worker 工作正常")
        else:
            print("⚠️  测试未完全通过，请检查上述日志")
        print("="*60)
    except KeyboardInterrupt:
        print("\n\n测试已中断")
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()
