from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


class CredIssuerTemplate(BaseModel):
    id: str
    name: str
    description: str


class CredIssuerConfigIn(BaseModel):
    api_key: str
    template_id: str
    template_name: str

    @field_validator("api_key", "template_id", "template_name")
    @classmethod
    def not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("This field is required")
        return v


class CredIssuerConfigOut(BaseModel):
    configured: bool
    template_id: str | None = None
    template_name: str | None = None
    api_key_masked: str | None = None
    updated_at: datetime | None = None


class IssueCredentialRequest(BaseModel):
    user_id: int
    retro_id: int | None = None


class IssuedCredentialOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    user_name: str
    template_name: str
    vc_id: str
    status: str
    issued_at: datetime
