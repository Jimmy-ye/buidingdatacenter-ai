from typing import List, Optional
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request, status
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from shared.db.session import get_db
from shared.db.models_project import Project, Building, Zone, BuildingSystem, Device
from ...schemas.project import ProjectCreate, ProjectUpdate, ProjectRead
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
from ...services.tree_service import EngineeringTreeService


DEFAULT_BUILDING_SYSTEM_NAMES = [
    "围护结构",
    "制冷",
    "制热",
    "空调末端",
    "照明",
    "电梯",
    "动力",
    "电力监控",
    "能管平台",
]

AUTO_CREATE_DEFAULT_SYSTEMS = True


router = APIRouter()


# ---------------------------------------------------------------------------
# Project endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/projects/",
    response_model=List[ProjectRead],
    summary="List all active projects",
)
async def list_projects(
    db: Session = Depends(get_db),
) -> List[Project]:
    """Return all non-deleted projects ordered by name."""
    return (
        db.query(Project)
        .filter(Project.is_deleted.is_(False))
        .order_by(Project.name)
        .all()
    )


@router.post(
    "/projects/",
    response_model=ProjectRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create project",
)
async def create_project(
    payload: ProjectCreate,
    db: Session = Depends(get_db),
) -> Project:
    """Create a new project."""
    data = payload.model_dump()
    project = Project(**data)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.patch(
    "/projects/{project_id}",
    response_model=ProjectRead,
    summary="Update project",
)
async def update_project(
    project_id: uuid.UUID = Path(..., description="Project ID"),
    payload: ProjectUpdate = ...,  # type: ignore[assignment]
    db: Session = Depends(get_db),
) -> Project:
    project = db.query(Project).filter(Project.id == project_id, Project.is_deleted.is_(False)).one_or_none()
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)

    db.commit()
    db.refresh(project)
    return project


@router.delete(
    "/projects/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete project",
)
async def delete_project(
    request: Request,
    project_id: uuid.UUID = Path(..., description="Project ID"),
    reason: Optional[str] = Query(None, description="Reason for deletion"),
    db: Session = Depends(get_db),
) -> None:
    """Soft delete a project and cascade delete its children via ORM relations.

    The record is kept with is_deleted=True and deleted_* metadata set, so
    historical references can still resolve the project.
    """

    project = db.query(Project).filter(Project.id == project_id, Project.is_deleted.is_(False)).one_or_none()
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    operator = request.headers.get("operator")
    project.is_deleted = True
    project.deleted_at = datetime.utcnow()
    project.deleted_by = operator
    project.deletion_reason = reason

    db.commit()
    return None


# ---------------------------------------------------------------------------
# Project structure tree endpoint
# ---------------------------------------------------------------------------


@router.get(
    "/projects/{project_id}/structure_tree",
    summary="Get engineering structure tree for a project",
)
async def get_project_structure_tree(
    project_id: uuid.UUID = Path(..., description="Project ID"),
    db: Session = Depends(get_db),
) -> dict:
    """Return the engineering structure tree for a project.

    This is used by the PC UI to render the left-hand engineering tree.
    """

    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.is_deleted.is_(False))
        .one_or_none()
    )
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    root = EngineeringTreeService.build_project_tree(project_id, db)
    tree_dict = EngineeringTreeService.tree_to_dict(root)
    return tree_dict


# ---------------------------------------------------------------------------
# Building endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/projects/{project_id}/buildings",
    response_model=List[BuildingRead],
    summary="List buildings for a project",
)
async def list_buildings_for_project(
    project_id: uuid.UUID = Path(..., description="Project ID"),
    usage_type: Optional[str] = Query(None, description="Filter by building usage_type"),
    name_contains: Optional[str] = Query(None, description="Case-insensitive name contains filter"),
    tags: Optional[str] = Query(
        None,
        description="Comma separated tags, AND semantics (building.tags contains all)",
    ),
    db: Session = Depends(get_db),
) -> List[Building]:
    query = db.query(Building).filter(Building.project_id == project_id)

    if usage_type is not None:
        query = query.filter(Building.usage_type == usage_type)
    if name_contains:
        like = f"%{name_contains}%"
        query = query.filter(Building.name.ilike(like))
    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        if tag_list:
            query = query.filter(Building.tags.contains(tag_list))

    return query.order_by(Building.name).all()


