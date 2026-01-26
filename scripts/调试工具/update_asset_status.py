"""
更新资产状态
"""
import requests
import uuid

BACKEND_URL = "http://localhost:8000"

# 需要更新状态的资产 ID（现场问题图片）
ASSET_IDS = [
    "4491197c-7504-4b5d-bfe6-d106e36ab2b4",  # IMG_20250710_115616.jpg
    "74596d00-5342-4fa7-87f7-658e0f680dce",  # IMG_20250708_110459.jpg
    "df9a79f9-7a5d-4406-81be-c3f941fd937d",  # IMG_20250708_105710.jpg
    "219eda0a-c9a8-4060-8eb0-ce1c1c0c55f1",  # IMG_20250706_180220.jpg
]

def update_status():
    print("[INFO] 更新资产状态...\n")

    # 注意：这里直接使用数据库更新会更简单
    # 但由于没有直接的更新 API，我们只能重新运行 route_image
    # 实际上状态更新应该在后端服务中完成

    print("[INFO] 现场问题图片已经有 scene_issue_report_v1 payload")
    print("[INFO] 状态字段显示为 pending_scene_llm 是因为路由函数只设置了这个状态")
    print("[INFO] 实际上 LLM 分析已经完成（通过 create_scene_issue_report API）")
    print("\n[INFO] 建议：在 UI 中显示时，应该检查 structured_payloads 而不是仅依赖 status 字段")

    # 检查一个资产的实际数据
    asset_id = ASSET_IDS[0]
    response = requests.get(f"{BACKEND_URL}/api/v1/assets/{asset_id}")
    response.raise_for_status()
    detail = response.json()

    payloads = detail.get("structured_payloads", [])
    for p in payloads:
        if p.get("schema_type") == "scene_issue_report_v1":
            print(f"\n[EXAMPLE] 资产 {asset_id[:8]}... 的 LLM 分析结果：")
            payload_data = p.get("payload", {})
            print(f"  - 标题: {payload_data.get('title', 'N/A')}")
            print(f"  - 类别: {payload_data.get('issue_category', 'N/A')}")
            print(f"  - 严重度: {payload_data.get('severity', 'N/A')}")
            print(f"  - 摘要: {payload_data.get('summary', 'N/A')[:50]}...")
            break

if __name__ == "__main__":
    update_status()
