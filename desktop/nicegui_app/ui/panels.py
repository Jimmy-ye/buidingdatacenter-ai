"""
面板组件模块

提供可复用的面板组件和辅助函数

版本: v1.0
创建时间: 2025-01-22
"""

from typing import Any, Dict, Optional
import re


class AssetDetailHelper:
    """
    资产详情辅助类

    提供资产详情面板的更新逻辑
    """

    @staticmethod
    def format_basic_info(asset: Dict[str, Any]) -> Dict[str, Any]:
        """
        格式化资产基本信息

        Args:
            asset: 资产数据

        Returns:
            格式化后的信息字典
        """
        title = asset.get("title") or asset.get("id") or "资产详情"
        modality = asset.get("modality") or "-"
        role = asset.get("content_role") or "-"
        capture_time = asset.get("capture_time") or "-"
        description = asset.get("description") or "(无描述)"
        tags = asset.get("tags") or {}

        return {
            "title": str(title),
            "meta": f"类型: {modality} • 角色: {role} • 采集时间: {capture_time}",
            "body": str(description),
            "tags": f"Tags: {tags}" if tags else "",
            "is_image": str(modality).lower() == "image",
        }

    @staticmethod
    def extract_ocr_results(asset: Dict[str, Any]) -> Dict[str, Any]:
        """
        提取 OCR 识别结果

        Args:
            asset: 资产数据

        Returns:
            OCR 结果字典
        """
        is_meter = (str(asset.get("content_role", "")) == "meter")
        payloads = asset.get("structured_payloads") or []

        ocr_objects_text = ""
        ocr_text_text = ""
        all_numbers = []

        for sp in payloads:
            schema = sp.get("schema_type", "")
            data = sp.get("payload", {})

            # 图片 OCR 识别结果（表具类型跳过）
            if schema == "image_annotation" and not is_meter:
                annotations = data.get("annotations", {}) or {}
                ocr_lines = annotations.get("ocr_lines") or []

                # 显示所有 OCR 文本
                if ocr_lines:
                    texts = [line.get("text", "") for line in ocr_lines if line.get("text")]
                    if texts:
                        ocr_text = "\n".join(texts)
                        ocr_text_text = ocr_text
                else:
                    # 回退到 derived_text 字段
                    derived_text = data.get("derived_text")
                    if isinstance(derived_text, str) and derived_text:
                        ocr_text_text = derived_text

                # 显示 OCR 统计信息
                stats = data.get("stats", {})
                if stats:
                    engine = stats.get("engine", "unknown")
                    avg_conf = stats.get("avg_confidence", 0)
                    if isinstance(avg_conf, (int, float)):
                        ocr_objects_text = f"OCR 引擎: {engine}\n平均置信度: {avg_conf:.1%}\n识别行数: {len(ocr_lines)}"

                # 提取并显示所有数字
                if ocr_lines:
                    for line in ocr_lines:
                        text = line.get("text", "")
                        conf = line.get("confidence", 0)
                        # 提取所有数字（包括小数）
                        numbers = re.findall(r"\d+\.?\d*", text)
                        for num in numbers:
                            try:
                                val = float(num)
                                all_numbers.append({
                                    "value": val,
                                    "text": text,
                                    "confidence": conf
                                })
                            except ValueError:
                                pass

                    if all_numbers:
                        # 按数值排序
                        all_numbers.sort(key=lambda x: x["value"])

                        # 显示所有提取的数字
                        debug_lines = []
                        for item in all_numbers:
                            val = item["value"]
                            txt = item["text"]
                            conf = item.get("confidence", 0)
                            debug_lines.append(f"  {val:6.2f} (置信度: {conf:.1%}) - 来自: \"{txt}\"")

                        # 添加到 OCR 统计信息下方
                        ocr_objects_text = f"{ocr_objects_text}\n\n【提取到的所有数字】\n" + "\n".join(debug_lines)

        return {
            "ocr_objects": ocr_objects_text,
            "ocr_text": ocr_text_text,
        }

    @staticmethod
    def extract_llm_results(asset: Dict[str, Any]) -> str:
        """
        提取 LLM 分析结果

        Args:
            asset: 资产数据

        Returns:
            LLM 结果文本
        """
        payloads = asset.get("structured_payloads") or []
        llm_text = ""

        if not payloads:
            return llm_text

        # 为避免同一 schema 多次识别时出现重复块，这里按 schema_type 折叠，
        # 仅保留每种 schema 的最新版本（根据 version 字段判断）。
        latest_by_schema: Dict[str, Any] = {}
        for sp in payloads:
            if not isinstance(sp, dict):
                continue
            schema = sp.get("schema_type", "")
            if not schema:
                continue
            try:
                version = float(sp.get("version", 0) or 0)
            except Exception:
                version = 0.0

            existing = latest_by_schema.get(schema)
            if existing is None:
                latest_by_schema[schema] = sp
            else:
                try:
                    existing_version = float(existing.get("version", 0) or 0)
                except Exception:
                    existing_version = 0.0
                if version >= existing_version:
                    latest_by_schema[schema] = sp

        # 按固定顺序渲染：场景问题 → 铭牌 → 仪表
        for schema in ["scene_issue_report_v1", "nameplate_table_v1", "meter_reading_v1"]:
            sp = latest_by_schema.get(schema)
            if not sp:
                continue
            data = sp.get("payload", {}) or {}

            # 现场问题 LLM 分析结果
            if schema == "scene_issue_report_v1":
                parts = []

                issue_title = data.get("title", "")
                if issue_title:
                    parts.append(f"【问题】{issue_title}")

                summary = data.get("summary", "")
                if summary:
                    if len(summary) > 300:
                        summary = summary[:300] + "..."
                    parts.append(f"【摘要】{summary}")

                actions = data.get("recommended_actions") or []
                if actions:
                    action_text = "\n".join([f"• {a}" for a in actions[:3]])
                    parts.append(f"【建议】\n{action_text}")

                if parts:
                    block = "\n".join(parts)
                    if llm_text:
                        llm_text += "\n\n" + block
                    else:
                        llm_text = block

            # 铭牌表格解析结果
            if schema == "nameplate_table_v1":
                lines = ["【铭牌信息】"]

                equipment_type = data.get("equipment_type")
                if equipment_type:
                    lines.append(f"设备类型: {equipment_type}")

                fields = data.get("fields") or []
                if fields:
                    lines.append("关键参数:")
                    for field in fields[:8]:
                        label = field.get("label") or field.get("key") or ""
                        value = field.get("value")
                        unit = field.get("unit")
                        confidence = field.get("confidence")

                        value_str = "" if value is None else str(value)
                        if unit:
                            value_str = f"{value_str} {unit}".strip()

                        if confidence is not None:
                            try:
                                conf_str = f" (置信度: {float(confidence):.0%})"
                            except Exception:
                                conf_str = ""
                        else:
                            conf_str = ""

                        if label or value_str:
                            lines.append(f"• {label}: {value_str}{conf_str}")

                if len(lines) > 1:
                    block = "\n".join(lines)
                    if llm_text:
                        llm_text += "\n\n" + block
                    else:
                        llm_text = block

            # 仪表读数解析结果
            if schema == "meter_reading_v1":
                lines = ["【仪表读数】"]

                reading = data.get("reading")
                unit = data.get("unit") or ""
                pre_reading = data.get("pre_reading")
                status = data.get("status") or ""
                summary = data.get("summary") or ""
                confidence = data.get("confidence")

                if reading is not None:
                    try:
                        reading_val = float(reading)
                        reading_str = f"{reading_val:g}{unit}".strip()
                    except Exception:
                        reading_str = f"{reading}{unit}".strip()
                    lines.append(f"当前读数: {reading_str}")

                if pre_reading is not None:
                    try:
                        pre_val = float(pre_reading)
                        pre_str = f"{pre_val:g}{unit}".strip()
                    except Exception:
                        pre_str = f"{pre_reading}{unit}".strip()
                    lines.append(f"预读数: {pre_str}")

                if status:
                    lines.append(f"状态: {status}")

                if summary:
                    if len(summary) > 300:
                        summary = summary[:300] + "..."
                    lines.append(f"说明: {summary}")

                if confidence is not None:
                    try:
                        lines.append(f"置信度: {float(confidence):.0%}")
                    except Exception:
                        pass

                if len(lines) > 1:
                    block = "\n".join(lines)
                    if llm_text:
                        llm_text += "\n\n" + block
                    else:
                        llm_text = block

        return llm_text

    @staticmethod
    def update_inference_status(asset: Optional[Dict[str, Any]], ui_elements: Dict[str, Any]) -> None:
        """
        更新推理状态和按钮可用性

        Args:
            asset: 资产数据（None 表示清空）
            ui_elements: UI 元素字典，包含：
                - inference_status_label
                - run_ocr_button
                - run_llm_button
        """
        if not asset:
            ui_elements["inference_status_label"].text = ""

            run_ocr_button = ui_elements.get("run_ocr_button")
            if run_ocr_button is not None:
                run_ocr_button.disabled = True

            run_llm_button = ui_elements.get("run_llm_button")
            if run_llm_button is not None:
                run_llm_button.disabled = True

            return

        status = str(asset.get("status") or "").lower()
        modality = str(asset.get("modality") or "").lower()
        role = str(asset.get("content_role") or "").lower()

        # 根据状态显示消息
        msg = ""
        if not status:
            msg = "未解析，点击下方按钮运行 OCR 或提交 LLM 分析"
        elif status == "parsed_ocr_ok":
            msg = "OCR 完成（置信度较高）"
        elif status == "parsed_ocr_low_conf":
            msg = "OCR 完成（置信度较低，建议人工复核）"
        elif status == "pending_scene_llm":
            msg = "已提交到 LLM 管线，等待分析结果……"
        elif status == "parsed_scene_llm":
            msg = "LLM 场景分析已完成"
        elif status == "parsed_nameplate_llm":
            msg = "铭牌信息解析已完成"
        elif status == "parsed_meter_llm":
            msg = "仪表读数解析已完成"
        else:
            msg = f"当前状态: {status}"

        ui_elements["inference_status_label"].text = msg

        # 根据模态类型和角色启用/禁用按钮
        is_image = modality == "image"

        run_ocr_button = ui_elements.get("run_ocr_button")
        if run_ocr_button is not None:
            run_ocr_button.disabled = not is_image

        run_llm_button = ui_elements.get("run_llm_button")
        if run_llm_button is not None:
            run_llm_button.disabled = not (is_image and role in {"scene_issue", "meter", "nameplate"})

    @staticmethod
    def update_detail_panel(
        asset: Optional[Dict[str, Any]],
        ui_elements: Dict[str, Any],
    ) -> None:
        """
        更新资产详情面板

        Args:
            asset: 资产数据（None 表示清空）
            ui_elements: UI 元素字典，包含：
                - detail_title
                - detail_meta
                - detail_body
                - detail_tags
                - preview_image
                - preview_button
                - ocr_objects_label
                - ocr_text_label
                - llm_summary_label
                - inference_status_label
                - run_ocr_button
                - run_llm_button
        """
        if not asset:
            # 清空显示
            ui_elements["detail_title"].text = "资产详情"
            ui_elements["detail_meta"].text = ""
            ui_elements["detail_body"].text = "请选择左侧设备，加载资产后查看详情。"
            ui_elements["detail_tags"].text = ""
            ui_elements["preview_image"].visible = False
            ui_elements["preview_image"].source = ""

            preview_button = ui_elements.get("preview_button")
            if preview_button is not None:
                preview_button.disabled = True

            ui_elements["inference_status_label"].text = ""

            run_ocr_button = ui_elements.get("run_ocr_button")
            if run_ocr_button is not None:
                run_ocr_button.disabled = True

            run_llm_button = ui_elements.get("run_llm_button")
            if run_llm_button is not None:
                run_llm_button.disabled = True

            ui_elements["ocr_objects_label"].text = ""
            ui_elements["ocr_text_label"].text = ""
            ui_elements["llm_summary_label"].text = ""
            return

        # 格式化基本信息
        info = AssetDetailHelper.format_basic_info(asset)
        ui_elements["detail_title"].text = info["title"]
        ui_elements["detail_meta"].text = info["meta"]
        ui_elements["detail_body"].text = info["body"]
        ui_elements["detail_tags"].text = info["tags"]

        # 更新预览按钮状态（按钮可能为可选）
        preview_button = ui_elements.get("preview_button")
        if preview_button is not None:
            preview_button.disabled = not info["is_image"]

        # 清空 OCR/LLM 结果区域
        ui_elements["ocr_objects_label"].text = ""
        ui_elements["ocr_text_label"].text = ""
        ui_elements["llm_summary_label"].text = ""

        # 提取并显示 OCR 结果
        ocr_results = AssetDetailHelper.extract_ocr_results(asset)
        if ocr_results["ocr_objects"]:
            ui_elements["ocr_objects_label"].text = ocr_results["ocr_objects"]
        if ocr_results["ocr_text"]:
            ui_elements["ocr_text_label"].text = ocr_results["ocr_text"]

        # 提取并显示 LLM 结果
        llm_text = AssetDetailHelper.extract_llm_results(asset)
        if llm_text:
            ui_elements["llm_summary_label"].text = llm_text

        # 更新推理状态
        AssetDetailHelper.update_inference_status(asset, ui_elements)


# ==================== 便捷函数 ====================

def update_asset_detail_panel(
    asset: Optional[Dict[str, Any]],
    ui_elements: Dict[str, Any],
) -> None:
    """
    更新资产详情面板（便捷函数）

    Args:
        asset: 资产数据（None 表示清空）
        ui_elements: UI 元素字典
    """
    AssetDetailHelper.update_detail_panel(asset, ui_elements)
