from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_current_user, require_admin
from app.database import get_db
from app.schemas.project import ProjectCreate, ProjectOut, ProjectUpdate
from app.services import project_service

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("", response_model=list[ProjectOut])
def list_projects(db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    return project_service.list_projects(db, current_user.org_id)


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(
    project_id: int, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)
):
    return project_service.get_project(db, current_user.org_id, project_id)


@router.post("", response_model=ProjectOut, status_code=201)
def create_project(
    payload: ProjectCreate, db: Session = Depends(get_db), current_user: CurrentUser = Depends(require_admin)
):
    return project_service.create_project(db, current_user.org_id, payload)


@router.put("/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: int,
    payload: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_admin),
):
    return project_service.update_project(db, current_user.org_id, project_id, payload)
