from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.models.org_membership import OrgMembership
from app.models.project import Project
from app.models.retro import Retrospective, RetroParticipant, RetroStatus, InvitationStatus, FeedbackStatus
from app.models.team import Team
from app.models.user import User
from app.schemas.retro import RetroCreate, RetroSummaryOut, RetroUpdate
from app.services.email_service import send_invitation_email
from app.utils.logger import get_logger

logger = get_logger(__name__)


def list_retros(db: Session, org_id: int, project_id: int | None = None, team_id: int | None = None,
                 status_filter: RetroStatus | None = None) -> list[Retrospective]:
    query = (
        db.query(Retrospective)
        .options(joinedload(Retrospective.project), joinedload(Retrospective.team))
        .filter(Retrospective.org_id == org_id)
    )
    if project_id:
        query = query.filter(Retrospective.project_id == project_id)
    if team_id:
        query = query.filter(Retrospective.team_id == team_id)
    if status_filter:
        query = query.filter(Retrospective.status == status_filter)
    return query.order_by(Retrospective.retro_date.desc()).all()


def get_retro(db: Session, org_id: int, retro_id: int) -> Retrospective:
    retro = (
        db.query(Retrospective)
        .options(joinedload(Retrospective.project), joinedload(Retrospective.team))
        .filter(Retrospective.id == retro_id, Retrospective.org_id == org_id)
        .first()
    )
    if not retro:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Retrospective not found")
    return retro


def _org_member_ids(db: Session, org_id: int, user_ids: list[int]) -> set[int]:
    if not user_ids:
        return set()
    rows = (
        db.query(OrgMembership.user_id)
        .filter(OrgMembership.org_id == org_id, OrgMembership.user_id.in_(set(user_ids)))
        .all()
    )
    return {r[0] for r in rows}


def _invite_participants(db: Session, org_id: int, retro: Retrospective, participant_ids: list[int]) -> None:
    for uid in _org_member_ids(db, org_id, participant_ids):
        exists = (
            db.query(RetroParticipant)
            .filter(RetroParticipant.retro_id == retro.id, RetroParticipant.user_id == uid)
            .first()
        )
        if exists:
            continue
        db.add(
            RetroParticipant(
                retro_id=retro.id,
                user_id=uid,
                invitation_status=InvitationStatus.PENDING,
                feedback_status=FeedbackStatus.NOT_STARTED,
            )
        )


def _ensure_in_org(db: Session, org_id: int, model, model_id: int, label: str) -> None:
    exists = db.query(model).filter(model.id == model_id, model.org_id == org_id).first()
    if not exists:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{label} not found in your organization")


def create_retro(db: Session, org_id: int, data: RetroCreate, created_by: int) -> Retrospective:
    _ensure_in_org(db, org_id, Project, data.project_id, "Project")
    _ensure_in_org(db, org_id, Team, data.team_id, "Team")

    retro = Retrospective(
        org_id=org_id,
        project_id=data.project_id,
        team_id=data.team_id,
        name=data.name,
        sprint_name=data.sprint_name,
        sprint_start_date=data.sprint_start_date,
        sprint_end_date=data.sprint_end_date,
        retro_date=data.retro_date,
        retro_time=data.retro_time,
        status=RetroStatus.DRAFT,
        created_by=created_by,
    )
    db.add(retro)
    db.flush()
    _invite_participants(db, org_id, retro, data.participant_ids)
    db.commit()
    db.refresh(retro)
    return retro


def update_retro(db: Session, org_id: int, retro_id: int, data: RetroUpdate) -> Retrospective:
    retro = get_retro(db, org_id, retro_id)
    payload = data.model_dump(exclude_unset=True, exclude={"participant_ids"})
    for field, value in payload.items():
        setattr(retro, field, value)
    if data.participant_ids is not None:
        _invite_participants(db, org_id, retro, data.participant_ids)
    db.commit()
    db.refresh(retro)
    return retro


def send_invitations(db: Session, org_id: int, retro_id: int) -> Retrospective:
    retro = get_retro(db, org_id, retro_id)
    if retro.status == RetroStatus.DRAFT:
        retro.status = RetroStatus.OPEN

    participants = db.query(RetroParticipant).filter(RetroParticipant.retro_id == retro.id).all()
    for participant in participants:
        user = db.get(User, participant.user_id)
        if not user:
            continue
        sent = send_invitation_email(user.email, user.name, retro)
        participant.invitation_status = InvitationStatus.SENT if sent else InvitationStatus.FAILED
        participant.invited_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(retro)
    return retro


def close_retro(db: Session, org_id: int, retro_id: int) -> Retrospective:
    retro = get_retro(db, org_id, retro_id)
    retro.status = RetroStatus.COMPLETED
    db.commit()
    db.refresh(retro)
    return retro


def get_participation_stats(db: Session, retro_id: int) -> dict:
    participants = db.query(RetroParticipant).filter(RetroParticipant.retro_id == retro_id).all()
    total = len(participants)
    submitted = sum(1 for p in participants if p.feedback_status == FeedbackStatus.SUBMITTED)
    percent = round((submitted / total) * 100, 1) if total else 0.0
    return {"total": total, "submitted": submitted, "pending": total - submitted, "percent": percent}


def list_retro_summaries(
    db: Session,
    org_id: int,
    project_id: int | None = None,
    team_id: int | None = None,
    status_filter: RetroStatus | None = None,
    q: str | None = None,
    user_id: int | None = None,
) -> list[RetroSummaryOut]:
    query = (
        db.query(Retrospective)
        .options(joinedload(Retrospective.project), joinedload(Retrospective.team))
        .filter(Retrospective.org_id == org_id)
    )
    if project_id:
        query = query.filter(Retrospective.project_id == project_id)
    if team_id:
        query = query.filter(Retrospective.team_id == team_id)
    if status_filter:
        query = query.filter(Retrospective.status == status_filter)
    if user_id:
        query = query.filter(
            Retrospective.id.in_(
                db.query(RetroParticipant.retro_id).filter(RetroParticipant.user_id == user_id)
            )
        )
    if q:
        like = f"%{q.strip()}%"
        query = (
            query.join(Project, Retrospective.project_id == Project.id)
            .join(Team, Retrospective.team_id == Team.id)
            .filter(
                or_(
                    Retrospective.sprint_name.ilike(like),
                    Retrospective.name.ilike(like),
                    Project.name.ilike(like),
                    Team.name.ilike(like),
                )
            )
        )

    retros = query.order_by(Retrospective.retro_date.desc()).all()

    summaries = []
    for retro in retros:
        stats = get_participation_stats(db, retro.id)
        summaries.append(
            RetroSummaryOut(
                id=retro.id,
                project_id=retro.project_id,
                team_id=retro.team_id,
                name=retro.name,
                sprint_name=retro.sprint_name,
                sprint_start_date=retro.sprint_start_date,
                sprint_end_date=retro.sprint_end_date,
                retro_date=retro.retro_date,
                retro_time=retro.retro_time,
                status=retro.status,
                created_by=retro.created_by,
                created_at=retro.created_at,
                project_name=retro.project.name,
                team_name=retro.team.name,
                submitted_count=stats["submitted"],
                total_count=stats["total"],
                completion_percent=stats["percent"],
            )
        )
    return summaries
