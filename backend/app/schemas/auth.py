from pydantic import BaseModel, EmailStr, field_validator

from app.schemas.user import UserOut


class RequestOtpRequest(BaseModel):
    """Used both to start a login and to request signup verification —
    the code is delivered the same way either way."""

    email: EmailStr


class OtpRequestedResponse(BaseModel):
    message: str
    email: str


class OrgOption(BaseModel):
    id: int
    name: str
    role: str


class TokenResponse(BaseModel):
    requires_org_selection: bool = False
    access_token: str | None = None
    token_type: str = "bearer"
    user: UserOut | None = None
    pending_token: str | None = None
    orgs: list[OrgOption] | None = None


class SelectOrgRequest(BaseModel):
    org_id: int


class SignupRequest(BaseModel):
    org_name: str
    name: str
    email: EmailStr

    @field_validator("org_name", "name")
    @classmethod
    def _not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("This field cannot be blank")
        return v


class VerifyOtpRequest(BaseModel):
    email: EmailStr
    code: str
