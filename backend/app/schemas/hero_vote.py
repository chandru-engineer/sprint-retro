from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


class HeroCandidate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str


class HeroVoteIn(BaseModel):
    candidate_id: int
    is_anonymous: bool = True
    comment: str | None = None

    @field_validator("comment")
    @classmethod
    def _blank_to_none(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        if len(v) > 500:
            raise ValueError("Comment must be 500 characters or fewer")
        return v or None


class HeroVoteOut(BaseModel):
    candidate_id: int
    candidate_name: str
    is_anonymous: bool
    comment: str | None
    updated_at: datetime


class HeroVoteEntry(BaseModel):
    voter_name: str | None  # None when the voter chose to stay anonymous
    comment: str | None


class HeroVoteResultItem(BaseModel):
    user_id: int
    user_name: str
    vote_count: int
    entries: list[HeroVoteEntry]


class HeroVoteResults(BaseModel):
    retro_id: int
    total_votes: int
    results: list[HeroVoteResultItem]
