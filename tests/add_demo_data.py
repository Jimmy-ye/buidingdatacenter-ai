"""
添加演示数据到 BDC-AI 系统

功能：
1. 创建演示项目
2. 创建工程结构（Building/Zone/System/Device）
3. 上传演示图片资产
"""

import requests
import os
from pathlib import Path

BASE_URL = "http://localhost:8000/api/v1"


def create_demo_project():
    """创建演示项目"""
    print("=" * 60)
    print("步骤 1: 创建演示项目")
    print("=" * 60)

    project_data = {
        "name": "演示项目 - 华润广场",
        "client": "华润置地",
        "location": "上海市浦东新区",
        "type": "商业综合体",
        "status": "运行中",
        "tags": {
            "city": "上海",
            "project_type": "商业综合体",
            "environment": "test",
            "demo": True
        }
    }

    response = requests.post(f"{BASE_URL}/projects/", json=project_data)
    if response.status_code == 201:
        project = response.json()
        print(f"[OK] 项目创建成功！")
        print(f"  项目 ID: {project['id']}")
        print(f"  项目名称: {project['name']}")
        print(f"  环境标识: test (标题会显示 [TEST])")
        return project['id']
    else:
        print(f"[FAIL] 项目创建失败: {response.status_code}")
        print(f"  错误: {response.text}")
        raise Exception("项目创建失败")


def create_engineering_structure(project_id: str):
    """创建工程结构"""
    print(f"\n{'=' * 60}")
    print("步骤 2: 创建工程结构")
    print(f"{'=' * 60}")

    # 1. 创建 Building
    print("\n[1/4] 创建 Building...")
    building_data = {
        "name": "A座办公楼",
        "usage_type": "办公楼",
        "floor_area": 45000,
        "year_built": 2020,
        "tags": ["A区", "办公楼"]
    }
    response = requests.post(f"{BASE_URL}/projects/{project_id}/buildings", json=building_data)
    if response.status_code == 201:
        building = response.json()
        building_id = building['id']
        print(f"  [OK] Building ID: {building_id}")
    else:
        print(f"  [FAIL] Building 创建失败: {response.text}")
        raise Exception("Building 创建失败")

    # 2. 创建 Zone
    print("\n[2/4] 创建 Zone...")
    zone_data = {
        "name": "5F办公区",
        "type": "办公区",
        "tags": ["5F", "办公区"]
    }
    response = requests.post(f"{BASE_URL}/buildings/{building_id}/zones", json=zone_data)
    if response.status_code == 201:
        zone = response.json()
        zone_id = zone['id']
        print(f"  [OK] Zone ID: {zone_id}")
    else:
        print(f"  [FAIL] Zone 创建失败: {response.text}")
        raise Exception("Zone 创建失败")

    # 3. 创建 System
    print("\n[3/4] 创建 System...")
    system_data = {
        "type": "HVAC",
        "name": "空调系统-HVAC",
        "description": "暖通空调系统",
        "tags": ["HVAC", "空调"]
    }
    response = requests.post(f"{BASE_URL}/buildings/{building_id}/systems", json=system_data)
    if response.status_code == 201:
        system = response.json()
        system_id = system['id']
        print(f"  [OK] System ID: {system_id}")
    else:
        print(f"  [FAIL] System 创建失败: {response.text}")
        raise Exception("System 创建失败")

    # 4. 创建 Device
    print("\n[4/4] 创建 Device...")
    device_data = {
        "device_type": "fcu",
        "model": "风机盘管FCU-05",
        "rated_power": 0.12,
        "serial_no": "FCU-2025-001",
        "zone_id": str(zone_id),
        "tags": ["FCU", "运行中"]
    }
    response = requests.post(f"{BASE_URL}/systems/{system_id}/devices", json=device_data)
    if response.status_code == 201:
        device = response.json()
        device_id = device['id']
        print(f"  [OK] Device ID: {device_id}")
        print(f"\n[OK] 工程结构创建完成！")
        return building_id, zone_id, system_id, device_id
    else:
        print(f"  [FAIL] Device 创建失败: {response.text}")
        raise Exception("Device 创建失败")


