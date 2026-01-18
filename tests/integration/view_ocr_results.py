"""
查看 OCR 识别结果的工具脚本
"""
import sqlite3
import json
import sys
from datetime import datetime
from pathlib import Path

# 设置 UTF-8 编码输出（Windows 兼容）
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def view_latest_ocr_result():
    """查看最新的 OCR 识别结果"""
    db_path = Path("data/bdc_ai.db")

    if not db_path.exists():
        print(f"❌ 数据库文件不存在: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 查询最新的 OCR 解析结果
    query = """
    SELECT
        a.id as asset_id,
        a.title,
        a.status,
        a.capture_time as asset_created,
        sp.schema_type as payload_schema,
        sp.version as payload_version,
        sp.payload,
        sp.created_at as parsed_at
    FROM assets a
    LEFT JOIN asset_structured_payloads sp ON a.id = sp.asset_id
    WHERE a.modality = 'image'
    ORDER BY sp.created_at DESC
    LIMIT 5
    """

    cursor.execute(query)
    results = cursor.fetchall()

    if not results:
        print("❌ 没有找到 OCR 识别结果")
        return

    print("\n" + "=" * 80)
    print("📊 OCR 识别结果概览")
    print("=" * 80)

    for i, row in enumerate(results, 1):
        (
            asset_id, title, status, asset_created,
            payload_schema, payload_version, payload, parsed_at
        ) = row

        print(f"\n【结果 {i}】")
        print(f"  Asset ID: {asset_id}")
        print(f"  标题: {title or '(未设置)'}")
        print(f"  状态: {status}")
        print(f"  上传时间: {asset_created}")
        print(f"  解析时间: {parsed_at}")

        if payload:
            payload_data = json.loads(payload)
            # OCR 数据在 annotations.ocr_lines 下
            annotations = payload_data.get('annotations', {})
            ocr_lines = annotations.get('ocr_lines', [])

            print(f"  Schema: {payload_schema}")
            print(f"  版本: {payload_version}")
            print(f"  识别行数: {len(ocr_lines)}")

            if ocr_lines:
                total_conf = sum(line.get('confidence', 0) for line in ocr_lines)
                avg_conf = total_conf / len(ocr_lines)
                print(f"  平均置信度: {avg_conf:.3f}")

                # 显示前 3 行识别结果
                print(f"\n  📝 前 3 行识别内容:")
                for j, line in enumerate(ocr_lines[:3], 1):
                    text = line.get('text', '')[:50]
                    conf = line.get('confidence', 0)
                    print(f"    {j}. [{conf:.3f}] {text}...")

                if len(ocr_lines) > 3:
                    print(f"    ... (还有 {len(ocr_lines) - 3} 行)")

    print("\n" + "=" * 80)

    # 保存最新结果到 JSON 文件
    if results and results[0][6]:  # payload 存在
        latest_payload = json.loads(results[0][6])
        output_file = Path("latest_ocr_result.json")

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(latest_payload, f, indent=2, ensure_ascii=False)

        print(f"✅ 最新结果已保存到: {output_file.absolute()}")
        print(f"   可以用文本编辑器或 VS Code 打开查看")

    conn.close()


def get_asset_by_id(asset_id: str):
    """根据 Asset ID 查看详细信息"""
    conn = sqlite3.connect("data/bdc_ai.db")
    cursor = conn.cursor()

    query = """
    SELECT
        a.id,
        a.title,
        a.status,
        a.modality,
        a.source,
        sp.schema_type,
        sp.payload
    FROM assets a
    LEFT JOIN asset_structured_payloads sp ON a.id = sp.asset_id
    WHERE a.id = ?
    """

    cursor.execute(query, (asset_id,))
    row = cursor.fetchone()

    if not row:
        print(f"❌ 未找到 Asset ID: {asset_id}")
        return

    (
        asset_id, title, status, modality, source,
        payload_schema, payload_json
    ) = row

    print(f"\n{'=' * 80}")
    print(f"📄 Asset 详细信息")
    print(f"{'=' * 80}")
    print(f"ID: {asset_id}")
    print(f"标题: {title or '(未设置)'}")
    print(f"状态: {status}")
    print(f"模态: {modality}")
    print(f"来源: {source}")
    print(f"Schema: {payload_schema or '(未解析)'}")

    if payload_json:
        payload = json.loads(payload_json)
        print(f"\n📊 OCR 数据:")
        print(json.dumps(payload, indent=2, ensure_ascii=False))

    conn.close()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        # 通过命令行参数指定 Asset ID
        asset_id = sys.argv[1]
        get_asset_by_id(asset_id)
    else:
        # 显示最新的结果概览
        view_latest_ocr_result()