@router.post(
    "/projects/{project_id}/buildings",
    response_model=BuildingRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create building under a project",
)
async def create_building_for_project(
    project_id: uuid.UUID = Path(..., description="Project ID"),
    payload: BuildingCreate = ...,  # type: ignore[assignment]
    db: Session = Depends(get_db),
) -> Building:
    # Ensure project exists
    project = db.query(Project).filter(Project.id == project_id).one_or_none()
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    data = payload.model_dump()
    building = Building(project_id=project_id, **data)
    db.add(building)
    db.flush()

    if AUTO_CREATE_DEFAULT_SYSTEMS:
        systems = [
            BuildingSystem(building_id=building.id, type=name, name=name)
            for name in DEFAULT_BUILDING_SYSTEM_NAMES
        ]
        db.add_all(systems)

    db.commit()
    db.refresh(building)
    return building


@router.get(
    "/buildings/{building_id}",
    response_model=BuildingRead,
    summary="Get single building",
)
async def get_building(
    building_id: uuid.UUID = Path(..., description="Building ID"),
    db: Session = Depends(get_db),
) -> Building:
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
    building_id: uuid.UUID = Path(..., description="Building ID"),
    payload: BuildingCreate = ...,  # require full payload for now
    db: Session = Depends(get_db),
) -> Building:
    building = db.query(Building).filter(Building.id == building_id).one_or_none()
    if building is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Building not found")

    update_data = payload.model_dump()
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
    building_id: uuid.UUID = Path(..., description="Building ID"),
    db: Session = Depends(get_db),
) -> None:
    building = db.query(Building).filter(Building.id == building_id).one_or_none()
    if building is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Building not found")

    db.delete(building)
    db.commit()
    return None


# ---------------------------------------------------------------------------
# Zone endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/buildings/{building_id}/zones",
    response_model=List[ZoneRead],
    summary="List zones under a building",
)
async def list_zones_for_building(
    building_id: uuid.UUID = Path(..., description="Building ID"),
    zone_type: Optional[str] = Query(None, description="Filter by zone type"),
    name_contains: Optional[str] = Query(None, description="Case-insensitive name contains"),
    tags: Optional[str] = Query(None, description="Comma separated tags, AND semantics"),
    db: Session = Depends(get_db),
) -> List[Zone]:
    query = db.query(Zone).filter(Zone.building_id == building_id)

    if zone_type is not None:
        query = query.filter(Zone.type == zone_type)
    if name_contains:
        like = f"%{name_contains}%"
        query = query.filter(Zone.name.ilike(like))
    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        if tag_list:
            query = query.filter(Zone.tags.contains(tag_list))

    return query.order_by(Zone.name).all()


@router.post(
    "/buildings/{building_id}/zones",
    response_model=ZoneRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create zone under a building",
)
async def create_zone_for_building(
    building_id: uuid.UUID = Path(..., description="Building ID"),
    payload: ZoneCreate = ...,  # type: ignore[assignment]
    db: Session = Depends(get_db),
) -> Zone:
    building = db.query(Building).filter(Building.id == building_id).one_or_none()
    if building is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Building not found")

    data = payload.model_dump()
    zone = Zone(building_id=building_id, **data)
    db.add(zone)
    db.commit()
    db.refresh(zone)
    return zone


@router.get(
    "/zones/{zone_id}",
    response_model=ZoneRead,
    summary="Get single zone",
)
async def get_zone(
    zone_id: uuid.UUID = Path(..., description="Zone ID"),
    db: Session = Depends(get_db),
) -> Zone:
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
    zone_id: uuid.UUID = Path(..., description="Zone ID"),
    payload: ZoneCreate = ...,  # require full payload for now
    db: Session = Depends(get_db),
) -> Zone:
    zone = db.query(Zone).filter(Zone.id == zone_id).one_or_none()
    if zone is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Zone not found")

    update_data = payload.model_dump()
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
    zone_id: uuid.UUID = Path(..., description="Zone ID"),
    db: Session = Depends(get_db),
) -> None:
    zone = db.query(Zone).filter(Zone.id == zone_id).one_or_none()
    if zone is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Zone not found")

    db.delete(zone)
    db.commit()
    return None


