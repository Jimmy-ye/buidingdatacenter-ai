import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict


class FileBlobCreate(BaseModel):
    storage_type: str = "minio"
    bucket: str
    path: str
    file_name: str
    content_type: Optional[str] = None
    size: Optional[float] = None
    hash: Optional[str] = None


class AssetBase(BaseModel):
    project_id: uuid.UUID
    building_id: Optional[uuid.UUID] = None
    zone_id: Optional[uuid.UUID] = None
    system_id: Optional[uuid.UUID] = None
    device_id: Optional[uuid.UUID] = None

    modality: str
    source: str
    content_role: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None

    capture_time: Optional[datetime] = None
    location_meta: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    quality_score: Optional[float] = None
    status: Optional[str] = None


class AssetCreate(AssetBase):
    file: FileBlobCreate


class AssetRead(AssetBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    file_id: uuid.UUID
    # Human-readable engineering path like "Building / Zone / System / Device"
    engineer_path: Optional[str] = None


class AssetStructuredPayloadRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    schema_type: str
    payload: Dict[str, Any]
    version: float
    created_by: Optional[str] = None
    created_at: datetime


class AssetDetailRead(AssetRead):
    structured_payloads: List[AssetStructuredPayloadRead] = []
    # Relative file path within local storage, derived from FileBlob.path
    file_path: Optional[str] = None


class SceneIssueReportPayload(BaseModel):
    """Structured payload for LLM-based scene issue understanding.

    This is intended to be stored under schema_type="scene_issue_report_v1"
    in AssetStructuredPayload.payload.
    """

    title: Optional[str] = None
    issue_category: Optional[str] = None  # e.g. "冷源效率", "控制策略", "设备维护"
    severity: Optional[str] = None  # e.g. low/medium/high
    summary: str  # concise description of the observed issue or status
    suspected_causes: List[str] = []
    recommended_actions: List[str] = []
    confidence: Optional[float] = None
    tags: List[str] = []


class NameplateField(BaseModel):
    """Single field extracted from an equipment nameplate.

    This is intended to be used inside NameplateTablePayload.fields and
    stored under schema_type="nameplate_table_v1" in AssetStructuredPayload.
    """

    key: str
    label: str
    value: Optional[Union[str, float]] = None
    unit: Optional[str] = None
    confidence: Optional[float] = None


class NameplateTablePayload(BaseModel):
    """Structured payload for LLM-extracted nameplate table information.

    Stored under schema_type="nameplate_table_v1" in AssetStructuredPayload.
    """

    equipment_type: Optional[str] = None
    fields: List[NameplateField] = []


class MeterReadingPayload(BaseModel):
    """Structured payload for LLM-extracted meter reading information.

    Stored under schema_type="meter_reading_v1" in AssetStructuredPayload.
    """

    pre_reading: Optional[float] = None
    reading: Optional[float] = None
    unit: Optional[str] = None
    status: Optional[str] = None
    summary: str
    confidence: Optional[float] = None
    tags: List[str] = []
