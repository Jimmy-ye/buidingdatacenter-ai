"""
直接查询数据库中的 payload
"""
import requests

BACKEND_URL = "http://localhost:8000"
ASSET_ID = "f17ad40c-4594-4ea6-8a9d-3ad4267ddcc3"

resp = requests.get(f"{BACKEND_URL}/api/v1/assets/{ASSET_ID}")
resp.raise_for_status()
asset = resp.json()

payloads = asset.get('structured_payloads', [])

print(f"Asset ID: {ASSET_ID}")
print(f"Status: {asset.get('status')}")
print(f"Total payloads: {len(payloads)}\n")

for i, p in enumerate(payloads, 1):
    schema = p.get('schema_type')
    version = p.get('version')
    created_by = p.get('created_by')
    print(f"{i}. {schema} (v{version}, by {created_by})")
    if schema == 'image_route_decision_v1':
        print(f"   Payload: {p.get('payload')}")

print(f"\n是否有 image_route_decision_v1: {'是' if any(p.get('schema_type') == 'image_route_decision_v1' for p in payloads) else '否'}")
