"""Projects API endpoints.

This module handles project CRUD operations and project-level queries.
"""
from datetime import datetime
from typing import List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from shared.db.session import get_db
from shared.db.models_project import Project
from ...schemas.project import ProjectCreate, ProjectRead, ProjectUpdate


router = APIRouter()


@router.get(
    "/",
    response_model=List[ProjectRead],
    summary="List all projects",
)
async def list_projects(
    status_filter: Optional[str] = Query(default=None, alias="status", description="Filter by project status"),
    type_filter: Optional[str] = Query(default=None, alias="type", description="Filter by project type"),
    client_contains: Optional[str] = Query(default=None, description="Filter by client name (partial match)"),
    name_contains: Optional[str] = Query(default=None, description="Filter by project name (partial match)"),
    include_deleted: bool = Query(default=False, description="Include soft-deleted projects"),
    db: Session = Depends(get_db),
) -> List[ProjectRead]:
    """List all projects with optional filters.

    Supports filtering by:
    - status: project status (e.g., 'in_progress', 'completed')
    - type: project type (e.g., 'industrial', 'commercial')
    - client: partial match on client name
    - name: partial match on project name
    - include_deleted: include soft-deleted projects
    """
    query = db.query(Project)

    # Apply filters
    if status_filter is not None:
        query = query.filter(Project.status == status_filter)

    if type_filter is not None:
        query = query.filter(Project.type == type_filter)

    if client_contains:
        pattern = f"%{client_contains}%"
        query = query.filter(Project.client.ilike(pattern))

    if name_contains:
        pattern = f"%{name_contains}%"
        query = query.filter(Project.name.ilike(pattern))

    # Exclude soft-deleted projects by default
    if not include_deleted:
        query = query.filter(Project.is_deleted == False)

    # Order by creation date (newest first)
    projects = query.order_by(Project.id.desc()).all()

    return projects


@router.get(
    "/{project_id}",
    response_model=ProjectRead,
    summary="Get project by ID",
)
async def get_project(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> ProjectRead:
    """Get a specific project by ID."""
    project = db.query(Project).filter(Project.id == project_id).one_or_none()

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    return project


@router.post(
    "/",
    response_model=ProjectRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new project",
)
async def create_project(
    payload: ProjectCreate,
    db: Session = Depends(get_db),
) -> ProjectRead:
    """Create a new project."""
    project = Project(**payload.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)

    return project


@router.patch(
    "/{project_id}",
    response_model=ProjectRead,
    summary="Update a project",
)
async def update_project(
    project_id: uuid.UUID,
    payload: ProjectUpdate,
    db: Session = Depends(get_db),
) -> ProjectRead:
    """Update an existing project."""
    project = db.query(Project).filter(Project.id == project_id).one_or_none()

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    # Update only provided fields
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)

    db.commit()
    db.refresh(project)

    return project


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a project (soft delete)",
)
async def delete_project(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> None:
    """Soft delete a project (marks as deleted but keeps in database)."""
    project = db.query(Project).filter(Project.id == project_id).one_or_none()

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    # Soft delete
    project.is_deleted = True
    project.deleted_at = datetime.now()
    # project.deleted_by = ... # TODO: Add user authentication
    # project.deletion_reason = ... # TODO: Add reason to request body

    db.commit()

    return None
