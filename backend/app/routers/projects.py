from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..auth import require_user
from ..db import get_db
from ..models import Project
from ..schemas import ProjectIn, ProjectOut

router = APIRouter(prefix="/api/projects", tags=["projects"], dependencies=[Depends(require_user)])


def _get(db: Session, project_id: int) -> Project:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    return project


def _save(db: Session, project: Project) -> ProjectOut:
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "A project with that name already exists")
    return ProjectOut.model_validate(project, from_attributes=True)


@router.get("", response_model=list[ProjectOut])
def list_projects(db: Session = Depends(get_db)):
    return db.scalars(select(Project).order_by(Project.archived, Project.name)).all()


@router.post("", response_model=ProjectOut, status_code=201)
def create_project(body: ProjectIn, db: Session = Depends(get_db)):
    project = Project(**body.model_dump())
    db.add(project)
    return _save(db, project)


@router.put("/{project_id}", response_model=ProjectOut)
def update_project(project_id: int, body: ProjectIn, db: Session = Depends(get_db)):
    project = _get(db, project_id)
    for k, v in body.model_dump().items():
        setattr(project, k, v)
    return _save(db, project)


@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: int, db: Session = Depends(get_db)):
    # Entries keep their history; their project becomes "No project".
    db.delete(_get(db, project_id))
    db.commit()
