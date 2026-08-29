from datetime import datetime, date, time

from pydantic import BaseModel, ConfigDict

from app.models.retro import RetroStatus, InvitationStatus, FeedbackStatus


class RetroBase(BaseModel):
    project_id: int
    team_id: int
    name: str
    sprint_name: str
    sprint_start_date: date
    sprint_end_date: date
    retro_date: date
    retro_time: time


class RetroCreate(RetroBase):
    participant_ids: list[int] = []


class RetroUpdate(BaseModel):
    name: str | None = None
    sprint_name: str | None = None
    sprint_start_date: date | None = None
    sprint_end_date: date | None = None
    retro_date: date | None = None
    retro_time: time | None = None
    status: RetroStatus | None = None
    participant_ids: list[int] | None = None


class RetroOut(RetroBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: RetroStatus
    created_by: int
    created_at: datetime


class ParticipantOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    user_name: str
    user_email: str
    invitation_status: InvitationStatus
    feedback_status: FeedbackStatus
    invited_at: datetime | None
    submitted_at: datetime | None


class RetroDetailOut(RetroOut):
    participants: list[ParticipantOut] = []
    submitted_count: int = 0
    total_count: int = 0
    completion_percent: float = 0


class RetroSummaryOut(RetroOut):
    project_name: str
    team_name: str
    submitted_count: int = 0
    total_count: int = 0
    completion_percent: float = 0
