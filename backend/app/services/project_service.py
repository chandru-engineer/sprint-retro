from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.team import Team
from app.schemas.project import ProjectCreate, ProjectUpdate


def list_projects(db: Session, org_id: int) -> list[Project]:
    return db.query(Project).filter(Project.org_id == org_id).order_by(Project.name).all()


def get_project(db: Session, org_id: int, project_id: int) -> Project:
    project = db.query(Project).filter(Project.id == project_id, Project.org_id == org_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


def _ensure_team_in_org(db: Session, org_id: int, team_id: int) -> None:
    exists = db.query(Team).filter(Team.id == team_id, Team.org_id == org_id).first()
    if not exists:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Team not found in your organization")


def create_project(db: Session, org_id: int, data: ProjectCreate) -> Project:
    _ensure_team_in_org(db, org_id, data.team_id)
    project = Project(org_id=org_id, **data.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def update_project(db: Session, org_id: int, project_id: int, data: ProjectUpdate) -> Project:
    project = get_project(db, org_id, project_id)
    payload = data.model_dump(exclude_unset=True)
    if "team_id" in payload and payload["team_id"] is not None:
        _ensure_team_in_org(db, org_id, payload["team_id"])
    for field, value in payload.items():
        setattr(project, field, value)
    db.commit()
    db.refresh(project)
    return project
