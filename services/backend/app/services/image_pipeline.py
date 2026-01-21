from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from sqlalchemy.orm import Session

from shared.config.settings import get_settings
from shared.db.models_asset import Asset, AssetStructuredPayload, FileBlob

try:
    from paddleocr import PaddleOCR
except ImportError:  # pragma: no cover - optional dependency
    PaddleOCR = None  # type: ignore[assignment]


settings = get_settings()
_ocr_client: PaddleOCR | None = None  # type: ignore[name-defined]


@dataclass
class OcrLine:
    text: str
    bbox: List[List[float]]
    confidence: float


def _get_ocr_client() -> PaddleOCR:
    if PaddleOCR is None:
        raise RuntimeError(
            "PaddleOCR is not installed. Please install 'paddleocr' and its dependencies."
        )

    global _ocr_client
    if _ocr_client is None:
        _ocr_client = PaddleOCR(use_angle_cls=True, lang="ch")  # type: ignore[call-arg]
    return _ocr_client


def _resolve_image_path(db: Session, asset_or_id) -> Tuple[Asset, str]:
    """Resolve image path from an Asset instance or asset ID.

    Args:
        db: Database session
        asset_or_id: Asset instance, UUID object, or UUID string
    """

    # Allow passing an already-loaded Asset to avoid extra queries and
    # sidestep any backend-specific UUID quirks during development.
    if isinstance(asset_or_id, Asset):
        asset = asset_or_id
    else:
        # Normalise to uuid.UUID, which is what the PostgreSQL UUID type
        # (and SQLAlchemy's dialect) expects as the Python-side value.
        if isinstance(asset_or_id, uuid.UUID):
            asset_uuid = asset_or_id
        else:
            asset_uuid = uuid.UUID(str(asset_or_id))

        asset: Asset | None = db.query(Asset).filter(Asset.id == asset_uuid).one_or_none()
        if asset is None:
            raise ValueError("Asset not found")

    if asset.modality != "image":
        raise ValueError("Asset modality must be 'image' for image parsing")

    file_blob: FileBlob | None = db.query(FileBlob).filter(FileBlob.id == asset.file_id).one_or_none()
    if file_blob is None:
        raise ValueError("FileBlob not found for asset")

    abs_path = os.path.join(settings.local_storage_dir, file_blob.path)
    if not os.path.exists(abs_path):
        raise FileNotFoundError(f"Image file not found at {abs_path}")

    return asset, abs_path


def _run_paddle_ocr(image_path: str) -> List[OcrLine]:
    ocr = _get_ocr_client()
    # Some PaddleOCR versions accept cls=True, newer versions may not.
    # Try with cls flag first, and fall back to a plain call if the
    # underlying predict() API does not support this argument.
    try:
        result = ocr.ocr(image_path, cls=True)
    except TypeError:
        result = ocr.ocr(image_path)

    # Handle case where PaddleOCR returns None (no text detected)
    if result is None:
        return []

    lines: List[OcrLine] = []
    for page in result:
        if page is None:
            continue
        for line in page:
            bbox = line[0]
            text = line[1][0]
            confidence = float(line[1][1])
            lines.append(OcrLine(text=text, bbox=bbox, confidence=confidence))
    return lines


def process_image_with_ocr(db: Session, asset_or_id) -> AssetStructuredPayload:
    """Run PaddleOCR on an image asset and store result as AssetStructuredPayload.

    This is the first layer of the image parsing pipeline.

    Args:
        db: Database session
        asset_or_id: Asset instance, UUID object, or UUID string
    """
    asset, abs_path = _resolve_image_path(db, asset_or_id)
    lines = _run_paddle_ocr(abs_path)

    if lines:
        avg_conf = sum(l.confidence for l in lines) / len(lines)
    else:
        avg_conf = 0.0

    payload: Dict[str, Any] = {
        "image_meta": {
            "path": abs_path,
        },
        "annotations": {
            "objects": [],
            "ocr_lines": [
                {
                    "text": l.text,
                    "bbox": l.bbox,
                    "confidence": l.confidence,
                }
                for l in lines
            ],
            "global_tags": [],
        },
        "derived_text": "\n".join(l.text for l in lines),
        "stats": {
            "avg_confidence": avg_conf,
            "engine": "paddleocr",
        },
    }

    # versioning: simple strategy, increment based on existing payloads count
    existing_count = (
        db.query(AssetStructuredPayload)
        .filter(AssetStructuredPayload.asset_id == asset.id)
        .count()
    )

    structured = AssetStructuredPayload(
        asset_id=asset.id,
        schema_type="image_annotation",
        payload=payload,
        version=float(existing_count + 1),
        created_by="ocr",
    )
    db.add(structured)

    # update asset status based on confidence
    if avg_conf >= 0.8:
        asset.status = "parsed_ocr_ok"
    else:
        asset.status = "parsed_ocr_low_conf"

    db.commit()
    db.refresh(structured)

    return structured


