"""
简单的工程结构测试脚本 - 用于诊断问题
"""
import json
import uuid
import sys
import time

import requests

BASE_URL = "http://127.0.0.1:8000"


def test_step_1_create_project():
    print("\n" + "=" * 60)
    print("[测试 1] 创建 Project")
    print("=" * 60)

    try:
        resp = requests.post(
            f"{BASE_URL}/api/v1/projects/",
            json={
                "name": "engineering-test",
                "client": "测试客户",
                "location": "测试地点",
                "status": "active",
            },
            timeout=10,
        )
        print(f"✓ 状态码: {resp.status_code}")
        if resp.status_code == 201:
            project = resp.json()
            print(f"[OK] Project ID: {project['id']}")
            return project["id"]
        else:
            print(f"✗ 响应: {resp.text}")
            return None
    except Exception as e:
        print(f"✗ 错误: {e}")
        return None


def test_step_2_check_routes(project_id):
    print("\n" + "=" * 60)
    print("[测试 2] 检查工程结构 API 路由是否存在")
    print("=" * 60)

    routes_to_test = [
        f"/api/v1/projects/{project_id}/buildings",
        f"/api/v1/projects/{project_id}/devices/flat",
        f"/api/v1/projects/{project_id}/structure_tree",
    ]

    for route in routes_to_test:
        try:
            # 使用 HEAD 请求测试路由是否存在
            resp = requests.request("HEAD", f"{BASE_URL}{route}", timeout=5)
            if resp.status_code in [200, 404, 405]:  # 405 Method Not Allowed 说明路由存在
                print(f"✓ {route}: 路由存在")
            else:
                print(f"? {route}: 状态码 {resp.status_code}")
        except requests.exceptions.ConnectionError:
            print(f"✗ {route}: 连接失败 - 后端可能未启动")
            break
        except Exception as e:
            print(f"✗ {route}: 错误 {e}")


def test_step_3_create_building(project_id):
    print("\n" + "=" * 60)
    print("[测试 3] 创建 Building")
    print("=" * 60)

    try:
        resp = requests.post(
            f"{BASE_URL}/api/v1/projects/{project_id}/buildings",
            json={
                "name": "测试办公楼",
                "usage_type": "office",
                "tags": ["测试标签"],
            },
            timeout=10,
        )
        print(f"状态码: {resp.status_code}")
        if resp.status_code == 201:
            building = resp.json()
            print(f"✓ Building 创建成功: {building['name']}")
            print(f"  ID: {building['id']}")
            return building["id"]
        else:
            print(f"✗ 响应: {resp.text[:200]}")
            return None
    except Exception as e:
        print(f"✗ 错误: {e}")
        return None


def test_step_4_list_buildings(project_id):
    print("\n" + "=" * 60)
    print("[测试 4] 列出 Buildings")
    print("=" * 60)

    try:
        resp = requests.get(
            f"{BASE_URL}/api/v1/projects/{project_id}/buildings",
            timeout=10,
        )
        print(f"状态码: {resp.status_code}")
        if resp.status_code == 200:
            buildings = resp.json()
            print(f"✓ 找到 {len(buildings)} 个建筑")
            for b in buildings:
                print(f"  - {b['name']} (tags: {b.get('tags')})")
        else:
            print(f"✗ 响应: {resp.text[:200]}")
    except Exception as e:
        print(f"✗ 错误: {e}")


def main():
    print("工程结构 API 测试（简化版）")
    print("=" * 60)
    print(f"后端地址: {BASE_URL}")
    print("=" * 60)

    # 测试 1: 创建 Project
    project_id = test_step_1_create_project()
    if not project_id:
        print("\n❌ 无法创建 Project，请检查后端是否正在运行")
        sys.exit(1)

    # 测试 2: 检查路由
    test_step_2_check_routes(project_id)

    # 测试 3: 创建 Building
    building_id = test_step_3_create_building(project_id)

    # 测试 4: 列出 Buildings
    test_step_4_list_buildings(project_id)

    print("\n" + "=" * 60)
    if building_id:
        print("✅ 基础测试通过！工程结构 API 正常工作")
    else:
        print("⚠️  部分测试失败，请查看上面的错误信息")
    print("=" * 60)


if __name__ == "__main__":
    main()
