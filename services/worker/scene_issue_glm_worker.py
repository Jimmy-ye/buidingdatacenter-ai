import os
import time
import base64
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from difflib import SequenceMatcher

import requests
from openai import OpenAI
from PIL import Image
import io
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# ================= 配置区域 =================
# 后端服务地址（FastAPI）
BACKEND_BASE_URL = os.getenv("BDC_BACKEND_BASE_URL", "http://127.0.0.1:8000").rstrip("/")

# 与后端 settings.local_storage_dir 保持一致，用于读取本地图片文件
# 默认使用项目根目录下的 data/assets；如果配置为相对路径，则基于项目根目录解析
LOCAL_STORAGE_DIR = os.getenv("BDC_LOCAL_STORAGE_DIR", "data/assets")
if not os.path.isabs(LOCAL_STORAGE_DIR):
    # 获取项目根目录（从 services/worker 向上 3 级）
    # 使用明确的 parent 调用，避免 .parents[] 在 Windows 上的问题
    PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
    LOCAL_STORAGE_DIR = str(PROJECT_ROOT / LOCAL_STORAGE_DIR)

# 可选：仅处理某个项目的 scene_issue 资产
PROJECT_ID_FILTER = os.getenv("BDC_SCENE_PROJECT_ID")  # 留空则处理所有项目

# GLM API 配置（兼容 OpenAI SDK）
GLM_API_KEY = os.getenv("GLM_API_KEY", "")
GLM_BASE_URL = os.getenv("GLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4/")
VISION_MODEL = os.getenv("GLM_VISION_MODEL", "glm-4v")

# Worker 轮询间隔 (秒)
POLL_INTERVAL = int(os.getenv("BDC_SCENE_WORKER_POLL_INTERVAL", "600"))

if not GLM_API_KEY:
    raise RuntimeError("GLM_API_KEY is not set in environment variables")

client = OpenAI(api_key=GLM_API_KEY, base_url=GLM_BASE_URL)


# ================= 辅助函数 =================

def get_pending_scene_assets() -> List[Dict[str, Any]]:
    """从后端获取待 LLM 处理的图片资产列表（scene_issue / meter / nameplate）。"""

    roles = ["scene_issue", "meter", "nameplate"]
    collected: Dict[str, Dict[str, Any]] = {}

    for role in roles:
        params: Dict[str, Any] = {
            "modality": "image",
            "content_role": role,
        }
        if PROJECT_ID_FILTER:
            params["project_id"] = PROJECT_ID_FILTER

        resp = requests.get(f"{BACKEND_BASE_URL}/api/v1/assets", params=params, timeout=30)
        if resp.status_code != 200:
            print(f"[WARN] Failed to fetch assets for role={role}: HTTP {resp.status_code} {resp.text}")
            continue

        assets = resp.json()
        if not isinstance(assets, list):
            print(f"[WARN] Unexpected assets response shape for role={role} (expected list)")
            continue

        for a in assets:
            if a.get("status") == "pending_scene_llm":
                asset_id = a.get("id")
                if asset_id:
                    collected[str(asset_id)] = a

    return list(collected.values())


def get_asset_detail(asset_id: str) -> Dict[str, Any]:
    resp = requests.get(f"{BACKEND_BASE_URL}/api/v1/assets/{asset_id}", timeout=30)
    resp.raise_for_status()
    return resp.json()


def get_image_content_from_detail(detail: Dict[str, Any]):
    """根据 AssetDetail 返回的 file_path 构造本地图片内容。"""

    file_path = detail.get("file_path")
    if not file_path:
        print(f"[WARN] asset {detail.get('id')} has no file_path; cannot load image")
        return None

    # 标准化路径：统一使用正斜杠，处理 Windows 反斜杠问题
    file_path = file_path.replace("\\", "/").replace("//", "/")

    full_path = Path(LOCAL_STORAGE_DIR) / file_path
    if not full_path.is_file():
        print(f"[WARN] Local image file not found: {full_path}")
        return None

    try:
        with Image.open(full_path) as img:
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            buffered = io.BytesIO()
            img.save(buffered, format="JPEG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            base64_url = f"data:image/jpeg;base64,{img_str}"
            return {"type": "image_url", "image_url": {"url": base64_url}}
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR] Error processing image {full_path}: {exc}")
        return None


