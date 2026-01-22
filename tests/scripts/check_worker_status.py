"""
手动触发Worker处理单个带备注的资产
用于调试为什么带备注的资产没有被处理
"""
import time
import requests

BACKEND_URL = "http://localhost:8000"
# 测试用例2：带漏水备注的资产
ASSET_ID = "3ba153fc-650f-4927-ba75-623aa3146d8e"

print(f"正在测试资产: {ASSET_ID}")
print(f"预期：这个资产有工程师备注，应该由Worker处理")
print(f"备注内容：怀疑冷却塔底部有漏水痕迹，请重点检查")
print()

# 查询当前状态
response = requests.get(f"{BACKEND_URL}/api/v1/assets/{ASSET_ID}")
asset = response.json()
print(f"当前状态: {asset['status']}")
print(f"Content Role: {asset['content_role']}")
print(f"Description: {asset.get('description', 'None')}")
print(f"Payloads数量: {len(asset.get('structured_payloads', []))}")
print()

# 检查Worker进程
import subprocess
try:
    result = subprocess.run(
        ["wmic", "process", "where", "name='python.exe'", "get", "processid,commandline"],
        capture_output=True,
        text=True,
        timeout=10
    )
    worker_lines = [line for line in result.stdout.split('\n') if 'scene_issue_glm_worker' in line]
    if worker_lines:
        print(f"✓ Worker进程正在运行:")
        for line in worker_lines:
            print(f"  {line.strip()}")
    else:
        print(f"✗ Worker进程未运行！")
except Exception as e:
    print(f"✗ 检查Worker进程失败: {e}")

print()
print("="*60)
print("请检查Worker的控制台输出，看是否有这个资产的处理日志")
print("如果Worker没有处理这个资产，可能的原因：")
print("1. Worker的轮询间隔太长（默认60秒）")
print("2. GLM API调用出错")
print("3. Worker代码有bug")
print("="*60)
