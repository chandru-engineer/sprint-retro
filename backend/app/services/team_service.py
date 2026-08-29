from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.org_membership import OrgMembership
from app.models.team import Team, TeamMember
from app.schemas.team import TeamCreate, TeamMemberOut, TeamOut, TeamUpdate


def list_teams(db: Session, org_id: int) -> list[Team]:
    return db.query(Team).filter(Team.org_id == org_id).order_by(Team.name).all()


def get_team(db: Session, org_id: int, team_id: int) -> Team:
    team = db.query(Team).filter(Team.id == team_id, Team.org_id == org_id).first()
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    return team


def to_team_out(team: Team) -> TeamOut:
    return TeamOut(
        id=team.id,
        name=team.name,
        description=team.description,
        team_lead_id=team.team_lead_id,
        is_active=team.is_active,
        created_at=team.created_at,
        members=[TeamMemberOut.model_validate(tm.user) for tm in team.members],
    )


def _filter_to_org_members(db: Session, org_id: int, user_ids: list[int]) -> set[int]:
    if not user_ids:
        return set()
    rows = (
        db.query(OrgMembership.user_id)
        .filter(OrgMembership.org_id == org_id, OrgMembership.user_id.in_(set(user_ids)))
        .all()
    )
    return {r[0] for r in rows}


def _sync_members(db: Session, org_id: int, team: Team, member_ids: list[int]) -> None:
    valid_ids = _filter_to_org_members(db, org_id, member_ids)
    db.query(TeamMember).filter(TeamMember.team_id == team.id).delete()
    db.flush()
    for uid in valid_ids:
        db.add(TeamMember(team_id=team.id, user_id=uid))


def create_team(db: Session, org_id: int, data: TeamCreate) -> Team:
    team_lead_id = data.team_lead_id
    if team_lead_id and not _filter_to_org_members(db, org_id, [team_lead_id]):
        team_lead_id = None

    team = Team(
        org_id=org_id,
        name=data.name,
        description=data.description,
        team_lead_id=team_lead_id,
        is_active=True,
    )
    db.add(team)
    db.flush()
    _sync_members(db, org_id, team, data.member_ids)
    db.commit()
    db.refresh(team)
    return team


def update_team(db: Session, org_id: int, team_id: int, data: TeamUpdate) -> Team:
    team = get_team(db, org_id, team_id)
    if data.name is not None:
        team.name = data.name
    if data.description is not None:
        team.description = data.description
    if data.team_lead_id is not None:
        team.team_lead_id = data.team_lead_id if _filter_to_org_members(db, org_id, [data.team_lead_id]) else None
    if data.is_active is not None:
        team.is_active = data.is_active
    if data.member_ids is not None:
        _sync_members(db, org_id, team, data.member_ids)
    db.commit()
    db.refresh(team)
    return team
