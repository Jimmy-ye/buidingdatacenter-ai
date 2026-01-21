"""
检查新上传资产的详细信息
"""
import requests

BACKEND_URL = "http://localhost:8000"
ASSET_ID = "d236b3d0-0850-4fd7-b6b4-da1a1561fb06"

resp = requests.get(f"{BACKEND_URL}/api/v1/assets/{ASSET_ID}")
resp.raise_for_status()
asset = resp.json()

print(f"Asset ID: {ASSET_ID}")
print(f"Content Role: {asset.get('content_role')}")
print(f"Status: {asset.get('status')}")

payloads = asset.get('structured_payloads', [])
print(f"\nTotal payloads: {len(payloads)}\n")

for i, p in enumerate(payloads, 1):
    schema = p.get('schema_type')
    version = p.get('version')
    created_by = p.get('created_by')
    print(f"{i}. {schema} (v{version}, by {created_by})")
