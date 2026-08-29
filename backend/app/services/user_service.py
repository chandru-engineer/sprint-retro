from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.org_membership import OrgMembership
from app.models.organization import Organization
from app.models.user import User
from app.schemas.user import UserCreate, UserOut, UserUpdate
from app.services.email_service import send_existing_account_org_invite_email, send_new_account_invite_email
from app.utils.logger import get_logger

logger = get_logger(__name__)


def to_user_out(user: User, membership: OrgMembership) -> UserOut:
    return UserOut(
        id=user.id,
        name=user.name,
        email=user.email,
        role=membership.role,
        is_active=membership.is_active,
        created_at=user.created_at,
    )


def list_org_users(db: Session, org_id: int) -> list[UserOut]:
    rows = (
        db.query(User, OrgMembership)
        .join(OrgMembership, OrgMembership.user_id == User.id)
        .filter(OrgMembership.org_id == org_id)
        .order_by(User.name)
        .all()
    )
    return [to_user_out(u, m) for u, m in rows]


def get_org_membership(db: Session, org_id: int, user_id: int) -> tuple[User, OrgMembership]:
    row = (
        db.query(User, OrgMembership)
        .join(OrgMembership, OrgMembership.user_id == User.id)
        .filter(OrgMembership.org_id == org_id, User.id == user_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found in this organization")
    return row


def create_or_attach_user(db: Session, org_id: int, data: UserCreate) -> UserOut:
    org = db.get(Organization, org_id)
    existing = db.query(User).filter(User.email == data.email.lower()).first()

    if existing:
        already_member = (
            db.query(OrgMembership)
            .filter(OrgMembership.org_id == org_id, OrgMembership.user_id == existing.id)
            .first()
        )
        if already_member:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="This person is already a member of your organization"
            )
        membership = OrgMembership(org_id=org_id, user_id=existing.id, role=data.role, is_active=True)
        db.add(membership)
        db.commit()
        db.refresh(membership)
        logger.info("Existing user attached to org user_id=%s org_id=%s", existing.id, org_id)
        send_existing_account_org_invite_email(existing.email, existing.name, org.name)
        return to_user_out(existing, membership)

    user = User(
        name=data.name,
        email=data.email.lower(),
        is_active=True,
    )
    db.add(user)
    db.flush()
    membership = OrgMembership(org_id=org_id, user_id=user.id, role=data.role, is_active=True)
    db.add(membership)
    db.commit()
    db.refresh(user)
    db.refresh(membership)
    send_new_account_invite_email(user.email, user.name, org.name)
    return to_user_out(user, membership)


def update_org_user(db: Session, org_id: int, user_id: int, data: UserUpdate) -> UserOut:
    user, membership = get_org_membership(db, org_id, user_id)
    if data.name is not None:
        user.name = data.name
    if data.role is not None:
        membership.role = data.role
    if data.is_active is not None:
        membership.is_active = data.is_active
    db.commit()
    db.refresh(user)
    db.refresh(membership)
    return to_user_out(user, membership)


def set_membership_active(db: Session, org_id: int, user_id: int, is_active: bool) -> UserOut:
    user, membership = get_org_membership(db, org_id, user_id)
    membership.is_active = is_active
    db.commit()
    db.refresh(membership)
    return to_user_out(user, membership)
