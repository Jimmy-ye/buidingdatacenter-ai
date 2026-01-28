from typing import List, Optional
import os
import uuid
from datetime import datetime

from fastapi import APIRouter, Body, Depends, File, Form, HTTPException, Path, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from shared.config.settings import get_settings
from shared.db.models_asset import Asset, AssetStructuredPayload, FileBlob
from shared.db.models_project import Building, Zone, BuildingSystem, Device
from shared.db.session import get_db
from ...schemas.asset import (
    AssetCreate,
    AssetRead,
    AssetDetailRead,
    SceneIssueReportPayload,
    NameplateTablePayload,
    MeterReadingPayload,
)
from ...services.image_pipeline import process_image_with_ocr, route_image_asset


router = APIRouter()
settings = get_settings()


def _resolve_engineering_hierarchy(
    db: Session,
    project_id: uuid.UUID,
    building_id: Optional[uuid.UUID] = None,
    zone_id: Optional[uuid.UUID] = None,
    system_id: Optional[uuid.UUID] = None,
    device_id: Optional[uuid.UUID] = None,
):
    """Validate Building/Zone/System/Device chain and build a human-readable path.

    This does not modify the database, it only:
    - Ensures all referenced entities exist
    - Ensures they are consistent and belong to the given project
    - Returns the resolved objects and a display path
    """

    building: Optional[Building] = None
    zone: Optional[Zone] = None
    system: Optional[BuildingSystem] = None
    device: Optional[Device] = None

    # Building
    if building_id is not None:
        building = db.query(Building).filter_by(id=building_id).one_or_none()
        if building is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Building not found")
        if building.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Building does not belong to the given project",
            )

    # Zone
    if zone_id is not None:
        zone = db.query(Zone).filter_by(id=zone_id).one_or_none()
        if zone is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Zone not found")

        if building is not None and zone.building_id != building.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Zone does not belong to the given building",
            )

        if building is None:
            building = db.query(Building).filter_by(id=zone.building_id).one_or_none()
            if building is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Zone refers to a missing building",
                )

        if building.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Zone's building does not belong to the given project",
            )

    # System
    if system_id is not None:
        system = db.query(BuildingSystem).filter_by(id=system_id).one_or_none()
        if system is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="System not found")

        if building is not None and system.building_id != building.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="System does not belong to the given building",
            )

        if building is None:
            building = db.query(Building).filter_by(id=system.building_id).one_or_none()
            if building is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="System refers to a missing building",
                )

        if building.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="System's building does not belong to the given project",
            )

    # Device
    if device_id is not None:
        device = db.query(Device).filter_by(id=device_id).one_or_none()
        if device is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Device not found")

        # Validate against provided system
        if system is not None and device.system_id != system.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Device does not belong to the given system",
            )

        # If no system provided but device has one, adopt it
        if system is None and device.system_id is not None:
            system = db.query(BuildingSystem).filter_by(id=device.system_id).one_or_none()
            if system is not None:
                if building is not None and system.building_id != building.id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Device's system building does not match the given building",
                    )
                if building is None:
                    building = db.query(Building).filter_by(id=system.building_id).one_or_none()

        # Validate against provided zone
        if zone is not None and device.zone_id != zone.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Device does not belong to the given zone",
            )

        # If no zone provided but device has one, adopt it
        if zone is None and device.zone_id is not None:
            zone = db.query(Zone).filter_by(id=device.zone_id).one_or_none()
            if zone is not None:
                if building is not None and zone.building_id != building.id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Device's zone building does not match the given building",
                    )
                if building is None:
                    building = db.query(Building).filter_by(id=zone.building_id).one_or_none()

        if building is not None and building.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Device's building does not belong to the given project",
            )

        # Optional strict rule: device must belong to a system
        if system is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Device must belong to a System",
            )

    # Build path string
    parts = []
    if building is not None:
        parts.append(building.name or "Building")
    if zone is not None:
        parts.append(zone.name or "Zone")
    if system is not None:
        parts.append(system.name or system.type or "System")
    if device is not None:
        label = device.model or device.device_type or "Device"
        parts.append(label)

    path = " / ".join(parts) if parts else None

    return {
        "building": building,
        "zone": zone,
        "system": system,
        "device": device,
        "path": path,
    }