def build_scene_prompt(note: Optional[str]) -> str:
    """构造发送给 GLM-4V 的中文 Prompt，要求输出 SceneIssueReportPayload JSON（场景问题）。"""

    base = """
你是一名建筑设备运行状态评估专家。
你的任务是客观评估现场照片中设备的运行状态，区分"正常使用痕迹"和"需要关注的问题"。

评估原则：
1. 正常使用痕迹（轻微污垢、自然老化、轻微积灰）不是问题，不需要标记
2. 只有影响设备性能、安全或美观的明显异常才需要报告
3. 如果不确定，宁可标记为 low 或不报告问题
4. 大多数设备是正常的，不要过度诊断

严重程度定义：
- low：设备状态正常，或仅有极轻微问题不影响运行（如轻微积灰、正常老化）
- medium：明确的问题，有一定影响但非紧急（如明显污垢影响换热、轻微漏水）
- high：严重问题，需要立即处理（如大量漏水、设备故障、明显安全隐患）

严格按照下列 JSON 结构输出，不要包含任何多余文字或 markdown：
{
  "title": "一句话的简短标题，如果设备正常则为空",
  "issue_category": "问题类别（如：冷源效率、控制策略、设备维护、安全隐患、舒适性），正常则为空",
  "severity": "low | medium | high（正常设备使用 low）",
  "summary": "状态描述。如果设备正常，明确说明'设备运行状态正常，未发现异常'",
  "suspected_causes": ["可能原因列表，正常则为空"],
  "recommended_actions": ["建议措施列表，正常则可为常规维护建议"],
  "confidence": 0.0-1.0之间的数字（反映判断的确定程度，不确定时应降低到0.6-0.7）",
  "tags": ["标签列表（如：设备类型、状态等）"]
}

重要提示：
- 如果设备状态正常，severity 设为 "low"，summary 必须明确说明"运行正常"
- 置信度应该反映你的判断确定性，不要过高（正常状态可给0.8-0.9，不确定的问题给0.6-0.8）
- 严格输出 JSON 对象（最外层是 { ... }），不要输出 explain、注释或 markdown
""".strip()

    if note:
        base += f"""

工程师备注（仅供参考，以图片为主）：{note}
重要约束：summary 必须基于图片中可见信息独立撰写，不得逐字复制备注；如备注与图片不一致，一律以图片为准。
"""
    return base


def build_meter_prompt(pre_reading: Optional[float], note: Optional[str]) -> str:
    """构造发送给 GLM-4V 的 Prompt，用于仪表读数结构化识别（MeterReadingPayload）。"""

    base = """
你是一名建筑设备仪表读数识别助手。
你的任务是阅读图片中的仪表/表盘，并给出尽可能准确、可解释的数值读数。

重要要求：
1. 优先识别表盘或数字仪表上的读数（例如温度、压力、流量、电表读数等）。
2. 如果图片中有多个相关读数，可以都列出，但最终需要给出一个主要读数 reading。
3. 如果读数模糊、被遮挡或你不确定，请务必在 summary 中明确写出"读数不确定，需要人工确认"，不要胡乱猜测。

请严格按照下列 JSON 结构输出，不要包含任何多余文字或 markdown：
{
  "pre_reading": 65.0,
  "reading": 64.8,
  "unit": "℃",
  "status": "confirmed_from_image",
  "summary": "...",
  "confidence": 0.85,
  "tags": ["仪表", "温度"]
}

字段说明：
- pre_reading: 工程师预读数（如果有），可以用来对比；如果没有可为 null。
- reading: 你根据图片识别到的主要读数；如果图片不清晰无法可靠读数，可以与 pre_reading 相同，但必须在 summary 中说明"读数不确定，需要人工确认"。
- unit: 单位（如 ℃, kW, m3/h），看不出时可以为 null。
- status 取值建议：
  - "confirmed_from_image": 图片清晰，可以给出可信的读数；如与预读数接近，可在 summary 中说明一致或接近。
  - "fallback_to_pre_reading": 图片不清晰，无法给出可靠读数；此时 reading 应等于 pre_reading，summary 必须说明基于预读数，需人工确认。
  - "inconsistent_require_manual": 图片读数与预读数明显不一致，建议人工复核。
- summary: 用自然语言说明你如何判断该读数、是否需要人工确认，以及与预读数的关系。读数不确定时必须包含"读数不确定，需要人工确认"等提示。
- confidence: 0.0-1.0 之间的数字，读数不确定或图像质量差时应降低到 0.5-0.7。
- tags: 标签列表，例如 ["仪表", "读数", "meter"]。

重要提示：
- 严格输出 JSON 对象（最外层是 { ... }），不要输出 explain、注释或 markdown。
""".strip()

    if pre_reading is not None:
        base += f"""

工程师提供的预读数 pre_reading={pre_reading}。你可以参考该数值，但必须首先基于图片独立判断实际读数，如与图片不一致要在 summary 中说明并提示人工确认。
"""

    if note:
        base += f"""

工程师备注（仅供参考，以实际仪表为准）：{note}
重要约束：summary 必须基于图片中的仪表读数独立撰写，不得逐字复制备注；如备注与图片不一致，一律以图片为准。
"""
    return base


