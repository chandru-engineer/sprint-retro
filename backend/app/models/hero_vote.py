from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SprintHeroVote(Base):
    __tablename__ = "sprint_hero_votes"
    __table_args__ = (UniqueConstraint("retro_id", "voter_id", name="uq_hero_vote_retro_voter"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    retro_id: Mapped[int] = mapped_column(ForeignKey("retrospectives.id"), nullable=False)
    voter_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    retro = relationship("Retrospective")
    voter = relationship("User", foreign_keys=[voter_id])
    candidate = relationship("User", foreign_keys=[candidate_id])
