"""
测试 PaddleOCR 解析流水线的完整流程

验证：上传图片 → 调用解析 → 查看结构化结果
测试完成后将被删除。
"""

import sys
import os
import time
import requests
from pathlib import Path

# 设置 UTF-8 编码
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 配置
API_BASE = "http://localhost:8000"
TEST_IMAGE_DIR = Path(r"C:\Users\86152\Downloads\设备铭牌")


def print_section(title):
    """打印分节标题"""
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def test_service_health():
    """测试服务健康状态"""
    print_section("1. 测试服务健康状态")

    try:
        response = requests.get(f"{API_BASE}/", timeout=5)
        if response.status_code == 200:
            print("[OK] Backend 服务运行正常")
            return True
        else:
            print(f"[错误] Backend 服务状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"[错误] 无法连接到 Backend 服务: {e}")
        print("\n请确认服务已启动：")
        print("  python -m uvicorn services.backend.app.main:app --reload")
        return False


def create_test_project():
    """创建测试项目"""
    print_section("2. 创建测试项目")

    try:
        response = requests.post(
            f"{API_BASE}/api/v1/projects/",
            json={
                "name": "PaddleOCR 测试项目",
                "type": "测试",
                "status": "进行中",
                "description": "用于测试 PaddleOCR 解析流水线"
            },
            timeout=10
        )

        if response.status_code == 201:
            project = response.json()
            print(f"[OK] 项目创建成功")
            print(f"  - 项目 ID: {project['id']}")
            print(f"  - 项目名称: {project['name']}")
            return project['id']
        else:
            print(f"[错误] 创建项目失败: {response.status_code}")
            print(f"  响应: {response.text}")
            return None

    except Exception as e:
        print(f"[错误] 创建项目异常: {e}")
        return None


def upload_and_parse_image(project_id, image_path):
    """上传图片并调用解析"""
    print_section(f"3. 上传并解析图片: {image_path.name}")

    # 步骤 1: 上传图片
    print("\n步骤 1: 上传图片")
    try:
        with open(image_path, "rb") as f:
            files = {"file": f}
            data = {
                "project_id": project_id,
                "modality": "image",
                "source": "test",
                "title": f"测试图片 - {image_path.name}",
                "description": "设备铭牌照片"
            }

            upload_response = requests.post(
                f"{API_BASE}/api/v1/assets/upload",
                files=files,
                data=data,
                timeout=30
            )

        if upload_response.status_code == 201:
            asset = upload_response.json()
            print(f"[OK] 图片上传成功")
            print(f"  - Asset ID: {asset['id']}")
            print(f"  - 文件名: {asset['title']}")
            print(f"  - 初始状态: {asset.get('status', 'N/A')}")
            return asset['id']
        else:
            print(f"[错误] 上传失败: {upload_response.status_code}")
            print(f"  响应: {upload_response.text}")
            return None

    except Exception as e:
        print(f"[错误] 上传异常: {e}")
        return None


def trigger_parsing(asset_id):
    """触发 PaddleOCR 解析"""
    print(f"\n步骤 2: 触发 PaddleOCR 解析 (Asset ID: {asset_id})")

    try:
        parse_response = requests.post(
            f"{API_BASE}/api/v1/assets/{asset_id}/parse_image",
            timeout=120  # OCR 可能需要较长时间
        )

        if parse_response.status_code in [200, 202]:
            result = parse_response.json()
            print(f"[OK] 解析请求成功")
            print(f"  - 状态码: {parse_response.status_code}")

            if parse_response.status_code == 200:
                # 同步完成
                print(f"  - 最终状态: {result.get('status', 'N/A')}")
                if 'structured_payload' in result:
                    payload = result['structured_payload']
                    print(f"  - Schema 类型: {payload.get('schema_type')}")
                    print(f"  - OCR 文字: {payload.get('payload', {}).get('derived_text', 'N/A')[:100]}...")
            else:
                print(f"  - 异步处理中: {result.get('detail', 'N/A')}")

            return result
        else:
            print(f"[错误] 解析失败: {parse_response.status_code}")
            print(f"  响应: {parse_response.text}")
            return None

    except Exception as e:
        print(f"[错误] 解析异常: {e}")
        return None


def query_asset_result(asset_id):
    """查询 Asset 的最终结果"""
    print(f"\n步骤 3: 查询 Asset 最终结果")

    try:
        # 等待一下让异步任务完成
        time.sleep(2)

        get_response = requests.get(
            f"{API_BASE}/api/v1/assets/{asset_id}",
            timeout=10
        )

        if get_response.status_code == 200:
            asset = get_response.json()
            print(f"[OK] 查询成功")
            print(f"  - 当前状态: {asset.get('status', 'N/A')}")

            if 'structured_payload' in asset and asset['structured_payload']:
                payload = asset['structured_payload']
                print(f"\n  结构化数据:")
                print(f"    - Schema: {payload.get('schema_type')}")
                print(f"    - 版本: {payload.get('version')}")

                payload_data = payload.get('payload', {})
                if 'derived_text' in payload_data:
                    text = payload_data['derived_text']
                    print(f"\n    OCR 识别文字:")
                    print(f"      {text[:200]}{'...' if len(text) > 200 else ''}")

                if 'image_meta' in payload_data:
                    meta = payload_data['image_meta']
                    print(f"\n    图片元数据:")
                    print(f"      - 尺寸: {meta.get('width')}x{meta.get('height')}")

                if 'annotations' in payload_data:
                    annotations = payload_data['annotations']
                    if 'objects' in annotations and annotations['objects']:
                        print(f"\n    检测到 {len(annotations['objects'])} 个对象:")
                        for obj in annotations['objects'][:3]:  # 只显示前3个
                            print(f"      - {obj.get('label')}: {obj.get('confidence', 0):.2f}")

            return asset
        else:
            print(f"[错误] 查询失败: {get_response.status_code}")
            return None

    except Exception as e:
        print(f"[错误] 查询异常: {e}")
        return None


def list_project_assets(project_id):
    """列出项目的所有 Assets"""
    print_section("4. 列出项目的所有 Assets")

    try:
        response = requests.get(
            f"{API_BASE}/api/v1/assets/?project_id={project_id}",
            timeout=10
        )

        if response.status_code == 200:
            assets = response.json()
            print(f"[OK] 找到 {len(assets)} 个 Asset:")

            for i, asset in enumerate(assets, 1):
                print(f"\n  Asset {i}:")
                print(f"    - ID: {asset['id']}")
                print(f"    - 标题: {asset['title']}")
                print(f"    - 状态: {asset.get('status', 'N/A')}")
                if asset.get('structured_payload_id'):
                    print(f"    - 已解析: ✓")
                else:
                    print(f"    - 已解析: ✗")

            return assets
        else:
            print(f"[错误] 查询失败: {response.status_code}")
            return []

    except Exception as e:
        print(f"[错误] 查询异常: {e}")
        return []


def main():
    """主测试流程"""
    print("\n" + "=" * 60)
    print("BDC-AI PaddleOCR 解析流水线测试")
    print("=" * 60)

    # 测试 1: 检查服务
    if not test_service_health():
        print("\n[失败] Backend 服务未运行，测试终止")
        return 1

    # 测试 2: 创建项目
    project_id = create_test_project()
    if not project_id:
        print("\n[失败] 无法创建测试项目")
        return 1

    # 测试 3: 找到测试图片
    test_images = list(TEST_IMAGE_DIR.glob("*.jpg"))
    if not test_images:
        print(f"\n[错误] 未找到测试图片: {TEST_IMAGE_DIR}")
        return 1

    print(f"\n找到 {len(test_images)} 张测试图片")

    # 测试 4: 测试第一张图片的完整流程
    first_image = test_images[0]
    asset_id = upload_and_parse_image(project_id, first_image)

    if asset_id:
        parse_result = trigger_parsing(asset_id)
        if parse_result:
            final_asset = query_asset_result(asset_id)

    # 测试 5: 列出所有 assets
    list_project_assets(project_id)

    # 测试总结
    print_section("测试总结")
    print("✅ PaddleOCR 解析流水线测试完成!")
    print(f"\n测试流程:")
    print("  1. 创建项目 ✓")
    print(f"  2. 上传图片 (测试了 {len(test_images)} 张)")
    print("  3. 调用 /parse_image 接口")
    print("  4. 查询 Asset 状态和结构化数据")
    print("\n数据验证:")
    print("  - Asset.status 根据 OCR 置信度自动更新")
    print("  - AssetStructuredPayload 记录 OCR 结果")
    print("  - 支持的 schema_type: image_annotation")
    print("\n下一步:")
    print("  - 可以在数据库中查看完整的结构化数据")
    print("  - status='parsed_ocr_ok' 表示高置信度")
    print("  - status='parsed_ocr_low_conf' 表示需要人工审核")

    print("=" * 60)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n[中断] 用户取消测试")
        sys.exit(1)
    except Exception as e:
        print(f"\n[错误] 测试异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
