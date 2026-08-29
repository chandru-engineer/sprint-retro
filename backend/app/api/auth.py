from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_current_user, get_pending_user
from app.database import get_db
from app.models.org_membership import OrgMembership
from app.models.user import User
from app.schemas.auth import (
    OrgOption,
    OtpRequestedResponse,
    RequestOtpRequest,
    SelectOrgRequest,
    SignupRequest,
    TokenResponse,
    VerifyOtpRequest,
)
from app.schemas.user import UserOut
from app.services import auth_service, user_service

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _token_response_for(user: User, membership: OrgMembership) -> TokenResponse:
    token = auth_service.issue_token(user, membership)
    return TokenResponse(
        requires_org_selection=False,
        access_token=token,
        user=user_service.to_user_out(user, membership),
    )


def _resolve_org_and_respond(db: Session, user: User) -> TokenResponse:
    """After OTP verification (whether that followed a signup or a login
    request), figure out which org(s) the user can enter and respond
    accordingly — one org logs straight in, several ask which one."""
    memberships = auth_service.get_active_memberships(db, user.id)
    if not memberships:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don't have access to any organization")

    if len(memberships) == 1:
        return _token_response_for(user, memberships[0])

    pending_token = auth_service.issue_pending_token(user)
    return TokenResponse(
        requires_org_selection=True,
        pending_token=pending_token,
        orgs=[OrgOption(id=m.org_id, name=m.org.name, role=m.role.value) for m in memberships],
    )


@router.post("/signup", response_model=OtpRequestedResponse, status_code=201)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    user = auth_service.signup(db, payload)
    return OtpRequestedResponse(message="Verification code sent to your email.", email=user.email)


@router.post("/login", response_model=OtpRequestedResponse)
def login(payload: RequestOtpRequest, db: Session = Depends(get_db)):
    auth_service.request_login_otp(db, payload.email)
    return OtpRequestedResponse(message="Verification code sent to your email.", email=payload.email)


@router.post("/verify-otp", response_model=TokenResponse)
def verify_otp(payload: VerifyOtpRequest, db: Session = Depends(get_db)):
    user = auth_service.verify_otp(db, payload.email, payload.code)
    return _resolve_org_and_respond(db, user)


@router.post("/resend-otp", response_model=OtpRequestedResponse)
def resend_otp(payload: RequestOtpRequest, db: Session = Depends(get_db)):
    auth_service.resend_otp(db, payload.email)
    return OtpRequestedResponse(message="A new code has been sent.", email=payload.email)


@router.post("/select-org", response_model=TokenResponse)
def select_org(
    payload: SelectOrgRequest, db: Session = Depends(get_db), pending_user: User = Depends(get_pending_user)
):
    membership = (
        db.query(OrgMembership)
        .filter(
            OrgMembership.user_id == pending_user.id,
            OrgMembership.org_id == payload.org_id,
            OrgMembership.is_active.is_(True),
        )
        .first()
    )
    if not membership:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don't have access to that organization")
    return _token_response_for(pending_user, membership)


@router.get("/my-orgs", response_model=list[OrgOption])
def my_orgs(current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    memberships = auth_service.get_active_memberships(db, current_user.id)
    return [OrgOption(id=m.org_id, name=m.org.name, role=m.role.value) for m in memberships]


@router.post("/switch-org", response_model=TokenResponse)
def switch_org(
    payload: SelectOrgRequest, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)
):
    membership = (
        db.query(OrgMembership)
        .filter(
            OrgMembership.user_id == current_user.id,
            OrgMembership.org_id == payload.org_id,
            OrgMembership.is_active.is_(True),
        )
        .first()
    )
    if not membership:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don't have access to that organization")
    user = db.get(User, current_user.id)
    return _token_response_for(user, membership)


@router.get("/me", response_model=UserOut)
def me(current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    user, membership = user_service.get_org_membership(db, current_user.org_id, current_user.id)
    return user_service.to_user_out(user, membership)


@router.post("/logout")
def logout(current_user: CurrentUser = Depends(get_current_user)):
    # JWTs are stateless; the client discards the token. Endpoint exists for a clean logout UX.
    return {"detail": "Logged out"}
