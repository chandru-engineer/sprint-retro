from dataclasses import dataclass
from datetime import datetime

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jwt import PyJWTError
from sqlalchemy.orm import Session

from app.auth.security import decode_access_token
from app.database import get_db
from app.models.org_membership import OrgMembership
from app.models.user import User, UserRole
from app.utils.logger import get_logger

logger = get_logger(__name__)
bearer_scheme = HTTPBearer(auto_error=False)


@dataclass
class CurrentUser:
    """The authenticated user, scoped to the organization encoded in their
    access token. A person may have a different id/role in another org, but
    within a single request they only ever act as this one membership."""

    id: int
    org_id: int
    role: UserRole
    name: str
    email: str
    is_active: bool
    created_at: datetime


def _decode(credentials: HTTPAuthorizationCredentials | None) -> dict:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        return decode_access_token(credentials.credentials)
    except (PyJWTError, TypeError, ValueError):
        logger.warning("Authentication failed: invalid token")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> CurrentUser:
    payload = _decode(credentials)
    if payload.get("pending"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Organization selection required")
    try:
        user_id = int(payload.get("sub"))
        org_id = int(payload.get("org_id"))
    except (TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    membership = (
        db.query(OrgMembership)
        .filter(OrgMembership.user_id == user_id, OrgMembership.org_id == org_id)
        .first()
    )
    if not membership or not membership.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No active access to this organization")

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    return CurrentUser(
        id=user.id,
        org_id=org_id,
        role=membership.role,
        name=user.name,
        email=user.email,
        is_active=user.is_active,
        created_at=user.created_at,
    )


def get_pending_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """For the org-selection step: an OTP-verified user who hasn't picked
    which organization to enter yet."""
    payload = _decode(credentials)
    if not payload.get("pending"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token for this step")
    try:
        user_id = int(payload.get("sub"))
    except (TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    return user


def require_roles(*roles: UserRole):
    def _check(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if current_user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user

    return _check


require_admin = require_roles(UserRole.ADMIN)
require_pmo = require_roles(UserRole.ADMIN, UserRole.PMO)
