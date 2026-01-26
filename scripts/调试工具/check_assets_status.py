"""
检查测试项目中资产的当前状态
"""
import requests

BACKEND_URL = "http://localhost:8000"
PROJECT_ID = "c5460273-820b-4c8e-abea-0239e84885fd"

def check_assets():
    response = requests.get(f"{BACKEND_URL}/api/v1/assets/", params={"project_id": PROJECT_ID})
    response.raise_for_status()
    assets = response.json()

    image_assets = [a for a in assets if a.get("modality") == "image"]

    print(f"项目 {PROJECT_ID} 的图片资产状态：\n")

    for asset in image_assets:
        asset_id = asset.get("id")
        title = asset.get("title", "unknown")
        content_role = asset.get("content_role", "unknown")
        status = asset.get("status", "unknown")

        # 获取详细信息包括 structured_payloads
        detail_resp = requests.get(f"{BACKEND_URL}/api/v1/assets/{asset_id}")
        detail_resp.raise_for_status()
        detail = detail_resp.json()

        # 检查 structured_payloads
        payloads = detail.get("structured_payloads", [])
        payload_types = [p.get("schema_type") for p in payloads]

        print(f"标题: {title}")
        print(f"  角色: {content_role}")
        print(f"  状态: {status}")
        print(f"  Payloads: {', '.join(payload_types) if payload_types else '(无)'}")
        print()

if __name__ == "__main__":
    check_assets()
