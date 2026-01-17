from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class FileBlobCreate(BaseModel):
    storage_type: str = "minio"
    bucket: str
    path: str
    file_name: str
    content_type: Optional[str] = None
    size: Optional[float] = None
    hash: Optional[str] = None


class AssetBase(BaseModel):
    project_id: str
    building_id: Optional[str] = None
    zone_id: Optional[str] = None
    system_id: Optional[str] = None
    device_id: Optional[str] = None

    modality: str
    source: str
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
    id: str
    file_id: str

    class Config:
        from_attributes = True
