import enum
from datetime import datetime, date, time, timezone

from sqlalchemy import String, DateTime, Date, Time, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class RetroStatus(str, enum.Enum):
    DRAFT = "draft"
    OPEN = "open"
    COMPLETED = "completed"


class InvitationStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class FeedbackStatus(str, enum.Enum):
    NOT_STARTED = "not_started"
    DRAFT = "draft"
    SUBMITTED = "submitted"


class Retrospective(Base):
    __tablename__ = "retrospectives"

    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    sprint_name: Mapped[str] = mapped_column(String(150), nullable=False)
    sprint_start_date: Mapped[date] = mapped_column(Date, nullable=False)
    sprint_end_date: Mapped[date] = mapped_column(Date, nullable=False)
    retro_date: Mapped[date] = mapped_column(Date, nullable=False)
    retro_time: Mapped[time] = mapped_column(Time, nullable=False)
    status: Mapped[RetroStatus] = mapped_column(Enum(RetroStatus), default=RetroStatus.DRAFT, nullable=False)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    project = relationship("Project")
    team = relationship("Team")
    creator = relationship("User")
    participants = relationship("RetroParticipant", back_populates="retro", cascade="all, delete-orphan")
    feedbacks = relationship("Feedback", back_populates="retro", cascade="all, delete-orphan")


class RetroParticipant(Base):
    __tablename__ = "retro_participants"
    __table_args__ = (UniqueConstraint("retro_id", "user_id", name="uq_retro_user"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    retro_id: Mapped[int] = mapped_column(ForeignKey("retrospectives.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    invitation_status: Mapped[InvitationStatus] = mapped_column(
        Enum(InvitationStatus), default=InvitationStatus.PENDING, nullable=False
    )
    feedback_status: Mapped[FeedbackStatus] = mapped_column(
        Enum(FeedbackStatus), default=FeedbackStatus.NOT_STARTED, nullable=False
    )
    invited_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    retro = relationship("Retrospective", back_populates="participants")
    user = relationship("User")
