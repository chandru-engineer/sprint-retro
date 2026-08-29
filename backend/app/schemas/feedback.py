from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.retro import FeedbackStatus


class FeedbackBase(BaseModel):
    achievement: str = ""
    went_well: str = ""
    did_not_go_well: str = ""
    learnings: str = ""
    improvements: str = ""


class FeedbackSave(FeedbackBase):
    """Used for saving a draft."""


class FeedbackOut(FeedbackBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    retro_id: int
    user_id: int
    status: FeedbackStatus
    created_at: datetime
    updated_at: datetime
    submitted_at: datetime | None


class ReactionSummary(BaseModel):
    emoji: str
    count: int
    reacted_by_me: bool


class FeedbackWithUser(FeedbackOut):
    user_name: str
    reactions: dict[str, list[ReactionSummary]] = {}


class ReactRequest(BaseModel):
    emoji: str
    question_key: str
