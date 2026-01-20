from typing import List, Optional
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query, Header
from sqlalchemy.orm import Session

from shared.db.session import get_db
from shared.db.models_project import Project
from shared.db.models_asset import Asset
from ...schemas.project import ProjectCreate, ProjectRead, ProjectUpdate


router = APIRouter()


@router.get("/", response_model=List[ProjectRead], summary="List projects")
async def list_projects(
    skip: int = 0,
    limit: int = 100,
    include_deleted: bool = Query(False, description="是否包含已删除项目"),
    db: Session = Depends(get_db)
) -> List[ProjectRead]:
    """获取项目列表"""
    query = db.query(Project)
    if not include_deleted:
        query = query.filter(Project.is_deleted.is_(False))
    projects = query.order_by(Project.name).offset(skip).limit(limit).all()
    return projects


@router.post(
    "/",
    response_model=ProjectRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create project",
)
async def create_project(
    payload: ProjectCreate,
    db: Session = Depends(get_db),
) -> ProjectRead:
    """创建新项目"""
    project = Project(**payload.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("/{project_id}", response_model=ProjectRead, summary="Get project")
async def get_project(
    project_id: str,
    include_deleted: bool = Query(False, description="是否包含已删除项目"),
    db: Session = Depends(get_db)
) -> ProjectRead:
    """获取单个项目详情"""
    try:
        project_uuid = uuid.UUID(project_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid project ID format"
        )

    query = db.query(Project).filter(Project.id == project_uuid)
    if not include_deleted:
        query = query.filter(Project.is_deleted.is_(False))

    project = query.first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    return project


@router.patch("/{project_id}", response_model=ProjectRead, summary="Update project")
async def update_project(
    project_id: str,
    payload: ProjectUpdate,
    db: Session = Depends(get_db)
) -> ProjectRead:
    """更新项目信息"""
    try:
        project_uuid = uuid.UUID(project_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid project ID format"
        )

    project = db.query(Project).filter(Project.id == project_uuid).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)

    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete project")
async def delete_project(
    project_id: str,
    reason: Optional[str] = Query(None, description="删除原因"),
    hard_delete: bool = Query(False, description="是否物理删除（危险操作）"),
    operator: Optional[str] = Header(None, description="操作人"),
    db: Session = Depends(get_db)
) -> None:
    """删除项目（默认软删除，可选物理删除）"""
    try:
        project_uuid = uuid.UUID(project_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid project ID format"
        )

    project = db.query(Project).filter(Project.id == project_uuid).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    if hard_delete:
        if not reason:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="硬删除必须提供删除原因"
            )
        db.query(Asset).filter(Asset.project_id == project_uuid).delete(synchronize_session=False)
        db.delete(project)
    else:
        project.is_deleted = True
        project.deleted_at = datetime.utcnow()
        project.deleted_by = operator or "system"
        project.deletion_reason = reason

    db.commit()
    return None


@router.post("/{project_id}/restore", response_model=ProjectRead, summary="Restore project")
async def restore_project(
    project_id: str,
    operator: Optional[str] = Header(None, description="操作人"),
    db: Session = Depends(get_db)
) -> ProjectRead:
    """恢复已软删除的项目"""
    try:
        project_uuid = uuid.UUID(project_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid project ID format"
        )

    project = db.query(Project).filter(
        Project.id == project_uuid,
        Project.is_deleted.is_(True)
    ).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deleted project not found"
        )

    # 恢复项目
    project.is_deleted = False
    project.deleted_at = None
    project.deleted_by = None
    project.deletion_reason = None

    db.commit()
    db.refresh(project)
    return project
