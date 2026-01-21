from typing import List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from shared.db.session import get_db
from shared.db.models_project import Building, Zone, BuildingSystem, Device
from shared.db.models_asset import Asset, FileBlob
from ...schemas.engineering import (
    BuildingCreate,
    BuildingRead,
    ZoneCreate,
    ZoneRead,
    SystemCreate,
    SystemRead,
    DeviceCreate,
    DeviceRead,
    DeviceFlatRead,
    SystemSummary,
    ZoneSummary,
)
from ...schemas.asset import AssetDetailRead
from ...services.tree_service import EngineeringTreeService

# Helper function for asset serialization


router = APIRouter()


def _populate_asset_file_paths(assets: List[Asset], db: Session) -> List[AssetDetailRead]:
    """Helper function to populate file_path for each asset."""
    result = []
    for asset in assets:
        detail = AssetDetailRead.model_validate(asset)
        if asset.file_id:
            file_blob = db.query(FileBlob).filter(FileBlob.id == asset.file_id).first()
            if file_blob:
                detail.file_path = file_blob.path
        result.append(detail)
    return result


@router.get(
    "/projects/{project_id}/buildings",
    response_model=List[BuildingRead],
    summary="List buildings for a project",
)
async def list_buildings_for_project(
    project_id: uuid.UUID,
    usage_type: Optional[str] = Query(default=None),
    energy_grade: Optional[str] = Query(default=None),
    name_contains: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
) -> List[BuildingRead]:
    query = db.query(Building).filter(Building.project_id == project_id)
    if usage_type is not None:
        query = query.filter(Building.usage_type == usage_type)
    if energy_grade is not None:
        query = query.filter(Building.energy_grade == energy_grade)
    if name_contains:
        pattern = f"%{name_contains}%"
        query = query.filter(Building.name.ilike(pattern))
    buildings = query.order_by(Building.name).all()
    return buildings


@router.post(
    "/projects/{project_id}/buildings",
    response_model=BuildingRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create building for a project",
)
async def create_building_for_project(
    project_id: uuid.UUID,
    payload: BuildingCreate,
    db: Session = Depends(get_db),
) -> BuildingRead:
    building = Building(project_id=project_id, **payload.model_dump())
    db.add(building)
    db.commit()
    db.refresh(building)
    return building


