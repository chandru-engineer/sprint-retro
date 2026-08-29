from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.feedback import Feedback
from app.models.feedback_reaction import FeedbackReaction
from app.models.retro import Retrospective, RetroParticipant, RetroStatus, FeedbackStatus
from app.schemas.feedback import FeedbackSave, ReactionSummary
from app.utils.logger import get_logger

logger = get_logger(__name__)

ALLOWED_REACTION_EMOJIS = {"👍", "❤️", "🎉", "👏", "💡", "🙌"}
ALLOWED_QUESTION_KEYS = {"achievement", "went_well", "did_not_go_well", "learnings", "improvements"}


def _get_participant(db: Session, retro_id: int, user_id: int) -> RetroParticipant:
    participant = (
        db.query(RetroParticipant)
        .filter(RetroParticipant.retro_id == retro_id, RetroParticipant.user_id == user_id)
        .first()
    )
    if not participant:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not a participant of this retro")
    return participant


def get_my_feedback(db: Session, retro_id: int, user_id: int) -> Feedback | None:
    return db.query(Feedback).filter(Feedback.retro_id == retro_id, Feedback.user_id == user_id).first()


def _get_retro_or_404(db: Session, retro_id: int) -> Retrospective:
    retro = db.get(Retrospective, retro_id)
    if not retro:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Retrospective not found")
    return retro


def save_draft(db: Session, retro_id: int, user_id: int, data: FeedbackSave) -> Feedback:
    retro = _get_retro_or_404(db, retro_id)
    participant = _get_participant(db, retro_id, user_id)

    if retro.status == RetroStatus.COMPLETED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Retrospective is completed and read-only")

    feedback = get_my_feedback(db, retro_id, user_id)
    if feedback and feedback.status == FeedbackStatus.SUBMITTED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Response already submitted and cannot be edited")

    if not feedback:
        feedback = Feedback(retro_id=retro_id, user_id=user_id, status=FeedbackStatus.DRAFT)
        db.add(feedback)

    for field, value in data.model_dump().items():
        setattr(feedback, field, value)
    feedback.status = FeedbackStatus.DRAFT

    participant.feedback_status = FeedbackStatus.DRAFT

    db.commit()
    db.refresh(feedback)
    return feedback


def submit_feedback(db: Session, retro_id: int, user_id: int, data: FeedbackSave) -> Feedback:
    retro = _get_retro_or_404(db, retro_id)
    participant = _get_participant(db, retro_id, user_id)

    if retro.status == RetroStatus.COMPLETED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Retrospective is completed and read-only")

    feedback = get_my_feedback(db, retro_id, user_id)
    if feedback and feedback.status == FeedbackStatus.SUBMITTED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Response already submitted")

    required_fields = ["achievement", "went_well", "did_not_go_well", "learnings", "improvements"]
    payload = data.model_dump()
    missing = [f for f in required_fields if not payload.get(f, "").strip()]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"All questions are required before submitting. Missing: {', '.join(missing)}",
        )

    if not feedback:
        feedback = Feedback(retro_id=retro_id, user_id=user_id)
        db.add(feedback)

    for field, value in payload.items():
        setattr(feedback, field, value)

    now = datetime.now(timezone.utc)
    feedback.status = FeedbackStatus.SUBMITTED
    feedback.submitted_at = now

    participant.feedback_status = FeedbackStatus.SUBMITTED
    participant.submitted_at = now

    db.commit()
    db.refresh(feedback)
    logger.info("Feedback submitted retro_id=%s user_id=%s", retro_id, user_id)
    return feedback


def list_feedback_for_retro(db: Session, retro_id: int, submitted_only: bool = False) -> list[Feedback]:
    query = db.query(Feedback).filter(Feedback.retro_id == retro_id)
    if submitted_only:
        query = query.filter(Feedback.status == FeedbackStatus.SUBMITTED)
    return query.all()


def get_reactions(db: Session, feedback_id: int, current_user_id: int) -> dict[str, list[ReactionSummary]]:
    rows = db.query(FeedbackReaction).filter(FeedbackReaction.feedback_id == feedback_id).all()
    tally: dict[str, dict[str, dict]] = {}
    for r in rows:
        by_emoji = tally.setdefault(r.question_key, {})
        entry = by_emoji.setdefault(r.emoji, {"count": 0, "reacted_by_me": False})
        entry["count"] += 1
        if r.user_id == current_user_id:
            entry["reacted_by_me"] = True
    return {
        question_key: [
            ReactionSummary(emoji=emoji, count=data["count"], reacted_by_me=data["reacted_by_me"])
            for emoji, data in sorted(by_emoji.items())
        ]
        for question_key, by_emoji in tally.items()
    }


def toggle_reaction(
    db: Session, feedback_id: int, user_id: int, emoji: str, question_key: str
) -> dict[str, list[ReactionSummary]]:
    if emoji not in ALLOWED_REACTION_EMOJIS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported reaction")
    if question_key not in ALLOWED_QUESTION_KEYS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported question")

    feedback = db.get(Feedback, feedback_id)
    if not feedback or feedback.status != FeedbackStatus.SUBMITTED:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No submitted response to react to")

    existing = (
        db.query(FeedbackReaction)
        .filter(
            FeedbackReaction.feedback_id == feedback_id,
            FeedbackReaction.user_id == user_id,
            FeedbackReaction.emoji == emoji,
            FeedbackReaction.question_key == question_key,
        )
        .first()
    )
    if existing:
        db.delete(existing)
    else:
        db.add(
            FeedbackReaction(
                feedback_id=feedback_id, user_id=user_id, emoji=emoji, question_key=question_key
            )
        )
    db.commit()

    return get_reactions(db, feedback_id, user_id)
