import uuid
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class BuildingBase(BaseModel):
    name: str
    usage_type: Optional[str] = None
    floor_area: Optional[float] = None
    year_built: Optional[float] = None
    energy_grade: Optional[str] = None
    tags: Optional[List[str]] = None


class BuildingCreate(BuildingBase):
    pass


class BuildingRead(BuildingBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID


class ZoneBase(BaseModel):
    name: str
    type: Optional[str] = None
    geometry_ref: Optional[str] = None
    tags: Optional[List[str]] = None


class ZoneCreate(ZoneBase):
    pass


class ZoneRead(ZoneBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    building_id: uuid.UUID


class SystemBase(BaseModel):
    type: str
    name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None


class SystemCreate(SystemBase):
    pass


class SystemRead(SystemBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    building_id: uuid.UUID


class DeviceBase(BaseModel):
    zone_id: Optional[uuid.UUID] = None
    device_type: Optional[str] = None
    model: Optional[str] = None
    rated_power: Optional[float] = None
    serial_no: Optional[str] = None
    tags: Optional[List[str]] = None


class DeviceCreate(DeviceBase):
    pass


class DeviceRead(DeviceBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    system_id: uuid.UUID
    zone_id: Optional[uuid.UUID] = None


class SystemSummary(BaseModel):
    id: uuid.UUID
    name: Optional[str] = None
    type: Optional[str] = None


class ZoneSummary(BaseModel):
    id: uuid.UUID
    name: Optional[str] = None


class DeviceFlatRead(DeviceRead):
    primary_system: Optional[SystemSummary] = None
    location: Optional[ZoneSummary] = None
    engineer_path: Optional[str] = None