@router.get("/", response_model=List[AssetRead], summary="List assets")
async def list_assets(
    project_id: Optional[uuid.UUID] = Query(default=None, description="Filter by project ID"),
    modality: Optional[str] = Query(default=None, description="Filter by modality, e.g. image, table"),
    content_role: Optional[str] = Query(default=None, description="Filter by high-level content role"),
    building_id: Optional[uuid.UUID] = Query(default=None, description="Filter by building ID"),
    zone_id: Optional[uuid.UUID] = Query(default=None, description="Filter by zone ID"),
    system_id: Optional[uuid.UUID] = Query(default=None, description="Filter by system ID"),
    device_id: Optional[uuid.UUID] = Query(default=None, description="Filter by device ID"),
    updated_after: Optional[datetime] = Query(
        default=None,
        description="Return only assets with capture_time later than this UTC timestamp (incremental sync)",
    ),
    db: Session = Depends(get_db),
) -> List[AssetRead]:
    """List assets with optional multi-dimensional and incremental-sync filters.

    Supports filtering by:
    - project
    - modality / content_role
    - building / zone / system / device
    - updated_after (for incremental sync based on capture_time)
    """

    query = db.query(Asset)
    if project_id is not None:
        query = query.filter(Asset.project_id == project_id)
    if modality is not None:
        query = query.filter(Asset.modality == modality)
    if content_role is not None:
        query = query.filter(Asset.content_role == content_role)
    if building_id is not None:
        query = query.filter(Asset.building_id == building_id)
    if zone_id is not None:
        query = query.filter(Asset.zone_id == zone_id)
    if system_id is not None:
        query = query.filter(Asset.system_id == system_id)
    if device_id is not None:
        query = query.filter(Asset.device_id == device_id)
    if updated_after is not None:
        query = query.filter(Asset.capture_time > updated_after)

    assets = query.order_by(Asset.capture_time.desc().nullslast()).all()
    return assets


@router.get(
    "/{asset_id}",
    response_model=AssetDetailRead,
    summary="Get asset with structured payloads",
)
async def get_asset(
    asset_id: uuid.UUID = Path(..., description="Asset ID"),
    db: Session = Depends(get_db),
) -> AssetDetailRead:
    from shared.db.models_asset import FileBlob

    # Convert UUID to string for SQLite compatibility
    asset_id_str = str(asset_id)

    asset = db.query(Asset).filter(Asset.id == asset_id_str).one_or_none()
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")

    detail = AssetDetailRead.model_validate(asset)

    # Manually query file_blob to avoid SQLAlchemy relationship issues with SQLite
    if asset.file_id:
        file_blob = db.query(FileBlob).filter(FileBlob.id == str(asset.file_id)).one_or_none()
        if file_blob is not None:
            detail.file_path = file_blob.path

    return detail


