import requests
import json

# 测试创建 Project
print("=" * 50)
print("测试 1: 创建 Project")
print("=" * 50)

response = requests.post(
    "http://localhost:8000/api/v1/projects/",
    json={
        "name": "测试项目",
        "client": "测试客户",
        "location": "测试地点",
        "status": "active"
    }
)

print(f"Status Code: {response.status_code}")
print(f"Response Text: {response.text}")

if response.status_code in (200, 201):
    project = response.json()
    project_id = project.get("id")

    print("\n" + "=" * 50)
    print("测试 2: 查询项目列表")
    print("=" * 50)

    response = requests.get("http://localhost:8000/api/v1/projects/")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    print(f"\n项目 ID: {project_id}")

else:
    print("\n创建 Project 失败")
    exit(1)