@router.get(
    "/buildings/{building_id}",
    response_model=BuildingRead,
    summary="Get building",
)
async def get_building(
    building_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> BuildingRead:
    building = db.query(Building).filter(Building.id == building_id).one_or_none()
    if building is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Building not found")
    return building


@router.patch(
    "/buildings/{building_id}",
    response_model=BuildingRead,
    summary="Update building",
)
async def update_building(
    building_id: uuid.UUID,
    payload: BuildingCreate,
    db: Session = Depends(get_db),
) -> BuildingRead:
    building = db.query(Building).filter(Building.id == building_id).one_or_none()
    if building is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Building not found")
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(building, field, value)
    db.commit()
    db.refresh(building)
    return building


@router.delete(
    "/buildings/{building_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete building",
)
async def delete_building(
    building_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> None:
    building = db.query(Building).filter(Building.id == building_id).one_or_none()
    if building is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Building not found")
    db.delete(building)
    db.commit()
    return None


@router.get(
    "/buildings/{building_id}/zones",
    response_model=List[ZoneRead],
    summary="List zones for a building",
)
async def list_zones_for_building(
    building_id: uuid.UUID,
    zone_type: Optional[str] = Query(default=None),
    name_contains: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
) -> List[ZoneRead]:
    query = db.query(Zone).filter(Zone.building_id == building_id)
    if zone_type is not None:
        query = query.filter(Zone.type == zone_type)
    if name_contains:
        pattern = f"%{name_contains}%"
        query = query.filter(Zone.name.ilike(pattern))
    zones = query.order_by(Zone.name).all()
    return zones


@router.post(
    "/buildings/{building_id}/zones",
    response_model=ZoneRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create zone for a building",
)
async def create_zone_for_building(
    building_id: uuid.UUID,
    payload: ZoneCreate,
    db: Session = Depends(get_db),
) -> ZoneRead:
    building = db.query(Building).filter(Building.id == building_id).one_or_none()
    if building is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Building not found")
    zone = Zone(building_id=building_id, **payload.model_dump())
    db.add(zone)
    db.commit()
    db.refresh(zone)
    return zone


@router.get(
    "/zones/{zone_id}",
    response_model=ZoneRead,
    summary="Get zone",
)
async def get_zone(
    zone_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> ZoneRead:
    zone = db.query(Zone).filter(Zone.id == zone_id).one_or_none()
    if zone is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Zone not found")
    return zone


@router.patch(
    "/zones/{zone_id}",
    response_model=ZoneRead,
    summary="Update zone",
)
async def update_zone(
    zone_id: uuid.UUID,
    payload: ZoneCreate,
    db: Session = Depends(get_db),
) -> ZoneRead:
    zone = db.query(Zone).filter(Zone.id == zone_id).one_or_none()
    if zone is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Zone not found")
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(zone, field, value)
    db.commit()
    db.refresh(zone)
    return zone


@router.delete(
    "/zones/{zone_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete zone",
)
async def delete_zone(
    zone_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> None:
    zone = db.query(Zone).filter(Zone.id == zone_id).one_or_none()
    if zone is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Zone not found")
    db.delete(zone)
    db.commit()
    return None


@router.get(
    "/buildings/{building_id}/systems",
    response_model=List[SystemRead],
    summary="List systems for a building",
)
async def list_systems_for_building(
    building_id: uuid.UUID,
    system_type: Optional[str] = Query(default=None),
    name_contains: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
) -> List[SystemRead]:
    query = db.query(BuildingSystem).filter(BuildingSystem.building_id == building_id)
    if system_type is not None:
        query = query.filter(BuildingSystem.type == system_type)
    if name_contains:
        pattern = f"%{name_contains}%"
        query = query.filter(BuildingSystem.name.ilike(pattern))
    systems = query.order_by(BuildingSystem.name).all()
    return systems


@router.post(
    "/buildings/{building_id}/systems",
    response_model=SystemRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create system for a building",
)
async def create_system_for_building(
    building_id: uuid.UUID,
    payload: SystemCreate,
    db: Session = Depends(get_db),
) -> SystemRead:
    building = db.query(Building).filter(Building.id == building_id).one_or_none()
    if building is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Building not found")
    system = BuildingSystem(building_id=building_id, **payload.model_dump())
    db.add(system)
    db.commit()
    db.refresh(system)
    return system


@router.get(
    "/systems/{system_id}",
    response_model=SystemRead,
    summary="Get system",
)
async def get_system(
    system_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> SystemRead:
    system = db.query(BuildingSystem).filter(BuildingSystem.id == system_id).one_or_none()
    if system is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="System not found")
    return system


@router.patch(
    "/systems/{system_id}",
    response_model=SystemRead,
    summary="Update system",
)
async def update_system(
    system_id: uuid.UUID,
    payload: SystemCreate,
    db: Session = Depends(get_db),
) -> SystemRead:
    system = db.query(BuildingSystem).filter(BuildingSystem.id == system_id).one_or_none()
    if system is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="System not found")
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(system, field, value)
    db.commit()
    db.refresh(system)
    return system


@router.delete(
    "/systems/{system_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete system",
)
async def delete_system(
    system_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> None:
    system = db.query(BuildingSystem).filter(BuildingSystem.id == system_id).one_or_none()
    if system is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="System not found")
    db.delete(system)
    db.commit()
    return None


@router.post(
    "/systems/{system_id}/devices",
    response_model=DeviceRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create device under a system",
)
async def create_device_for_system(
    system_id: uuid.UUID,
    payload: DeviceCreate,
    db: Session = Depends(get_db),
) -> DeviceRead:
    system = db.query(BuildingSystem).filter(BuildingSystem.id == system_id).one_or_none()
    if system is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="System not found")

    zone_id = payload.zone_id
    if zone_id is not None:
        zone = db.query(Zone).filter(Zone.id == zone_id).one_or_none()
        if zone is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Zone not found")
        if zone.building_id != system.building_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Zone and System must belong to the same Building",
            )

    device = Device(system_id=system_id, **payload.model_dump())
    db.add(device)
    db.commit()
    db.refresh(device)
    return device


@router.get(
    "/systems/{system_id}/devices",
    response_model=List[DeviceRead],
    summary="List devices for a system",
)
async def list_devices_for_system(
    system_id: uuid.UUID,
    device_type: Optional[str] = Query(default=None),
    zone_id: Optional[uuid.UUID] = Query(default=None),
    db: Session = Depends(get_db),
) -> List[DeviceRead]:
    query = db.query(Device).filter(Device.system_id == system_id)
    if device_type is not None:
        query = query.filter(Device.device_type == device_type)
    if zone_id is not None:
        query = query.filter(Device.zone_id == zone_id)
    devices = query.order_by(Device.model).all()
    return devices


@router.get(
    "/projects/{project_id}/devices/flat",
    response_model=List[DeviceFlatRead],
    summary="Flat device list for a project with filters",
)
async def list_devices_flat_for_project(
    project_id: uuid.UUID,
    system_id: Optional[uuid.UUID] = Query(default=None),
    zone_id: Optional[uuid.UUID] = Query(default=None),
    device_type: Optional[str] = Query(default=None),
    min_rated_power: Optional[float] = Query(default=None),
    tags: Optional[str] = Query(default=None, description="Comma-separated tags, AND semantics"),
    search: Optional[str] = Query(default=None, description="Search in model or serial_no"),
    db: Session = Depends(get_db),
) -> List[DeviceFlatRead]:
    query = (
        db.query(Device)
        .join(BuildingSystem, Device.system_id == BuildingSystem.id)
        .join(Building, BuildingSystem.building_id == Building.id)
        .options(joinedload(Device.system), joinedload(Device.zone))
        .filter(Building.project_id == project_id)
    )

    if system_id is not None:
        query = query.filter(Device.system_id == system_id)
    if zone_id is not None:
        query = query.filter(Device.zone_id == zone_id)
    if device_type is not None:
        query = query.filter(Device.device_type == device_type)
    if min_rated_power is not None:
        query = query.filter(Device.rated_power >= min_rated_power)
    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        if tag_list:
            query = query.filter(Device.tags.contains(tag_list))
    if search:
        pattern = f"%{search}%"
        query = query.filter((Device.model.ilike(pattern)) | (Device.serial_no.ilike(pattern)))

    devices = query.order_by(Device.model).all()

    results: List[DeviceFlatRead] = []
    for dev in devices:
        primary_system = None
        if dev.system is not None:
            primary_system = SystemSummary(id=dev.system.id, name=dev.system.name, type=dev.system.type)

        location = None
        if dev.zone is not None:
            location = ZoneSummary(id=dev.zone.id, name=dev.zone.name)

        engineer_parts = []
        building = dev.system.building if dev.system is not None else None
        if building is not None:
            engineer_parts.append(building.name)
        if dev.system is not None:
            engineer_parts.append(dev.system.name or dev.system.type)
        if dev.model or dev.device_type:
            engineer_parts.append(dev.model or dev.device_type)
        engineer_path = " / ".join(engineer_parts) if engineer_parts else None

        flat = DeviceFlatRead(
            id=dev.id,
            system_id=dev.system_id,
            zone_id=dev.zone_id,
            device_type=dev.device_type,
            model=dev.model,
            rated_power=dev.rated_power,
            serial_no=dev.serial_no,
            tags=dev.tags,
            primary_system=primary_system,
            location=location,
            engineer_path=engineer_path,
        )
        results.append(flat)

    return results


@router.get(
    "/projects/{project_id}/structure_tree",
    summary="Get engineering structure tree for a project",
)
async def get_project_structure_tree(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> dict:
    root = EngineeringTreeService.build_project_tree(project_id, db)
    return {
        "project_id": str(project_id),
        "tree": EngineeringTreeService.tree_to_dict(root),
    }


@router.get(
    "/zones/{zone_id}/devices",
    response_model=List[DeviceRead],
    summary="List devices for a zone (read-only view)",
)
async def list_devices_for_zone(
    zone_id: uuid.UUID,
    device_type: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
) -> List[DeviceRead]:
    query = db.query(Device).filter(Device.zone_id == zone_id)
    if device_type is not None:
        query = query.filter(Device.device_type == device_type)
    devices = query.order_by(Device.model).all()
    return devices


@router.get(
    "/devices/{device_id}",
    response_model=DeviceRead,
    summary="Get device",
)
async def get_device(
    device_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> DeviceRead:
    device = db.query(Device).filter(Device.id == device_id).one_or_none()
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    return device


@router.patch(
    "/devices/{device_id}",
    response_model=DeviceRead,
    summary="Update device",
)
async def update_device(
    device_id: uuid.UUID,
    payload: DeviceCreate,
    db: Session = Depends(get_db),
) -> DeviceRead:
    device = db.query(Device).filter(Device.id == device_id).one_or_none()
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    update_data = payload.model_dump(exclude_unset=True)
    zone_id = update_data.get("zone_id")
    if zone_id is not None:
        zone = db.query(Zone).filter(Zone.id == zone_id).one_or_none()
        if zone is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Zone not found")
        system = db.query(BuildingSystem).filter(BuildingSystem.id == device.system_id).one()
        if zone.building_id != system.building_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Zone and System must belong to the same Building",
            )

    for field, value in update_data.items():
        setattr(device, field, value)
    db.commit()
    db.refresh(device)
    return device


@router.delete(
    "/devices/{device_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete device",
)
async def delete_device(
    device_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> None:
    device = db.query(Device).filter(Device.id == device_id).one_or_none()
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    db.delete(device)
    db.commit()
    return None


@router.get(
    "/devices/{device_id}/assets",
    response_model=List[AssetDetailRead],
    summary="List assets for a device",
)
async def list_assets_for_device(
    device_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> List[AssetDetailRead]:
    assets = (
        db.query(Asset)
        .filter(Asset.device_id == device_id)
        .order_by(Asset.capture_time.desc().nullslast())
        .all()
    )
    return _populate_asset_file_paths(assets, db)


@router.get(
    "/systems/{system_id}/assets",
    response_model=List[AssetDetailRead],
    summary="List assets for a system",
)
async def list_assets_for_system(
    system_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> List[AssetDetailRead]:
    assets = (
        db.query(Asset)
        .filter(Asset.system_id == system_id)
        .order_by(Asset.capture_time.desc().nullslast())
        .all()
    )
    return _populate_asset_file_paths(assets, db)


@router.get(
    "/zones/{zone_id}/assets",
    response_model=List[AssetDetailRead],
    summary="List assets for a zone",
)
async def list_assets_for_zone(
    zone_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> List[AssetDetailRead]:
    assets = (
        db.query(Asset)
        .filter(Asset.zone_id == zone_id)
        .order_by(Asset.capture_time.desc().nullslast())
        .all()
    )
    return _populate_asset_file_paths(assets, db)


@router.get(
    "/buildings/{building_id}/assets",
    response_model=List[AssetDetailRead],
    summary="List assets for a building",
)
async def list_assets_for_building(
    building_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> List[AssetDetailRead]:
    assets = (
        db.query(Asset)
        .filter(Asset.building_id == building_id)
        .order_by(Asset.capture_time.desc().nullslast())
        .all()
    )
    return _populate_asset_file_paths(assets, db)
