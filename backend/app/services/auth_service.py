from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.auth.security import (
    OTP_EXPIRE_MINUTES,
    OTP_MAX_ATTEMPTS,
    create_access_token,
    create_pending_token,
    generate_otp_code,
    hash_otp_code,
    verify_otp_code,
)
from app.config import get_settings
from app.models.email_otp import EmailOtp
from app.models.org_membership import OrgMembership
from app.models.organization import Organization
from app.models.user import User, UserRole
from app.schemas.auth import SignupRequest
from app.services.email_service import send_otp_email
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def get_active_memberships(db: Session, user_id: int) -> list[OrgMembership]:
    return (
        db.query(OrgMembership)
        .join(Organization, Organization.id == OrgMembership.org_id)
        .filter(OrgMembership.user_id == user_id, OrgMembership.is_active.is_(True))
        .order_by(Organization.name)
        .all()
    )


def issue_token(user: User, membership: OrgMembership) -> str:
    return create_access_token(
        subject=str(user.id), extra_claims={"org_id": membership.org_id, "role": membership.role.value}
    )


def issue_pending_token(user: User) -> str:
    return create_pending_token(subject=str(user.id))


def _send_otp(db: Session, user: User) -> None:
    """Sends a fresh login code, subject to a resend cooldown. Used both for
    the initial signup/login request and for "resend code"."""
    last = (
        db.query(EmailOtp)
        .filter(EmailOtp.user_id == user.id)
        .order_by(EmailOtp.created_at.desc())
        .first()
    )
    if last and (_now() - last.created_at) < timedelta(seconds=settings.OTP_RESEND_COOLDOWN_SECONDS):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Please wait before requesting another code")

    code = generate_otp_code()
    otp = EmailOtp(
        user_id=user.id,
        purpose="login",
        code_hash=hash_otp_code(code),
        expires_at=_now() + timedelta(minutes=OTP_EXPIRE_MINUTES),
    )
    db.add(otp)
    db.commit()
    send_otp_email(user.email, user.name, code)


def _get_user_or_404(db: Session, email: str) -> User:
    user = db.query(User).filter(User.email == email.lower()).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No account found for this email. Sign up instead."
        )
    return user


def signup(db: Session, data: SignupRequest) -> User:
    existing = db.query(User).filter(User.email == data.email.lower()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists. Log in instead, or ask an admin to add you to their organization.",
        )

    user = User(name=data.name.strip(), email=data.email.lower(), is_active=True)
    db.add(user)
    db.flush()

    org = Organization(name=data.org_name.strip())
    db.add(org)
    db.flush()

    membership = OrgMembership(org_id=org.id, user_id=user.id, role=UserRole.ADMIN, is_active=True)
    db.add(membership)
    db.commit()
    db.refresh(user)

    _send_otp(db, user)
    logger.info("Signup started user_id=%s org_id=%s", user.id, org.id)
    return user


def request_login_otp(db: Session, email: str) -> None:
    user = _get_user_or_404(db, email)
    _send_otp(db, user)


def resend_otp(db: Session, email: str) -> None:
    user = _get_user_or_404(db, email)
    _send_otp(db, user)


def verify_otp(db: Session, email: str, code: str) -> User:
    user = db.query(User).filter(User.email == email.lower()).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid code")

    otp = (
        db.query(EmailOtp)
        .filter(EmailOtp.user_id == user.id, EmailOtp.consumed_at.is_(None))
        .order_by(EmailOtp.created_at.desc())
        .first()
    )
    if not otp:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No verification code found. Request a new one.")
    if otp.expires_at < _now():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This code has expired. Request a new one.")
    if otp.attempts >= OTP_MAX_ATTEMPTS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Too many incorrect attempts. Request a new one.")

    if not verify_otp_code(code, otp.code_hash):
        otp.attempts += 1
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect code.")

    otp.consumed_at = _now()
    db.commit()
    db.refresh(user)
    logger.info("OTP verified user_id=%s", user.id)
    return user
