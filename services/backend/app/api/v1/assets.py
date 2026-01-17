from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from shared.db.models_asset import Asset, FileBlob
from shared.db.session import get_db

from ...schemas.asset import AssetCreate, AssetRead


router = APIRouter()


@router.get("/", response_model=List[AssetRead], summary="List assets")
async def list_assets(
    project_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
) -> List[AssetRead]:
    query = db.query(Asset)
    if project_id is not None:
        query = query.filter(Asset.project_id == project_id)
    assets = query.order_by(Asset.capture_time.desc().nullslast()).all()
    return assets


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
