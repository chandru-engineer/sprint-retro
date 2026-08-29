from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class FeedbackReaction(Base):
    """An emoji reaction from one participant on a single question's answer
    within a teammate's submitted retro response. Reactions are scoped per
    question (achievement, went_well, ...), not the response as a whole, so
    reacting to one answer never shows up under another. A user can react
    with several different emoji to the same answer, but only once each
    (re-tapping the same emoji removes it)."""

    __tablename__ = "feedback_reactions"
    __table_args__ = (
        UniqueConstraint(
            "feedback_id", "user_id", "emoji", "question_key", name="uq_reaction_feedback_user_emoji_question"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    feedback_id: Mapped[int] = mapped_column(ForeignKey("feedback.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    emoji: Mapped[str] = mapped_column(String(8), nullable=False)
    question_key: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User")