@router.get(
    "/zones/{zone_id}/devices",
    response_model=List[DeviceRead],
    summary="List devices located in a zone (read-only view)",
)
async def list_devices_for_zone(
    zone_id: uuid.UUID = Path(..., description="Zone ID"),
    db: Session = Depends(get_db),
) -> List[Device]:
    return db.query(Device).filter(Device.zone_id == zone_id).all()


# ---------------------------------------------------------------------------
# System endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/buildings/{building_id}/systems",
    response_model=List[SystemRead],
    summary="List systems under a building",
)
async def list_systems_for_building(
    building_id: uuid.UUID = Path(..., description="Building ID"),
    system_type: Optional[str] = Query(None, description="Filter by system type"),
    name_contains: Optional[str] = Query(None, description="Case-insensitive name contains"),
    tags: Optional[str] = Query(None, description="Comma separated tags, AND semantics"),
    db: Session = Depends(get_db),
) -> List[BuildingSystem]:
    query = db.query(BuildingSystem).filter(BuildingSystem.building_id == building_id)

    if system_type is not None:
        query = query.filter(BuildingSystem.type == system_type)
    if name_contains:
        like = f"%{name_contains}%"
        query = query.filter(BuildingSystem.name.ilike(like))
    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        if tag_list:
            query = query.filter(BuildingSystem.tags.contains(tag_list))

    return query.order_by(BuildingSystem.name).all()


@router.post(
    "/buildings/{building_id}/systems",
    response_model=SystemRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create system under a building",
)
async def create_system_for_building(
    building_id: uuid.UUID = Path(..., description="Building ID"),
    payload: SystemCreate = ...,  # type: ignore[assignment]
    db: Session = Depends(get_db),
) -> BuildingSystem:
    building = db.query(Building).filter(Building.id == building_id).one_or_none()
    if building is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Building not found")

    data = payload.model_dump()
    system = BuildingSystem(building_id=building_id, **data)
    db.add(system)
    db.commit()
    db.refresh(system)
    return system


@router.get(
    "/systems/{system_id}",
    response_model=SystemRead,
    summary="Get single system",
)
async def get_system(
    system_id: uuid.UUID = Path(..., description="System ID"),
    db: Session = Depends(get_db),
) -> BuildingSystem:
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
    system_id: uuid.UUID = Path(..., description="System ID"),
    payload: SystemCreate = ...,  # require full payload for now
    db: Session = Depends(get_db),
) -> BuildingSystem:
    system = db.query(BuildingSystem).filter(BuildingSystem.id == system_id).one_or_none()
    if system is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="System not found")

    update_data = payload.model_dump()
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
    system_id: uuid.UUID = Path(..., description="System ID"),
    db: Session = Depends(get_db),
) -> None:
    system = db.query(BuildingSystem).filter(BuildingSystem.id == system_id).one_or_none()
    if system is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="System not found")

    db.delete(system)
    db.commit()
    return None


@router.get(
    "/systems/{system_id}/devices",
    response_model=List[DeviceRead],
    summary="List devices under a system",
)
async def list_devices_for_system(
    system_id: uuid.UUID = Path(..., description="System ID"),
    device_type: Optional[str] = Query(None, description="Filter by device_type"),
    tags: Optional[str] = Query(None, description="Comma separated tags, AND semantics"),
    zone_id: Optional[uuid.UUID] = Query(None, description="Filter by zone_id"),
    db: Session = Depends(get_db),
) -> List[Device]:
    query = db.query(Device).filter(Device.system_id == system_id)

    if device_type is not None:
        query = query.filter(Device.device_type == device_type)
    if zone_id is not None:
        query = query.filter(Device.zone_id == zone_id)
    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        if tag_list:
            query = query.filter(Device.tags.contains(tag_list))

    return query.all()


@router.post(
    "/systems/{system_id}/devices",
    response_model=DeviceRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create device under a system (primary ownership)",
)
async def create_device_for_system(
    system_id: uuid.UUID = Path(..., description="System ID"),
    payload: DeviceCreate = ...,  # type: ignore[assignment]
    db: Session = Depends(get_db),
) -> Device:
    system = db.query(BuildingSystem).filter(BuildingSystem.id == system_id).one_or_none()
    if system is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="System not found")

    data = payload.model_dump()
    zone_id = data.get("zone_id")

    # If zone_id is provided, ensure it belongs to the same building as the system
    if zone_id is not None:
        zone = db.query(Zone).filter(Zone.id == zone_id).one_or_none()
        if zone is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Zone not found")
        if zone.building_id != system.building_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Zone and System must belong to the same Building",
            )

    device = Device(system_id=system_id, **data)
    db.add(device)
    db.commit()
    db.refresh(device)
    return device