def build_nameplate_prompt(note: Optional[str]) -> str:
    """构造发送给 GLM-4V 的 Prompt，用于通用建筑用能设备铭牌抽取，输出 nameplate_table_v1。"""

    base = """
你是一个严谨的建筑能耗设备“铭牌”解析助手。

你的任务：
1. 输入：一张图片（由系统单独传入）以及从该图片/OCR 得到的一段文本（如果有备注，将在后面给出）。
2. 输出：一个 JSON 对象，字段结构必须严格符合 nameplate_table_v1 规范，用于描述建筑内用能设备的铭牌信息。

第一步：先判断是否为“建筑用能设备铭牌”
- 如果明显不是（例如饮料瓶、食品营养成分表、广告海报等），则：
  - is_energy_equipment = false
  - not_energy_reason 写明原因（例如 "image_is_beverage_can_label"）
  - 其余字段全部使用 null 或空结构。

第二步：如果是建筑用能设备铭牌
- 典型设备包括但不限于：冷水机组、热泵机组、冷却塔、冷/热水泵、风机盘管、空调机组、新风机组、锅炉、换热机组、空压机、电机/风机、变压器等。
- 你需要填充以下 JSON 结构（只从铭牌文本中“抄”，禁止编造）：

{
  "version": "nameplate_table_v1",

  "is_energy_equipment": true,
  "not_energy_reason": null,

  "equipment": {
    "category": "chiller | heat_pump | cooling_tower | boiler | pump | fan | ahu | fcu | heat_exchanger | air_compressor | cooling_unit | transformer | other",
    "subtype": "可选，自由文本子类型，例如 water_cooled_chiller",
    "name_cn": "中文设备名称，如 离心式冷水机组",
    "name_en": null,
    "brand": "品牌，如 某某牌",
    "model": "型号",
    "series": null,
    "serial_number": null,
    "factory_code": null,
    "manufacture_date": "尽量用 YYYY-MM 或 YYYY，例如 2023-05",
    "standard_code": null
  },

  "energy_parameters": {
    "rated_cooling_capacity_kw": null,
    "rated_heating_capacity_kw": null,
    "rated_power_input_kw": null,
    "motor_power_kw": null,
    "air_flow_m3h": null,
    "water_flow_m3h": null,
    "cop": null,
    "eer": null,
    "iplv": null,
    "efficiency_percent": null,
    "energy_efficiency_grade": null
  },

  "electrical_parameters": {
    "voltage_v": null,
    "phase": null,
    "frequency_hz": null,
    "current_a": null,
    "power_factor": null
  },

  "working_conditions": {
    "inlet_water_temp_c": null,
    "outlet_water_temp_c": null,
    "ambient_temp_c": null,
    "condensing_temp_c": null,
    "evaporating_temp_c": null,
    "other_condition_note": null
  },

  "refrigerant_and_medium": {
    "refrigerant_type": null,
    "refrigerant_charge_kg": null,
    "heat_transfer_medium": null
  },

  "mechanical_parameters": {
    "pressure_level_mpa": null,
    "speed_rpm": null,
    "head_m": null
  },

  "location_info": {
    "project_name": null,
    "system_name": null,
    "device_label": null
  },

  "raw_text": "请在这里原样放入你识别到的完整铭牌文字（包括重要数字和单位）",
  "parse_confidence": 0.0,
  "unknown_parameters": []
}

字段与行为要求：
- equipment.category 必须从下列枚举中选择一个：
  ["chiller","heat_pump","cooling_tower","boiler","pump","fan","ahu","fcu","heat_exchanger","air_compressor","cooling_unit","transformer","other"]。
- 所有数值类字段，只能在铭牌文本中能找到清晰的数值和单位时才填写；否则保持为 null。
- 如果铭牌使用的是 RT 等单位（例如制冷量），你可以：
  - 如果铭牌同时给出了 kW，则填入 kW；
  - 否则不要自行换算，只在 unknown_parameters 里记录原始数值和单位。
- unknown_parameters 用来记录你认为与能耗或设备识别相关、但上述结构中没有专门字段的参数，例如：
  {
    "label": "额定出水温度",
    "value": "7℃",
    "unit": "°C",
    "category": "working_condition"
  }
- parse_confidence 取值在 0.0 到 1.0 之间，用于反映你对整体解析结果的信心；
  - 字体清晰、字段齐全时可以在 0.8~0.95；
  - 图片模糊或缺失时应降低到 0.5~0.75。

严禁：
- 严禁凭空编造任何数值或参数。
- 严禁因为“看起来像冷机”就假设一个制冷量或功率。
- 如果无法确认，就把对应字段设为 null，并如实在 raw_text 或 unknown_parameters 中体现原始文字。

输出要求：
- 最外层必须是一个 JSON 对象，字段名严格按照 nameplate_table_v1 的结构。
- 不要输出任何额外文字、解释、注释或 markdown，只输出 JSON。
""".strip()

    if note:
        base += f"""

工程师备注（仅供参考，以图片为准）：{note}
重要约束：如备注与图片不一致，一律以图片为准；你必须优先相信图片信息，其次才参考备注。
"""
    return base


