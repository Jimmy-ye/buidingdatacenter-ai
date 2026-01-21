"""
重新运行测试项目的所有图片 OCR/LLM 处理
"""
import requests
import time

# 配置
BACKEND_URL = "http://localhost:8000"
PROJECT_ID = "c5460273-820b-4c8e-abea-0239e84885fd"  # 测试项目 ID

def rerun_all_images():
    """重新运行项目中所有图片的处理"""

    # 1. 获取项目下的所有资产
    print(f"[INFO] 获取项目 {PROJECT_ID} 的所有资产...")
    response = requests.get(f"{BACKEND_URL}/api/v1/assets/", params={"project_id": PROJECT_ID})
    response.raise_for_status()
    assets = response.json()

    # 2. 筛选出图片类型的资产
    image_assets = [a for a in assets if a.get("modality") == "image"]
    print(f"[INFO] 找到 {len(image_assets)} 个图片资产")

    if not image_assets:
        print("[ERROR] 没有找到图片资产")
        return

    # 3. 对每个图片重新运行处理
    success_count = 0
    failed_count = 0

    for i, asset in enumerate(image_assets, 1):
        asset_id = asset.get("id")
        title = asset.get("title", asset.get("id", "unknown"))
        content_role = asset.get("content_role", "unknown")

        print(f"\n[{i}/{len(image_assets)}] 处理: {title}")
        print(f"  - ID: {asset_id}")
        print(f"  - 角色: {content_role}")

        try:
            # 调用路由 API，会自动根据 content_role 选择处理流程
            response = requests.post(
                f"{BACKEND_URL}/api/v1/assets/{asset_id}/route_image",
                timeout=60  # 给足够的时间处理
            )
            response.raise_for_status()

            result = response.json()
            new_status = result.get("status", "unknown")
            print(f"  [OK] 成功 - 状态: {new_status}")
            success_count += 1

            # 避免请求过快
            time.sleep(0.5)

        except requests.exceptions.Timeout:
            print(f"  [WARN] 超时")
            failed_count += 1
        except requests.exceptions.HTTPError as e:
            print(f"  [ERROR] HTTP 错误: {e.response.status_code} - {e.response.text}")
            failed_count += 1
        except Exception as e:
            print(f"  [ERROR] 错误: {e}")
            failed_count += 1

    # 4. 打印总结
    print(f"\n{'='*60}")
    print(f"[SUMMARY] 处理完成！")
    print(f"  - 总计: {len(image_assets)} 个图片")
    print(f"  - 成功: {success_count} 个")
    print(f"  - 失败: {failed_count} 个")
    print(f"{'='*60}")

if __name__ == "__main__":
    rerun_all_images()
