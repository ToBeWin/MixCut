from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.project import Project
from backend.sanitize import sanitize_filename, sanitize_user_text
from backend.schemas.project import Project as ProjectSchema
from backend.schemas.project import ProjectCreate, ProjectList

router = APIRouter()


def _project_to_schema(project: Project) -> ProjectSchema:
    return ProjectSchema(
        id=project.id,
        name=project.name,
        description=project.description,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


@router.get("", response_model=ProjectList)
async def list_projects(db: AsyncSession = Depends(get_db)) -> ProjectList:
    result = await db.execute(select(Project).order_by(Project.updated_at.desc()))
    projects = result.scalars().all()
    return ProjectList(projects=[_project_to_schema(p) for p in projects])


@router.post("", response_model=ProjectSchema, status_code=201)
async def create_project(payload: ProjectCreate, db: AsyncSession = Depends(get_db)) -> ProjectSchema:
    name = sanitize_filename(payload.name, max_len=100)
    desc = sanitize_user_text(payload.description, max_len=1000) if payload.description else None
    project = Project(name=name, description=desc)
    db.add(project)
    await db.flush()
    await db.refresh(project)
    return _project_to_schema(project)


@router.get("/{project_id}", response_model=ProjectSchema)
async def get_project(project_id: str, db: AsyncSession = Depends(get_db)) -> ProjectSchema:
    project = await db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return _project_to_schema(project)


@router.patch("/{project_id}", response_model=ProjectSchema)
async def update_project(project_id: str, payload: ProjectCreate, db: AsyncSession = Depends(get_db)) -> ProjectSchema:
    project = await db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    project.name = sanitize_filename(payload.name, max_len=100)
    project.description = sanitize_user_text(payload.description, max_len=1000) if payload.description else None
    await db.flush()
    await db.refresh(project)
    return _project_to_schema(project)


@router.delete("/{project_id}", status_code=204)
async def delete_project(project_id: str, db: AsyncSession = Depends(get_db)) -> None:
    project = await db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    await db.delete(project)