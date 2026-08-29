from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_current_user
from app.database import get_db
from app.models.retro import FeedbackStatus, Retrospective, RetroParticipant, RetroStatus
from app.models.user import UserRole

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("")
def get_dashboard(db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    if current_user.role in (UserRole.ADMIN, UserRole.PMO):
        base = db.query(Retrospective).filter(Retrospective.org_id == current_user.org_id)
        active_retros = base.filter(Retrospective.status == RetroStatus.OPEN).count()
        completed_retros = base.filter(Retrospective.status == RetroStatus.COMPLETED).count()
        pending_responses = (
            db.query(RetroParticipant)
            .join(Retrospective, Retrospective.id == RetroParticipant.retro_id)
            .filter(
                Retrospective.org_id == current_user.org_id,
                Retrospective.status == RetroStatus.OPEN,
                RetroParticipant.feedback_status != FeedbackStatus.SUBMITTED,
            )
            .count()
        )
        return {
            "role": current_user.role.value,
            "active_retros": active_retros,
            "pending_responses": pending_responses,
            "completed_retros": completed_retros,
        }

    participations = (
        db.query(RetroParticipant)
        .join(Retrospective, Retrospective.id == RetroParticipant.retro_id)
        .filter(RetroParticipant.user_id == current_user.id, Retrospective.org_id == current_user.org_id)
        .all()
    )
    pending = []
    completed = []
    for p in participations:
        retro = p.retro
        item = {
            "id": retro.id,
            "sprint_name": retro.sprint_name,
            "team_name": retro.team.name,
            "retro_date": retro.retro_date,
            "status": retro.status.value,
            "feedback_status": p.feedback_status.value,
        }
        if retro.status == RetroStatus.COMPLETED:
            completed.append(item)
        elif p.feedback_status != FeedbackStatus.SUBMITTED:
            pending.append(item)
        else:
            completed.append(item)

    return {"role": current_user.role.value, "pending_retros": pending, "completed_retros": completed}
