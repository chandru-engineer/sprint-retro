from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_current_user, require_admin
from app.database import get_db
from app.schemas.team import TeamCreate, TeamOut, TeamUpdate
from app.services import team_service

router = APIRouter(prefix="/api/teams", tags=["teams"])


@router.get("", response_model=list[TeamOut])
def list_teams(db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    return [team_service.to_team_out(t) for t in team_service.list_teams(db, current_user.org_id)]


@router.get("/{team_id}", response_model=TeamOut)
def get_team(team_id: int, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    return team_service.to_team_out(team_service.get_team(db, current_user.org_id, team_id))


@router.post("", response_model=TeamOut, status_code=201)
def create_team(
    payload: TeamCreate, db: Session = Depends(get_db), current_user: CurrentUser = Depends(require_admin)
):
    return team_service.to_team_out(team_service.create_team(db, current_user.org_id, payload))


@router.put("/{team_id}", response_model=TeamOut)
def update_team(
    team_id: int,
    payload: TeamUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_admin),
):
    return team_service.to_team_out(team_service.update_team(db, current_user.org_id, team_id, payload))
