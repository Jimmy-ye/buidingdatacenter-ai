"""
重新上传仪表图片，使用 auto_route=true
"""
import requests
import os

BACKEND_URL = "http://localhost:8000"
PROJECT_ID = "c5460273-820b-4c8e-abea-0239e84885fd"
DEVICE_ID = "3dddfe4b-bf57-4306-b0b1-5608c661fcd8"

# 选择一张仪表图片重新上传
IMAGE_PATH = r"D:\Huawei Files\华为家庭存储\Programs\program-bdc-ai\data\assets\c5460273-820b-4c8e-abea-0239e84885fd\ce29ad6c-2bdb-41fc-88f1-e11898f264c4.jpg"

def upload_meter_image():
    if not os.path.exists(IMAGE_PATH):
        print(f"[ERROR] 图片不存在: {IMAGE_PATH}")
        return

    print(f"[INFO] 重新上传仪表图片: {IMAGE_PATH}")
    print(f"[INFO] 项目ID: {PROJECT_ID}")
    print(f"[INFO] 设备ID: {DEVICE_ID}")
    print(f"[INFO] content_role=meter, auto_route=true\n")

    url = f"{BACKEND_URL}/api/v1/assets/upload_image_with_note"

    with open(IMAGE_PATH, "rb") as f:
        files = {"file": ("IMG_20250710_144534.jpg", f, "image/jpeg")}
        # 使用 data 参数传递 auto_route 布尔值
        params = {
            "project_id": PROJECT_ID,
            "source": "pc_upload",
            "content_role": "meter",
            "device_id": DEVICE_ID,
            "auto_route": True,  # 使用布尔值而不是字符串
            "title": "仪表读数测试（重新上传）"
        }

        response = requests.post(url, files=files, params=params)
        response.raise_for_status()

        result = response.json()

        print(f"[SUCCESS] 上传成功！")
        print(f"  - Asset ID: {result.get('id')}")
        print(f"  - 状态: {result.get('status')}")
        print(f"  - Title: {result.get('title')}")
        print(f"  - Content Role: {result.get('content_role')}")

        # 检查是否有 structured_payloads
        if 'structured_payloads' in result:
            payloads = result.get('structured_payloads', [])
            print(f"  - Payloads: {[p.get('schema_type') for p in payloads]}")
        else:
            print(f"  - Payloads: (API未返回)")

        print(f"\n[INFO] 现在等待 Worker 处理...")
        print(f"[INFO] 状态应该从 '{result.get('status')}' 变为 'pending_scene_llm'")
        print(f"[INFO] 然后 Worker 会处理并变为 'parsed_scene_llm'")

if __name__ == "__main__":
    upload_meter_image()
