import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

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


class AssetStructuredPayloadRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    schema_type: str
    payload: Dict[str, Any]
    version: float
    created_by: Optional[str] = None
    created_at: datetime


class AssetDetailRead(AssetRead):
    structured_payloads: List[AssetStructuredPayloadRead] = []
