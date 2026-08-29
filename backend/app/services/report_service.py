from sqlalchemy.orm import Session

from app.models.feedback import Feedback
from app.models.retro import Retrospective, FeedbackStatus
from app.models.user import User


def build_report(db: Session, retro: Retrospective) -> dict:
    feedbacks = (
        db.query(Feedback)
        .filter(Feedback.retro_id == retro.id, Feedback.status == FeedbackStatus.SUBMITTED)
        .all()
    )
    participants_count = len(retro.participants)

    def bullets(field: str) -> list[str]:
        return [getattr(fb, field).strip() for fb in feedbacks if getattr(fb, field).strip()]

    return {
        "project_name": retro.project.name,
        "team_name": retro.team.name,
        "sprint_name": retro.sprint_name,
        "sprint_start_date": retro.sprint_start_date,
        "sprint_end_date": retro.sprint_end_date,
        "retro_date": retro.retro_date,
        "retro_time": retro.retro_time,
        "participants": participants_count,
        "responses": len(feedbacks),
        "achievements": bullets("achievement"),
        "went_well": bullets("went_well"),
        "did_not_go_well": bullets("did_not_go_well"),
        "learnings": bullets("learnings"),
        "improvements": bullets("improvements"),
    }