# ---------------------------------------------------------------------------
# Device endpoints (single / flat view)
# ---------------------------------------------------------------------------


@router.get(
    "/devices/{device_id}",
    response_model=DeviceRead,
    summary="Get single device",
)
async def get_device(
    device_id: uuid.UUID = Path(..., description="Device ID"),
    db: Session = Depends(get_db),
) -> Device:
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
    device_id: uuid.UUID = Path(..., description="Device ID"),
    payload: DeviceCreate = ...,  # require full payload for now
    db: Session = Depends(get_db),
) -> Device:
    device = db.query(Device).filter(Device.id == device_id).one_or_none()
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    data = payload.model_dump()
    zone_id = data.get("zone_id")

    # If zone_id is provided, validate building consistency (same as create)
    if zone_id is not None and device.system_id is not None:
        system = db.query(BuildingSystem).filter(BuildingSystem.id == device.system_id).one_or_none()
        zone = db.query(Zone).filter(Zone.id == zone_id).one_or_none()
        if system is None or zone is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid system or zone")
        if zone.building_id != system.building_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Zone and System must belong to the same Building",
            )

    for field, value in data.items():
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
    device_id: uuid.UUID = Path(..., description="Device ID"),
    db: Session = Depends(get_db),
) -> None:
    device = db.query(Device).filter(Device.id == device_id).one_or_none()
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    db.delete(device)
    db.commit()
    return None


@router.get(
    "/projects/{project_id}/devices/flat",
    response_model=List[DeviceFlatRead],
    summary="Flat device view for a project",
)
async def list_devices_flat_for_project(
    project_id: uuid.UUID = Path(..., description="Project ID"),
    system_id: Optional[uuid.UUID] = Query(None, description="Filter by system_id"),
    zone_id: Optional[uuid.UUID] = Query(None, description="Filter by zone_id"),
    device_type: Optional[str] = Query(None, description="Filter by device_type"),
    min_rated_power: Optional[float] = Query(None, description="Filter by minimum rated_power"),
    tags: Optional[str] = Query(None, description="Comma separated tags, AND semantics"),
    search: Optional[str] = Query(None, description="Search in model/serial_no"),
    db: Session = Depends(get_db),
) -> List[DeviceFlatRead]:
    # Join Device -> System -> Building, and optional Zone
    query = (
        db.query(Device, BuildingSystem, Building, Zone)
        .join(BuildingSystem, Device.system_id == BuildingSystem.id)
        .join(Building, BuildingSystem.building_id == Building.id)
        .outerjoin(Zone, Device.zone_id == Zone.id)
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
        like = f"%{search}%"
        query = query.filter(or_(Device.model.ilike(like), Device.serial_no.ilike(like)))

    rows = query.all()
    result: List[DeviceFlatRead] = []
    for device, system, building, zone in rows:
        # Normalise tags to list[str] if stored as JSON array
        tags_value = device.tags
        tags_list: Optional[List[str]] = None
        if isinstance(tags_value, list):
            tags_list = [str(t) for t in tags_value]

        primary_system = None
        if system is not None:
            primary_system = SystemSummary(id=system.id, name=system.name, type=system.type)

        location_summary = None
        if zone is not None:
            location_summary = ZoneSummary(id=zone.id, name=zone.name)

        # Engineer path: Building / System / Device
        parts: List[str] = []
        if building is not None and building.name:
            parts.append(building.name)
        if system is not None:
            parts.append(system.name or system.type or "System")
        if device.model:
            parts.append(device.model)
        elif device.device_type:
            parts.append(device.device_type)
        engineer_path = " / ".join(parts) if parts else None

        item = DeviceFlatRead(
            id=device.id,
            system_id=device.system_id,
            zone_id=device.zone_id,
            device_type=device.device_type,
            model=device.model,
            rated_power=device.rated_power,
            serial_no=device.serial_no,
            tags=tags_list,
            primary_system=primary_system,
            location=location_summary,
            engineer_path=engineer_path,
        )
        result.append(item)

    return result
