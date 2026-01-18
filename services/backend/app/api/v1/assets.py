from typing import List, Optional
import os
import uuid
from datetime import datetime

from fastapi import APIRouter, Body, Depends, File, Form, HTTPException, Path, Query, UploadFile, status
from sqlalchemy.orm import Session

from shared.config.settings import get_settings
from shared.db.models_asset import Asset, AssetStructuredPayload, FileBlob
from shared.db.session import get_db
from ...schemas.asset import AssetCreate, AssetRead, AssetDetailRead, SceneIssueReportPayload
from ...services.image_pipeline import process_image_with_ocr, route_image_asset


router = APIRouter()
settings = get_settings()


@router.get("/", response_model=List[AssetRead], summary="List assets")
async def list_assets(
    project_id: Optional[uuid.UUID] = Query(default=None, description="Filter by project ID"),
    modality: Optional[str] = Query(default=None, description="Filter by modality, e.g. image, table"),
    content_role: Optional[str] = Query(default=None, description="Filter by high-level content role"),
    db: Session = Depends(get_db),
) -> List[AssetRead]:
    query = db.query(Asset)
    if project_id is not None:
        query = query.filter(Asset.project_id == project_id)
    if modality is not None:
        query = query.filter(Asset.modality == modality)
    if content_role is not None:
        query = query.filter(Asset.content_role == content_role)

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
    asset = db.query(Asset).filter(Asset.id == asset_id).one_or_none()
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    return asset


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

    # Enforce that this endpoint is only used for scene_issue images
    role = (asset.content_role or "").lower()
    if asset.modality != "image" or role != "scene_issue":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="scene_issue_report is only valid for image assets with content_role='scene_issue'",
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
    note: Optional[str] = Form(None),
    title: Optional[str] = Form(None),
    auto_route: bool = Query(False, description="If true, automatically route image after upload"),
    db: Session = Depends(get_db),
) -> AssetRead:
    project_id_uuid = uuid.UUID(project_id) if isinstance(project_id, str) else project_id

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
        modality="image",
        source=source,
        content_role=content_role,
        title=title or file.filename,
        description=note,
        file_id=file_blob.id,
        capture_time=datetime.utcnow(),
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)

    # Optional automatic routing based on content_role
    if auto_route and asset.id:
        try:
            routed = route_image_asset(db, asset)
            return routed
        except ValueError:
            # Fall back to plain asset if routing fails (e.g. non-image modality)
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
    title: Optional[str] = None,
    description: Optional[str] = None,
    db: Session = Depends(get_db),
) -> AssetRead:
    project_id_uuid = uuid.UUID(project_id) if isinstance(project_id, str) else project_id

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
    return asset


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
    title: Optional[str] = None,
    description: Optional[str] = None,
    db: Session = Depends(get_db),
) -> AssetRead:
    # Convert string UUID to UUID object
    project_id_uuid = uuid.UUID(project_id) if isinstance(project_id, str) else project_id

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
    return asset
