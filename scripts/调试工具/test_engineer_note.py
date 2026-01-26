"""
测试带工程师备注的图片的LLM输出

测试场景：
1. 上传相同图片，但带不同的工程师备注
2. 对比LLM输出差异，验证备注是否影响分析结果
"""
import os
import time
import requests
import uuid

BACKEND_URL = "http://localhost:8000"
PROJECT_ID = "c5460273-820b-4c8e-abea-0239e84885fd"

# 使用一张已存在的测试图片
TEST_IMAGE_PATH = r"D:\Huawei Files\华为家庭存储\Programs\program-bdc-ai\data\assets\c5460273-820b-4c8e-abea-0239e84885fd\ce29ad6c-2bdb-41fc-88f1-e11898f264c4.jpg"


def test_upload_with_note(description: str, content_role: str = "scene_issue") -> str:
    """上传图片并附带工程师备注"""
    print(f"\n{'='*60}")
    print(f"测试场景：{content_role} - 备注：{description}")
    print(f"{'='*60}")

    if not os.path.exists(TEST_IMAGE_PATH):
        print(f"[ERROR] 测试图片不存在: {TEST_IMAGE_PATH}")
        return ""

    # 读取图片文件
    with open(TEST_IMAGE_PATH, "rb") as f:
        files = {"file": ("test_meter.jpg", f, "image/jpeg")}

        # 使用正确的API端点和参数格式
        # Query参数：project_id, source, content_role, auto_route
        # Form参数：note, title
        data = {
            "note": description,  # 工程师备注（Form参数）
            "title": f"测试备注：{description}",
        }

        params = {
            "project_id": PROJECT_ID,
            "source": "pc_upload",
            "content_role": content_role,
            "auto_route": "true",
        }

        response = requests.post(
            f"{BACKEND_URL}/api/v1/assets/upload_image_with_note",
            files=files,
            data=data,
            params=params
        )
        if response.status_code not in (200, 201):
            print(f"[ERROR] 上传失败: HTTP {response.status_code} {response.text}")
            return ""

        asset = response.json()
        asset_id = asset.get("id")
        print(f"[OK] 资产已创建: {asset_id}")
        print(f"     标题: {asset.get('title')}")
        print(f"     备注: {asset.get('description')}")
        print(f"     状态: {asset.get('status')}")
        print(f"     Content Role: {asset.get('content_role')}")

        return asset_id


def wait_for_llm_processing(asset_id: str, timeout: int = 120):
    """等待LLM处理完成"""
    print(f"\n[INFO] 等待LLM处理（最多{timeout}秒）...")
    start_time = time.time()

    while time.time() - start_time < timeout:
        response = requests.get(f"{BACKEND_URL}/api/v1/assets/{asset_id}")
        if response.status_code == 200:
            asset = response.json()
            status = asset.get("status")
            print(f"[INFO] 当前状态: {status}", end="\r")

            if status == "parsed_scene_llm":
                print(f"\n[OK] LLM处理完成！")
                return asset
            elif status in ("parsed_ocr_ok", "pending_scene_llm"):
                time.sleep(2)
            else:
                print(f"\n[WARN] 意外状态: {status}")
                return asset
        else:
            print(f"\n[ERROR] 查询资产失败: HTTP {response.status_code}")
            return None

    print(f"\n[WARN] 等待超时")
    return None


def display_llm_result(asset: dict):
    """显示LLM分析结果"""
    print(f"\n{'='*60}")
    print("LLM分析结果")
    print(f"{'='*60}")

    payloads = asset.get("structured_payloads") or []
    for sp in payloads:
        if sp.get("schema_type") == "scene_issue_report_v1":
            payload = sp.get("payload", {})

            print(f"\n【标题】")
            print(f"  {payload.get('title') or '(无)'}")

            print(f"\n【问题类别】")
            print(f"  {payload.get('issue_category') or '(无)'}")

            print(f"\n【严重程度】")
            severity = payload.get('severity', 'unknown')
            severity_map = {"low": "[LOW]", "medium": "[MEDIUM]", "high": "[HIGH]"}
            print(f"  {severity_map.get(severity, '')} {severity}")

            print(f"\n【状态描述】")
            print(f"  {payload.get('summary', '')}")

            print(f"\n【可能原因】")
            for i, cause in enumerate(payload.get('suspected_causes', []), 1):
                print(f"  {i}. {cause}")

            print(f"\n【建议措施】")
            for i, action in enumerate(payload.get('recommended_actions', []), 1):
                print(f"  {i}. {action}")

            print(f"\n【置信度】")
            print(f"  {payload.get('confidence', 0):.1%}")

            print(f"\n【标签】")
            tags = payload.get('tags', [])
            if tags:
                print(f"  {', '.join(tags)}")
            else:
                print(f"  (无)")

            print(f"\n【生成时间】")
            print(f"  {sp.get('created_at', '')}")


def run_test_cases():
    """运行多个测试用例"""
    print("\n" + "="*60)
    print("测试带工程师备注的图片LLM输出")
    print("="*60)

    test_cases = [
        {
            "name": "场景问题 - 无备注",
            "content_role": "scene_issue",
            "note": "",
        },
        {
            "name": "场景问题 - 提示可能漏水",
            "content_role": "scene_issue",
            "note": "怀疑冷却塔底部有漏水痕迹，请重点检查",
        },
        {
            "name": "场景问题 - 提示设备老化",
            "content_role": "scene_issue",
            "note": "该冷却塔已运行8年，盘管可能存在老化腐蚀",
        },
        {
            "name": "仪表读数 - 无备注",
            "content_role": "meter",
            "note": "",
        },
        {
            "name": "仪表读数 - 提示读数范围",
            "content_role": "meter",
            "note": "这是温度表，读数应该在60-70℃之间",
        },
    ]

    results = []

    for i, case in enumerate(test_cases, 1):
        print(f"\n\n{'#'*60}")
        print(f"# 测试用例 {i}/{len(test_cases)}: {case['name']}")
        print(f"{'#'*60}")

        asset_id = test_upload_with_note(case["note"], case["content_role"])
        if not asset_id:
            print(f"[SKIP] 跳过此测试用例")
            continue

        asset = wait_for_llm_processing(asset_id)
        if asset:
            display_llm_result(asset)
            results.append({
                "case": case["name"],
                "asset_id": asset_id,
                "note": case["note"],
                "severity": extract_severity(asset),
                "summary": extract_summary(asset),
            })
        else:
            print(f"[FAIL] LLM处理失败或超时")

        # 等待一下再处理下一个
        time.sleep(2)

    # 打印对比总结
    print(f"\n\n{'='*60}")
    print("测试结果对比")
    print(f"{'='*60}")

    for r in results:
        print(f"\n【{r['case']}】")
        print(f"  备注: {r['note'] or '(无)'}")
        print(f"  严重度: {r['severity']}")
        print(f"  描述: {r['summary'][:80]}...")

    print(f"\n\n[INFO] 测试完成！共处理 {len(results)} 个用例")


def extract_severity(asset: dict) -> str:
    """从资产中提取严重度"""
    payloads = asset.get("structured_payloads") or []
    for sp in payloads:
        if sp.get("schema_type") == "scene_issue_report_v1":
            return sp.get("payload", {}).get("severity", "unknown")
    return "unknown"


def extract_summary(asset: dict) -> str:
    """从资产中提取描述"""
    payloads = asset.get("structured_payloads") or []
    for sp in payloads:
        if sp.get("schema_type") == "scene_issue_report_v1":
            return sp.get("payload", {}).get("summary", "")
    return ""


if __name__ == "__main__":
    run_test_cases()