def call_glm_vision(image_content: Dict[str, Any], text_prompt: str) -> Optional[Dict[str, Any]]:
    """调用 GLM-4V，期望返回符合 SceneIssueReportPayload 的 JSON 对象。"""

    try:
        response = client.chat.completions.create(
            model=VISION_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        image_content,
                        {"type": "text", "text": text_prompt},
                    ],
                }
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        content = response.choices[0].message.content
        if isinstance(content, str):
            return json.loads(content)
        if isinstance(content, dict):
            return content
        print(f"[WARN] Unexpected GLM content type: {type(content)}")
        return None
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR] GLM API Error: {exc}")
        return None


def normalise_scene_payload(raw: Dict[str, Any], note: Optional[str] = None) -> Dict[str, Any]:
    """将 GLM 返回结果规范化为 SceneIssueReportPayload 结构。

    如果 summary 与工程师备注高度相似，则降低置信度并提示人工复核。
    """

    summary = raw.get("summary") or raw.get("description") or ""
    if not isinstance(summary, str):
        summary = str(summary)

    payload: Dict[str, Any] = {
        "title": raw.get("title"),
        "issue_category": raw.get("issue_category") or raw.get("issue_type"),
        "severity": raw.get("severity"),
        "summary": summary.strip() or "未能从图片中提取明确的问题，请人工复核。",
        "suspected_causes": raw.get("suspected_causes") or raw.get("causes") or [],
        "recommended_actions": raw.get("recommended_actions") or raw.get("actions") or [],
        "confidence": raw.get("confidence"),
        "tags": raw.get("tags") or [],
    }

    # 确保列表字段为 list[str]
    for key in ("suspected_causes", "recommended_actions", "tags"):
        val = payload.get(key)
        if isinstance(val, str):
            payload[key] = [val]
        elif not isinstance(val, list):
            payload[key] = []

    # 如果提供了工程师备注，且 summary 与备注高度相似，则认为过度依赖备注
    if note:
        note_text = str(note).strip()
        summary_text = str(payload.get("summary") or "").strip()
        if note_text and summary_text:
            ratio = SequenceMatcher(None, note_text, summary_text).ratio()
            if ratio >= 0.8 or note_text in summary_text or summary_text in note_text:
                conf = payload.get("confidence")
                if isinstance(conf, (int, float)):
                    payload["confidence"] = min(float(conf), 0.6)

                recs = payload.get("recommended_actions") or []
                if not isinstance(recs, list):
                    recs = [str(recs)]
                hint = "请人工核对：本次分析高度依赖工程师备注，结论仅供参考。"
                if hint not in recs:
                    recs.append(hint)
                payload["recommended_actions"] = recs

    return payload