def route_image_asset(db: Session, asset_or_id) -> Asset:
    """Route an image asset to the appropriate pipeline based on content_role.

    - meter/nameplate: run OCR pipeline immediately
    - scene_issue/other: mark as pending for LLM-based scene analysis

    Args:
        db: Database session
        asset_or_id: Asset instance, UUID object, or UUID string
    """

    print(f"[DEBUG] route_image_asset called with asset_or_id={asset_or_id}")

    if asset_or_id is None:
        raise ValueError("Asset or asset_id cannot be empty")

    # Accept a pre-loaded Asset (e.g. immediately after upload) to avoid an
    # extra lookup, but also support being called from endpoints with an ID.
    if isinstance(asset_or_id, Asset):
        asset = asset_or_id
    else:
        if isinstance(asset_or_id, uuid.UUID):
            asset_uuid = asset_or_id
        else:
            asset_uuid = uuid.UUID(str(asset_or_id))

        asset: Asset | None = db.query(Asset).filter(Asset.id == asset_uuid).one_or_none()
        if asset is None:
            raise ValueError("Asset not found")

    if asset.modality != "image":
        raise ValueError("Asset modality must be 'image' for image routing")

    role = (asset.content_role or "").lower()

    # 对仪表类图片：
    # 1）先跑 OCR，得到结构化文本
    # 2）同时也进入 LLM 管线，用于辅助识别读数
    if role == "meter":
        print(f"[DEBUG] Processing meter asset: {asset.id}, role={role}")
        process_image_with_ocr(db, asset)

        existing_count = (
            db.query(AssetStructuredPayload)
            .filter(AssetStructuredPayload.asset_id == asset.id)
            .count()
        )

        payload: Dict[str, Any] = {
            "route": "scene_llm_pipeline",
            "reason": "meter image also scheduled for LLM meter-reading analysis",
            "content_role": asset.content_role,
        }

        decision = AssetStructuredPayload(
            asset_id=asset.id,
            schema_type="image_route_decision_v1",
            payload=payload,
            version=float(existing_count + 1),
            created_by="router",
        )
        db.add(decision)

        print(f"[DEBUG] Setting asset status to pending_scene_llm")
        asset.status = "pending_scene_llm"
        db.commit()
        db.refresh(asset)
        print(f"[DEBUG] Asset status after commit: {asset.status}")
        return asset

    # 铭牌等仍然只跑 OCR，不进入 LLM
    if role == "nameplate":
        process_image_with_ocr(db, asset)
        db.refresh(asset)
        return asset

    # 其他（如 scene_issue）：只做路由，进入场景 LLM 管线
    existing_count = (
        db.query(AssetStructuredPayload)
        .filter(AssetStructuredPayload.asset_id == asset.id)
        .count()
    )

    payload: Dict[str, Any] = {
        "route": "scene_llm_pipeline",
        "reason": "content_role is not meter/nameplate; delegate to scene understanding pipeline",
        "content_role": asset.content_role,
    }

    decision = AssetStructuredPayload(
        asset_id=asset.id,
        schema_type="image_route_decision_v1",
        payload=payload,
        version=float(existing_count + 1),
        created_by="router",
    )
    db.add(decision)

    asset.status = "pending_scene_llm"
    db.commit()
    db.refresh(asset)
    return asset
