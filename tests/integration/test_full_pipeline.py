import requests
import json
import traceback

BASE_URL = "http://localhost:8000/api/v1"

print("=" * 60)
print("步骤 1: 创建 Project")
print("=" * 60)

try:
    response = requests.post(
        f"{BASE_URL}/projects/",
        json={
            "name": "PaddleOCR 测试项目",
            "client": "测试客户",
            "location": "测试地点",
            "status": "active"
        }
    )

    print(f"Status: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    print(f"Response: {response.text}")

    if response.status_code not in (200, 201):
        print("\n❌ Failed to create project")
        exit(1)

    project = response.json()
    project_id = project["id"]
    print(f"\n✓ Project created: {project['name']}")
    print(f"  ID: {project_id}")

except Exception as e:
    print(f"\n❌ Exception: {e}")
    traceback.print_exc()
    exit(1)
