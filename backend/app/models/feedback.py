from datetime import datetime, timezone

from sqlalchemy import String, Text, DateTime, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.retro import FeedbackStatus


class Feedback(Base):
    __tablename__ = "feedback"
    __table_args__ = (UniqueConstraint("retro_id", "user_id", name="uq_feedback_retro_user"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    retro_id: Mapped[int] = mapped_column(ForeignKey("retrospectives.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    achievement: Mapped[str] = mapped_column(Text, default="")
    went_well: Mapped[str] = mapped_column(Text, default="")
    did_not_go_well: Mapped[str] = mapped_column(Text, default="")
    learnings: Mapped[str] = mapped_column(Text, default="")
    improvements: Mapped[str] = mapped_column(Text, default="")

    status: Mapped[FeedbackStatus] = mapped_column(Enum(FeedbackStatus), default=FeedbackStatus.DRAFT, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    retro = relationship("Retrospective", back_populates="feedbacks")
    user = relationship("User")
