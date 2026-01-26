#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Worker 快速测试脚本
"""
import os
import sys
import requests
from dotenv import load_dotenv

# 加载环境变量
load_dotenv('services/worker/.env')

def test_backend_connection():
    """测试后端连接"""
    print("\n[1/4] Testing backend connection...")
    backend_url = os.getenv('BDC_BACKEND_BASE_URL', 'http://localhost:8000')

    try:
        response = requests.get(f'{backend_url}/api/v1/health', timeout=5)
        if response.status_code == 200:
            print(f"  [OK] Backend service is running")
            print(f"  Status: {response.status_code}")
            return True
        else:
            print(f"  [FAIL] Backend responded with: {response.status_code}")
            return False
    except Exception as e:
        print(f"  [FAIL] Cannot connect to backend: {e}")
        return False

def test_worker_config():
    """测试 Worker 配置"""
    print("\n[2/4] Checking Worker configuration...")

    required_vars = [
        'BDC_BACKEND_BASE_URL',
        'GLM_API_KEY',
        'BDC_LOCAL_STORAGE_DIR',
    ]

    all_ok = True
    for var in required_vars:
        value = os.getenv(var)
        if value:
            if 'API_KEY' in var:
                print(f"  [OK] {var}: {value[:15]}...")
            else:
                print(f"  [OK] {var}: {value}")
        else:
            print(f"  [FAIL] {var}: not set")
            all_ok = False

    return all_ok

def test_pending_assets():
    """检查待处理资产"""
    print("\n[3/4] 检查待处理资产...")

    backend_url = os.getenv('BDC_BACKEND_BASE_URL', 'http://localhost:8000')

    try:
        # 尝试获取资产列表
        response = requests.get(f'{backend_url}/api/v1/assets/', timeout=5)
        if response.status_code == 200:
            assets = response.json()
            if isinstance(assets, list) or isinstance(assets.get('items'), list):
                items = assets if isinstance(assets, list) else assets.get('items', [])
                pending_count = sum(1 for a in items if a.get('processing_status') == 'pending_scene_llm')
                print(f"  [OK] 总资产数: {len(items)}")
                print(f"  [OK] 待处理数: {pending_count}")
                if pending_count > 0:
                    print(f"  ! Worker 将开始处理这 {pending_count} 个资产")
                else:
                    print(f"  i 当前没有待处理的资产")
                return True
        print(f"  ? 无法获取资产列表")
        return False
    except Exception as e:
        print(f"  [FAIL] 检查失败: {e}")
        return False

def test_glm_api():
    """测试 GLM API 连接"""
    print("\n[4/4] 测试 GLM API...")

    api_key = os.getenv('GLM_API_KEY')
    if not api_key:
        print("  [FAIL] GLM_API_KEY 未设置")
        return False

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url='https://open.bigmodel.cn/api/paas/v4/')

        # 简单测试调用
        response = client.chat.completions.create(
            model='glm-4-flash',
            messages=[{'role': 'user', 'content': '你好'}],
            max_tokens=10
        )

        if response.choices:
            print(f"  [OK] GLM API 连接成功")
            print(f"  模型响应: {response.choices[0].message.content.strip()}")
            return True
        else:
            print(f"  [FAIL] GLM API 响应为空")
            return False
    except Exception as e:
        print(f"  [FAIL] GLM API 测试失败: {e}")
        return False

def main():
    print("="*60)
    print("  Worker 服务测试")
    print("="*60)

    results = []
    results.append(('后端连接', test_backend_connection()))
    results.append(('配置检查', test_worker_config()))
    results.append(('资产检查', test_pending_assets()))
    results.append(('GLM API', test_glm_api()))

    print("\n" + "="*60)
    print("  测试结果汇总")
    print("="*60)

    for name, result in results:
        status = "[OK] 通过" if result else "[FAIL] 失败"
        print(f"  {name}: {status}")

    all_passed = all(result for _, result in results)

    print("\n" + "="*60)
    if all_passed:
        print("  所有测试通过!Worker 可以正常工作。")
        print("  运行 '启动Worker.bat' 启动 Worker 服务。")
    else:
        print("  部分测试失败，请检查配置。")
    print("="*60)

    return 0 if all_passed else 1

if __name__ == '__main__':
    sys.exit(main())
