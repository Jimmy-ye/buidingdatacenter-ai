import json
import uuid

import requests

BASE_URL = "http://127.0.0.1:8000"


def main() -> None:
    print("=" * 60)
    print("[工程结构] 测试 1: 创建 Project")
    print("=" * 60)

    resp = requests.post(
        f"{BASE_URL}/api/v1/projects/",
        json={
            "name": "engineer-structure-test",
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

    print("\n[工程结构] 测试 2: 创建 Building / Zone / System / Device")
    # Building
    b_resp = requests.post(
        f"{BASE_URL}/api/v1/projects/{project_id}/buildings",
        json={
            "name": "A座办公楼",
            "usage_type": "office",
            "floor_area": 10000.0,
            "year_built": 2015,
            "energy_grade": "A",
            "tags": ["总部园区"],
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
            "tags": ["5F"],
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
            "tags": ["空调"],
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
            "tags": ["高能耗", "待观察"],
        },
        timeout=30,
    )
    print("Device status:", d_resp.status_code)
    d_resp.raise_for_status()
    device = d_resp.json()
    device_id = device["id"]

    print("\n[工程结构] 测试 3: Project 级扁平设备查询 /devices/flat")
    flat_resp = requests.get(
        f"{BASE_URL}/api/v1/projects/{project_id}/devices/flat",
        params={
            "device_type": "fcu",
            "min_rated_power": 1.0,
            "tags": "高能耗",
        },
        timeout=30,
    )
    print("Flat status:", flat_resp.status_code)
    flat_resp.raise_for_status()
    print("Flat response:")
    print(json.dumps(flat_resp.json(), indent=2, ensure_ascii=False))

    print("\n[工程结构] 测试 4: 结构树 /structure_tree")
    tree_resp = requests.get(
        f"{BASE_URL}/api/v1/projects/{project_id}/structure_tree",
        timeout=30,
    )
    print("Tree status:", tree_resp.status_code)
    tree_resp.raise_for_status()
    print("Tree response (截取前 800 字符):")
    print(tree_resp.text[:800])


if __name__ == "__main__":
    main()