@router.get(
    "/{asset_id}/download",
    summary="Download raw asset file by ID",
)
async def download_asset_file(
    asset_id: uuid.UUID = Path(..., description="Asset ID"),
    db: Session = Depends(get_db),
):
    """Serve the underlying file for an asset.

    This endpoint abstracts away the storage backend (local disk, NAS, object storage, etc.)
    and provides a stable HTTP URL for frontends like mobile and PC UI to fetch the file.
    """

    # Convert UUID to string for SQLite compatibility
    asset_id_str = str(asset_id)

    asset = db.query(Asset).filter(Asset.id == asset_id_str).one_or_none()
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")

    if asset.file_id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset has no associated file")

    file_blob = db.query(FileBlob).filter(FileBlob.id == str(asset.file_id)).one_or_none()
    if file_blob is None or not file_blob.path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File blob not found for asset")

    base_dir = settings.local_storage_dir
    abs_path = os.path.join(base_dir, file_blob.path)

    if not os.path.exists(abs_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found on disk")

    filename = os.path.basename(file_blob.path) or file_blob.file_name or str(asset.id)
    media_type = file_blob.content_type or "application/octet-stream"

    return FileResponse(
        abs_path,
        filename=filename,
        media_type=media_type,
    )


@router.post(
    "/{asset_id}/scene_issue_report",
    response_model=AssetDetailRead,
    summary="Attach an LLM-based scene issue report to a scene_issue image asset",
)
async def create_scene_issue_report(
    asset_id: uuid.UUID = Path(..., description="Asset ID"),
    report: SceneIssueReportPayload = Body(..., description="LLM-generated scene issue report payload"),
    db: Session = Depends(get_db),
) -> AssetDetailRead:
    asset = db.query(Asset).filter(Asset.id == asset_id).one_or_none()
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")

    # Enforce that this endpoint is only used for image assets with supported roles
    role = (asset.content_role or "").lower()
    if asset.modality != "image" or role not in {"scene_issue", "meter"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "scene_issue_report is only valid for image assets with "
                "content_role in {'scene_issue', 'meter'}"
            ),
        )

    existing_count = (
        db.query(AssetStructuredPayload)
        .filter(AssetStructuredPayload.asset_id == asset.id)
        .count()
    )

    structured = AssetStructuredPayload(
        asset_id=asset.id,
        schema_type="scene_issue_report_v1",
        payload=report.model_dump(),
        version=float(existing_count + 1),
        created_by="llm",
    )
    db.add(structured)

    asset.status = "parsed_scene_llm"
    db.commit()
    db.refresh(asset)
    return asset


@router.post(
    "/{asset_id}/nameplate_table",
    response_model=AssetDetailRead,
    summary="Attach an LLM-extracted nameplate table payload to a nameplate image asset",
)
async def create_nameplate_table_payload(
    asset_id: uuid.UUID = Path(..., description="Asset ID"),
    payload: NameplateTablePayload = Body(..., description="LLM-generated nameplate table payload"),
    db: Session = Depends(get_db),
) -> AssetDetailRead:
    asset = db.query(Asset).filter(Asset.id == asset_id).one_or_none()
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")

    role = (asset.content_role or "").lower()
    if asset.modality != "image" or role != "nameplate":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="nameplate_table is only valid for image assets with content_role='nameplate'",
        )

    existing_count = (
        db.query(AssetStructuredPayload)
        .filter(AssetStructuredPayload.asset_id == asset.id)
        .count()
    )

    structured = AssetStructuredPayload(
        asset_id=asset.id,
        schema_type="nameplate_table_v1",
        payload=payload.model_dump(),
        version=float(existing_count + 1),
        created_by="llm",
    )
    db.add(structured)

    asset.status = "parsed_nameplate_llm"
    db.commit()
    db.refresh(asset)
    return asset


@router.post(
    "/{asset_id}/meter_reading",
    response_model=AssetDetailRead,
    summary="Attach an LLM-extracted meter reading payload to a meter image asset",
)
async def create_meter_reading_payload(
    asset_id: uuid.UUID = Path(..., description="Asset ID"),
    payload: MeterReadingPayload = Body(..., description="LLM-generated meter reading payload"),
    db: Session = Depends(get_db),
) -> AssetDetailRead:
    asset = db.query(Asset).filter(Asset.id == asset_id).one_or_none()
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")

    role = (asset.content_role or "").lower()
    if asset.modality != "image" or role != "meter":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="meter_reading is only valid for image assets with content_role='meter'",
        )

    existing_count = (
        db.query(AssetStructuredPayload)
        .filter(AssetStructuredPayload.asset_id == asset.id)
        .count()
    )

    structured = AssetStructuredPayload(
        asset_id=asset.id,
        schema_type="meter_reading_v1",
        payload=payload.model_dump(),
        version=float(existing_count + 1),
        created_by="llm",
    )
    db.add(structured)

    asset.status = "parsed_meter_llm"
    db.commit()
    db.refresh(asset)
    return asset


@router.post(
    "/",
    response_model=AssetRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create asset with file metadata",
)
async def create_asset(
    payload: AssetCreate,
    db: Session = Depends(get_db),
) -> AssetRead:
    data = payload.model_dump()
    file_data = data.pop("file")

    file_blob = FileBlob(**file_data)
    db.add(file_blob)
    db.flush()

    asset = Asset(**data, file_id=file_blob.id)
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


