from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TeamMemberOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str


class TeamBase(BaseModel):
    name: str
    description: str = ""
    team_lead_id: int | None = None


class TeamCreate(TeamBase):
    member_ids: list[int] = []


class TeamUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    team_lead_id: int | None = None
    is_active: bool | None = None
    member_ids: list[int] | None = None


class TeamOut(TeamBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    created_at: datetime
    members: list[TeamMemberOut] = []
