"""
测试单个仪表图片的路由
"""
import requests

BACKEND_URL = "http://localhost:8000"
ASSET_ID = "f17ad40c-4594-4ea6-8a9d-3ad4267ddcc3"  # IMG_20250710_144534.jpg

def test_meter_routing():
    print(f"[INFO] 测试仪表图片路由: {ASSET_ID}")

    # 获取当前状态
    print("\n--- 处理前 ---")
    resp = requests.get(f"{BACKEND_URL}/api/v1/assets/{ASSET_ID}")
    resp.raise_for_status()
    asset = resp.json()
    print(f"当前状态: {asset.get('status')}")
    print(f"Payloads: {[p.get('schema_type') for p in asset.get('structured_payloads', [])]}")

    # 调用路由
    print(f"\n--- 调用路由 API ---")
    resp = requests.post(f"{BACKEND_URL}/api/v1/assets/{ASSET_ID}/route_image")
    resp.raise_for_status()
    result = resp.json()
    print(f"返回状态: {result.get('status')}")
    print(f"返回 Payloads: {[p.get('schema_type') for p in result.get('structured_payloads', [])]}")

    # 再次获取状态
    print("\n--- 处理后 ---")
    resp = requests.get(f"{BACKEND_URL}/api/v1/assets/{ASSET_ID}")
    resp.raise_for_status()
    asset = resp.json()
    print(f"最终状态: {asset.get('status')}")
    print(f"最终 Payloads: {[p.get('schema_type') for p in asset.get('structured_payloads', [])]}")

    # 检查是否有 image_route_decision_v1
    payloads = asset.get('structured_payloads', [])
    route_decisions = [p for p in payloads if p.get('schema_type') == 'image_route_decision_v1']
    if route_decisions:
        print(f"\n✅ 找到路由决策 payload: {route_decisions[-1].get('payload')}")
    else:
        print(f"\n❌ 未找到路由决策 payload")

if __name__ == "__main__":
    test_meter_routing()