def post_scene_issue_report(asset_id: str, payload: Dict[str, Any]) -> bool:
    url = f"{BACKEND_BASE_URL}/api/v1/assets/{asset_id}/scene_issue_report"
    try:
        resp = requests.post(url, json=payload, timeout=60)
        if resp.status_code in (200, 201):
            print(f"[OK] Reported scene_issue_report_v1 for asset {asset_id}")
            return True
        print(f"[WARN] Failed to post report for {asset_id}: HTTP {resp.status_code} {resp.text}")
        return False
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR] Exception while posting report for {asset_id}: {exc}")
        return False


def post_nameplate_table(asset_id: str, payload: Dict[str, Any]) -> bool:
    url = f"{BACKEND_BASE_URL}/api/v1/assets/{asset_id}/nameplate_table"
    try:
        resp = requests.post(url, json=payload, timeout=60)
        if resp.status_code in (200, 201):
            print(f"[OK] Reported nameplate_table_v1 for asset {asset_id}")
            return True
        print(f"[WARN] Failed to post nameplate table for {asset_id}: HTTP {resp.status_code} {resp.text}")
        return False
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR] Exception while posting nameplate table for {asset_id}: {exc}")
        return False


def post_meter_reading(asset_id: str, payload: Dict[str, Any]) -> bool:
    url = f"{BACKEND_BASE_URL}/api/v1/assets/{asset_id}/meter_reading"
    try:
        resp = requests.post(url, json=payload, timeout=60)
        if resp.status_code in (200, 201):
            print(f"[OK] Reported meter_reading_v1 for asset {asset_id}")
            return True
        print(f"[WARN] Failed to post meter reading for {asset_id}: HTTP {resp.status_code} {resp.text}")
        return False
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR] Exception while posting meter reading for {asset_id}: {exc}")
        return False


# ================= 主循环 =================

def process_once() -> None:
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Checking for pending scene_issue/meter/nameplate assets...")
    assets = get_pending_scene_assets()
    if not assets:
        print("No pending assets found.")
        return

    for asset in assets:
        asset_id = asset.get("id")
        if not asset_id:
            continue

        role = (asset.get("content_role") or "").lower()
        print(f"Processing asset {asset_id} (role={role}) ...")
        try:
            detail = get_asset_detail(asset_id)
        except Exception as exc:  # noqa: BLE001
            print(f"[WARN] Failed to fetch asset detail {asset_id}: {exc}")
            continue

        image_content = get_image_content_from_detail(detail)
        if not image_content:
            continue

        note = detail.get("description") or ""
        meta = detail.get("location_meta") or {}
        pre_reading = None
        if isinstance(meta, dict):
            pre_reading = meta.get("meter_pre_reading")

        # 根据 content_role 选择不同的 Prompt 和后端端点：
        role = (detail.get("content_role") or "").lower()
        if role == "nameplate":
            prompt = build_nameplate_prompt(note)
        elif role == "meter":
            prompt = build_meter_prompt(pre_reading, note)
        else:
            prompt = build_scene_prompt(note)

        raw_result = call_glm_vision(image_content, prompt)
        if not raw_result:
            print(f"[WARN] GLM returned empty/invalid result for asset {asset_id}")
            continue

        if role == "nameplate":
            post_nameplate_table(asset_id, raw_result)
        elif role == "meter":
            post_meter_reading(asset_id, raw_result)
        else:
            payload = normalise_scene_payload(raw_result, note)
            post_scene_issue_report(asset_id, payload)


def main() -> None:
    print("Starting GLM-4V scene_issue worker...")
    print(f"Backend: {BACKEND_BASE_URL}")
    print(f"Local storage dir: {LOCAL_STORAGE_DIR}")
    while True:
        process_once()
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