@router.post(
    "/{asset_id}/route_image",
    response_model=AssetRead,
    summary="Route an image asset to OCR or scene-LLM pipeline based on content_role",
)
async def route_image_asset_endpoint(
    asset_id: uuid.UUID = Path(..., description="Asset ID"),
    db: Session = Depends(get_db),
) -> AssetRead:
    try:
        # Pass UUID object through; route_image_asset handles UUID/str internally
        asset = route_image_asset(db, asset_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return asset


@router.post(
    "/upload_image_with_note",
    response_model=AssetRead,
    status_code=status.HTTP_201_CREATED,
    summary="Upload an image asset with engineer note and optional content_role, with optional auto routing",
)
async def upload_image_with_note(
    project_id: str = Query(..., description="Project UUID"),
    source: str = Query(..., description="Source, e.g. mobile, pc_upload"),
    file: UploadFile = File(...),
    content_role: Optional[str] = Query(default=None, description="meter, nameplate, scene_issue, etc."),
    building_id: Optional[str] = Query(default=None, description="Building UUID"),
    zone_id: Optional[str] = Query(default=None, description="Zone UUID"),
    system_id: Optional[str] = Query(default=None, description="System UUID"),
    device_id: Optional[str] = Query(default=None, description="Device UUID"),
    note: Optional[str] = Form(None),
    title: Optional[str] = Form(None),
    meter_pre_reading: Optional[float] = Query(
        default=None,
        description="Pre-reading value for meter images; only meaningful when content_role='meter'",
    ),
    meter_location: Optional[str] = Query(
        default=None,
        description="Location description for meter images; only meaningful when content_role='meter'",
    ),
    auto_route: bool = Query(False, description="If true, automatically route image after upload"),
    db: Session = Depends(get_db),
) -> AssetRead:
    project_id_uuid = uuid.UUID(project_id) if isinstance(project_id, str) else project_id

    building_uuid = uuid.UUID(building_id) if building_id else None
    zone_uuid = uuid.UUID(zone_id) if zone_id else None
    system_uuid = uuid.UUID(system_id) if system_id else None
    device_uuid = uuid.UUID(device_id) if device_id else None

    hierarchy = _resolve_engineering_hierarchy(
        db,
        project_id=project_id_uuid,
        building_id=building_uuid,
        zone_id=zone_uuid,
        system_id=system_uuid,
        device_id=device_uuid,
    )

    base_dir = settings.local_storage_dir
    file_ext = os.path.splitext(file.filename or "")[1]
    file_name = f"{uuid.uuid4()}{file_ext}"
    rel_path = os.path.join(project_id, file_name)
    abs_dir = os.path.join(base_dir, project_id)
    os.makedirs(abs_dir, exist_ok=True)
    abs_path = os.path.join(abs_dir, file_name)

    with open(abs_path, "wb") as f:
        content = await file.read()
        f.write(content)

    size = os.path.getsize(abs_path)

    file_blob = FileBlob(
        storage_type="local",
        bucket="assets",
        path=rel_path,
        file_name=file.filename or file_name,
        content_type=file.content_type,
        size=float(size),
    )
    db.add(file_blob)
    db.flush()

    location_meta = None
    # 仅在 content_role 为 meter 时写入与仪表相关的元数据，供 LLM worker 和前端使用
    if (content_role or "").lower() == "meter":
        meta: dict = {}
        if meter_pre_reading is not None:
            meta["meter_pre_reading"] = float(meter_pre_reading)
        if meter_location:
            meta["meter_location"] = meter_location
        if meta:
            location_meta = meta

    asset = Asset(
        project_id=project_id_uuid,
        building_id=hierarchy["building"].id if hierarchy["building"] is not None else None,
        zone_id=hierarchy["zone"].id if hierarchy["zone"] is not None else None,
        system_id=hierarchy["system"].id if hierarchy["system"] is not None else None,
        device_id=hierarchy["device"].id if hierarchy["device"] is not None else None,
        modality="image",
        source=source,
        content_role=content_role,
        title=title or file.filename,
        description=note,
        file_id=file_blob.id,
        capture_time=datetime.utcnow(),
        location_meta=location_meta,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)

    # Attach human-readable engineering path for response convenience
    if hierarchy["path"] is not None:
        setattr(asset, "engineer_path", hierarchy["path"])

    # Optional automatic routing based on content_role
    if auto_route and asset.id:
        print(
            f"[DEBUG] upload_image_with_note auto_route={auto_route} "
            f"asset_id={asset.id} content_role={asset.content_role!r}"
        )
        try:
            routed = route_image_asset(db, asset)
            print(
                f"[DEBUG] route_image_asset returned asset_id={routed.id} "
                f"status={routed.status}"
            )
            return routed
        except ValueError as exc:
            # Fall back to plain asset if routing fails (e.g. non-image modality)
            print(f"[WARN] route_image_asset failed for asset {asset.id}: {exc}")
            pass

    return asset


@router.post(
    "/upload_table",
    response_model=AssetRead,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a table data asset (e.g. energy or runtime data)",
)
async def upload_table_asset(
    project_id: str,
    source: str,
    file: UploadFile = File(...),
    content_role: Optional[str] = Query(default=None, description="energy_table, runtime_table, etc."),
    building_id: Optional[str] = Query(default=None, description="Building UUID"),
    zone_id: Optional[str] = Query(default=None, description="Zone UUID"),
    system_id: Optional[str] = Query(default=None, description="System UUID"),
    device_id: Optional[str] = Query(default=None, description="Device UUID"),
    title: Optional[str] = None,
    description: Optional[str] = None,
    db: Session = Depends(get_db),
) -> AssetRead:
    project_id_uuid = uuid.UUID(project_id) if isinstance(project_id, str) else project_id

    building_uuid = uuid.UUID(building_id) if building_id else None
    zone_uuid = uuid.UUID(zone_id) if zone_id else None
    system_uuid = uuid.UUID(system_id) if system_id else None
    device_uuid = uuid.UUID(device_id) if device_id else None

    hierarchy = _resolve_engineering_hierarchy(
        db,
        project_id=project_id_uuid,
        building_id=building_uuid,
        zone_id=zone_uuid,
        system_id=system_uuid,
        device_id=device_uuid,
    )

    base_dir = settings.local_storage_dir
    file_ext = os.path.splitext(file.filename or "")[1]
    file_name = f"{uuid.uuid4()}{file_ext}"
    rel_path = os.path.join(project_id, file_name)
    abs_dir = os.path.join(base_dir, project_id)
    os.makedirs(abs_dir, exist_ok=True)
    abs_path = os.path.join(abs_dir, file_name)

    with open(abs_path, "wb") as f:
        content = await file.read()
        f.write(content)

    size = os.path.getsize(abs_path)

    file_blob = FileBlob(
        storage_type="local",
        bucket="assets",
        path=rel_path,
        file_name=file.filename or file_name,
        content_type=file.content_type,
        size=float(size),
    )
    db.add(file_blob)
    db.flush()

    asset = Asset(
        project_id=project_id_uuid,
        building_id=hierarchy["building"].id if hierarchy["building"] is not None else None,
        zone_id=hierarchy["zone"].id if hierarchy["zone"] is not None else None,
        system_id=hierarchy["system"].id if hierarchy["system"] is not None else None,
        device_id=hierarchy["device"].id if hierarchy["device"] is not None else None,
        modality="table",
        source=source,
        content_role=content_role,
        title=title or file.filename,
        description=description,
        file_id=file_blob.id,
        capture_time=datetime.utcnow(),
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    if hierarchy["path"] is not None:
        setattr(asset, "engineer_path", hierarchy["path"])
    return asset


@router.delete(
    "/{asset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete asset and associated payloads/features and file blob",
)
async def delete_asset(
    asset_id: uuid.UUID = Path(..., description="Asset ID"),
    delete_file: bool = Query(
        True,
        description="If true, also delete underlying file on disk and related FileBlob record",
    ),
    db: Session = Depends(get_db),
) -> None:
    asset = db.query(Asset).filter(Asset.id == asset_id).one_or_none()
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")

    file_blob = None
    file_path: Optional[str] = None
    if asset.file_id is not None:
        file_blob = db.query(FileBlob).filter(FileBlob.id == asset.file_id).one_or_none()
        if file_blob is not None:
            file_path = file_blob.path

    db.delete(asset)
    if file_blob is not None:
        db.delete(file_blob)
    db.commit()

    if delete_file and file_path:
        base_dir = settings.local_storage_dir
        abs_path = os.path.join(base_dir, file_path)
        try:
            if os.path.exists(abs_path):
                os.remove(abs_path)
        except OSError:
            # 文件删除失败不影响接口结果
            pass


@router.post(
    "/{asset_id}/parse_image",
    response_model=AssetRead,
    summary="Run PaddleOCR on an image asset and store structured payload",
)
async def parse_image_asset(
    asset_id: uuid.UUID = Path(..., description="Asset ID"),
    db: Session = Depends(get_db),
) -> AssetRead:
    try:
        structured: AssetStructuredPayload = process_image_with_ocr(db, asset_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    # reload asset to return latest state
    asset = db.query(Asset).filter(Asset.id == asset_id).one()
    return asset


@router.post(
    "/upload",
    response_model=AssetRead,
    status_code=status.HTTP_201_CREATED,
    summary="Upload file and create asset",
)
async def upload_asset(
    project_id: str,
    modality: str,
    source: str,
    file: UploadFile = File(...),
    building_id: Optional[str] = Query(default=None, description="Building UUID"),
    zone_id: Optional[str] = Query(default=None, description="Zone UUID"),
    system_id: Optional[str] = Query(default=None, description="System UUID"),
    device_id: Optional[str] = Query(default=None, description="Device UUID"),
    title: Optional[str] = None,
    description: Optional[str] = None,
    db: Session = Depends(get_db),
) -> AssetRead:
    # Convert string UUID to UUID object
    project_id_uuid = uuid.UUID(project_id) if isinstance(project_id, str) else project_id

    building_uuid = uuid.UUID(building_id) if building_id else None
    zone_uuid = uuid.UUID(zone_id) if zone_id else None
    system_uuid = uuid.UUID(system_id) if system_id else None
    device_uuid = uuid.UUID(device_id) if device_id else None

    hierarchy = _resolve_engineering_hierarchy(
        db,
        project_id=project_id_uuid,
        building_id=building_uuid,
        zone_id=zone_uuid,
        system_id=system_uuid,
        device_id=device_uuid,
    )

    base_dir = settings.local_storage_dir
    file_ext = os.path.splitext(file.filename or "")[1]
    file_name = f"{uuid.uuid4()}{file_ext}"
    rel_path = os.path.join(project_id, file_name)
    abs_dir = os.path.join(base_dir, project_id)
    os.makedirs(abs_dir, exist_ok=True)
    abs_path = os.path.join(abs_dir, file_name)

    with open(abs_path, "wb") as f:
        content = await file.read()
        f.write(content)

    size = os.path.getsize(abs_path)

    file_blob = FileBlob(
        storage_type="local",
        bucket="assets",
        path=rel_path,
        file_name=file.filename or file_name,
        content_type=file.content_type,
        size=float(size),
    )
    db.add(file_blob)
    db.flush()

    asset = Asset(
        project_id=project_id_uuid,
        building_id=hierarchy["building"].id if hierarchy["building"] is not None else None,
        zone_id=hierarchy["zone"].id if hierarchy["zone"] is not None else None,
        system_id=hierarchy["system"].id if hierarchy["system"] is not None else None,
        device_id=hierarchy["device"].id if hierarchy["device"] is not None else None,
        modality=modality,
        source=source,
        title=title,
        description=description,
        file_id=file_blob.id,
        capture_time=datetime.utcnow(),
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    if hierarchy["path"] is not None:
        setattr(asset, "engineer_path", hierarchy["path"])
    return asset
