import json

import requests

BASE_URL = "http://127.0.0.1:8000"


def main() -> None:
    print("=" * 60)
    print("[Asset-Engineering] 测试 1: 创建 Project")
    print("=" * 60)

    resp = requests.post(
        f"{BASE_URL}/api/v1/projects/",
        json={
            "name": "asset-engineering-test",
            "client": "测试客户",
            "location": "测试地点",
            "status": "active",
        },
        timeout=30,
    )
    print("Project status:", resp.status_code)
    print("Project resp:", resp.text)
    resp.raise_for_status()
    project = resp.json()
    project_id = project["id"]

    print("\n[Asset-Engineering] 测试 2: 创建 Building / Zone / System / Device")
    # Building
    b_resp = requests.post(
        f"{BASE_URL}/api/v1/projects/{project_id}/buildings",
        json={
            "name": "A座办公楼",
            "usage_type": "office",
            "floor_area": 8000.0,
            "year_built": 2018,
            "energy_grade": "A",
        },
        timeout=30,
    )
    print("Building status:", b_resp.status_code)
    b_resp.raise_for_status()
    building = b_resp.json()
    building_id = building["id"]

    # Zone
    z_resp = requests.post(
        f"{BASE_URL}/api/v1/buildings/{building_id}/zones",
        json={
            "name": "5F办公区",
            "type": "office",
            "geometry_ref": "L5-Office",
        },
        timeout=30,
    )
    print("Zone status:", z_resp.status_code)
    z_resp.raise_for_status()
    zone = z_resp.json()
    zone_id = zone["id"]

    # System
    s_resp = requests.post(
        f"{BASE_URL}/api/v1/buildings/{building_id}/systems",
        json={
            "type": "HVAC",
            "name": "HVAC系统",
            "description": "空调系统",
        },
        timeout=30,
    )
    print("System status:", s_resp.status_code)
    s_resp.raise_for_status()
    system = s_resp.json()
    system_id = system["id"]

    # Device
    d_resp = requests.post(
        f"{BASE_URL}/api/v1/systems/{system_id}/devices",
        json={
            "zone_id": zone_id,
            "device_type": "fcu",
            "model": "风机盘管FCU-03",
            "rated_power": 1.5,
            "serial_no": "FCU-03",
        },
        timeout=30,
    )
    print("Device status:", d_resp.status_code)
    d_resp.raise_for_status()
    device = d_resp.json()
    device_id = device["id"]

    print("\n[Asset-Engineering] 测试 3: 上传绑定到工程结构的图片 Asset")
    # 这里复用 upload_image_with_note 接口，简化为本地构造一个小的二进制流
    files = {
        "file": ("test.jpg", b"fake-image-bytes", "image/jpeg"),
    }
    data = {
        "note": "5F风机盘管测试图片",
        "title": "FCU-03 测试图",
    }
    params = {
        "project_id": project_id,
        "source": "test_script",
        "content_role": "scene_issue",
        "building_id": building_id,
        "zone_id": zone_id,
        "system_id": system_id,
        "device_id": device_id,
    }

    a_resp = requests.post(
        f"{BASE_URL}/api/v1/assets/upload_image_with_note",
        params=params,
        data=data,
        files=files,
        timeout=60,
    )
    print("Upload asset status:", a_resp.status_code)
    print("Upload asset resp:", a_resp.text)
    a_resp.raise_for_status()
    asset = a_resp.json()
    asset_id = asset["id"]

    print("\n[Asset-Engineering] 测试 4: /api/v1/assets 多维过滤")
    list_resp = requests.get(
        f"{BASE_URL}/api/v1/assets",
        params={
            "project_id": project_id,
            "building_id": building_id,
            "zone_id": zone_id,
            "system_id": system_id,
            "device_id": device_id,
            "modality": "image",
        },
        timeout=30,
    )
    print("List assets status:", list_resp.status_code)
    list_resp.raise_for_status()
    print("List assets resp:")
    print(json.dumps(list_resp.json(), indent=2, ensure_ascii=False))

    print("\n[Asset-Engineering] 测试 5: 工程节点 → 资产反向查询")

    # Device → Assets
    dev_assets = requests.get(
        f"{BASE_URL}/api/v1/devices/{device_id}/assets",
        timeout=30,
    )
    print("Device->assets status:", dev_assets.status_code)
    dev_assets.raise_for_status()
    print("Device->assets resp:")
    print(json.dumps(dev_assets.json(), indent=2, ensure_ascii=False))

    # Zone → Assets
    zone_assets = requests.get(
        f"{BASE_URL}/api/v1/zones/{zone_id}/assets",
        timeout=30,
    )
    print("Zone->assets status:", zone_assets.status_code)
    zone_assets.raise_for_status()
    print("Zone->assets resp:")
    print(json.dumps(zone_assets.json(), indent=2, ensure_ascii=False))

    # Building → Assets
    bld_assets = requests.get(
        f"{BASE_URL}/api/v1/buildings/{building_id}/assets",
        timeout=30,
    )
    print("Building->assets status:", bld_assets.status_code)
    bld_assets.raise_for_status()
    print("Building->assets resp:")
    print(json.dumps(bld_assets.json(), indent=2, ensure_ascii=False))

    # System → Assets
    sys_assets = requests.get(
        f"{BASE_URL}/api/v1/systems/{system_id}/assets",
        timeout=30,
    )
    print("System->assets status:", sys_assets.status_code)
    sys_assets.raise_for_status()
    print("System->assets resp:")
    print(json.dumps(sys_assets.json(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