def upload_demo_assets(project_id: str, device_id: str, zone_id: str, system_id: str):
    """上传演示资产"""
    print(f"\n{'=' * 60}")
    print("步骤 3: 上传演示资产")
    print(f"{'=' * 60}")

    # 检查是否有演示图片
    demo_images = [
        ("tests/changsha-表具", "meter"),
        ("tests/changsha-现场", "scene_issue")
    ]

    total_uploaded = 0

    for image_dir, content_role in demo_images:
        dir_path = Path(image_dir)
        if not dir_path.exists():
            print(f"\n[WARN] 目录不存在: {image_dir}")
            continue

        image_files = list(dir_path.glob("*.jpg")) + list(dir_path.glob("*.png"))
        if not image_files:
            print(f"\n[WARN] 目录中没有图片: {image_dir}")
            continue

        print(f"\n上传 {content_role} 图片:")
        for i, img_path in enumerate(image_files[:4], 1):  # 每个类型最多上传4张
            print(f"  [{i}] {img_path.name}")

            # 根据内容角色选择绑定位置
            params = {
                "project_id": project_id,
                "source": "demo_upload",
                "content_role": content_role,
                "title": f"演示_{img_path.name}",
                "note": f"演示数据 - {content_role}",
                "auto_route": "true"
            }

            if content_role == "meter":
                params["device_id"] = str(device_id)
            else:  # scene_issue
                params["zone_id"] = str(zone_id)
                params["system_id"] = str(system_id)

            try:
                with open(img_path, "rb") as f:
                    files = {"file": (img_path.name, f, "image/jpeg")}
                    response = requests.post(
                        f"{BASE_URL}/assets/upload_image_with_note",
                        params=params,
                        files=files
                    )

                if response.status_code == 201:
                    asset = response.json()
                    print(f"    [OK] Asset ID: {asset['id']}")
                    total_uploaded += 1
                else:
                    print(f"    [FAIL] 上传失败: {response.status_code}")
            except Exception as e:
                print(f"    [FAIL] 上传异常: {e}")

    print(f"\n[OK] 共上传 {total_uploaded} 张演示资产")
    return total_uploaded


def create_test_assets_without_images(project_id: str, device_id: str):
    """如果没有图片文件，直接创建文本资产"""
    print(f"\n{'=' * 60}")
    print("步骤 3: 创建演示资产（无图片）")
    print(f"{'=' * 60}")

    demo_assets = [
        {
            "modality": "text",
            "content_role": "inspection_report",
            "title": "5F风机盘管巡检记录",
            "description": "2025年1月例行巡检，设备运行正常",
            "device_id": str(device_id)
        },
        {
            "modality": "text",
            "content_role": "maintenance_log",
            "title": "风机盘管维护记录",
            "description": "定期更换滤网，清洁盘管",
            "device_id": str(device_id)
        },
        {
            "modality": "table",
            "content_role": "energy_data",
            "title": "能耗记录表",
            "description": "2025年1月能耗数据",
            "device_id": str(device_id)
        }
    ]

    uploaded = 0
    for i, asset_data in enumerate(demo_assets, 1):
        print(f"\n[{i}/{len(demo_assets)}] 创建资产: {asset_data['title']}")

        response = requests.post(
            f"{BASE_URL}/assets/",
            params={
                "project_id": project_id,
                "modality": asset_data["modality"],
                "source": "demo",
                "device_id": asset_data["device_id"],
                "title": asset_data["title"],
                "description": asset_data["description"],
                "content_role": asset_data["content_role"]
            }
        )

        if response.status_code == 201:
            asset = response.json()
            print(f"  [OK] Asset ID: {asset['id']}")
            uploaded += 1
        else:
            print(f"  [FAIL] 创建失败: {response.status_code}")

    print(f"\n[OK] 共创建 {uploaded} 条演示资产")
    return uploaded


def verify_data(project_id: str):
    """验证创建的数据"""
    print(f"\n{'=' * 60}")
    print("步骤 4: 验证数据")
    print(f"{'=' * 60}")

    # 查询资产
    response = requests.get(
        f"{BASE_URL}/assets",
        params={"project_id": project_id}
    )

    if response.status_code == 200:
        assets = response.json()
        print(f"\n[OK] 查询到 {len(assets)} 条资产")

        if assets:
            print("\n资产列表:")
            for asset in assets[:5]:  # 只显示前5条
                print(f"  - {asset.get('title', asset.get('id'))}")
                print(f"    类型: {asset.get('modality')} | 角色: {asset.get('content_role')}")
            if len(assets) > 5:
                print(f"  ... 还有 {len(assets) - 5} 条")
    else:
        print(f"[FAIL] 查询失败: {response.status_code}")

    # 查询工程结构树
    response = requests.get(f"{BASE_URL}/projects/{project_id}/structure_tree")
    if response.status_code == 200:
        tree = response.json()
        print(f"\n[OK] 工程结构树已生成")
        print(f"  项目根节点: {tree.get('project_id')}")
    else:
        print(f"[FAIL] 查询结构树失败: {response.status_code}")


def main():
    """主流程"""
    print("\n" + "=" * 60)
    print("BDC-AI 演示数据添加脚本")
    print("=" * 60)

    try:
        # 步骤 1: 创建项目
        project_id = create_demo_project()

        # 步骤 2: 创建工程结构
        building_id, zone_id, system_id, device_id = create_engineering_structure(project_id)

        # 步骤 3: 添加资产
        # 先尝试上传图片
        uploaded = upload_demo_assets(project_id, device_id, zone_id, system_id)

        # 如果没有图片，创建文本资产
        if uploaded == 0:
            create_test_assets_without_images(project_id, device_id)

        # 步骤 4: 验证
        verify_data(project_id)

        print(f"\n{'=' * 60}")
        print("[OK] 演示数据添加完成！")
        print(f"{'=' * 60}")
        print(f"\n项目 ID: {project_id}")
        print(f"您现在可以在 PC UI 中查看这个项目！")
        print(f"访问地址: http://localhost:8080")

    except Exception as e:
        print(f"\n[FAIL] 处理失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
