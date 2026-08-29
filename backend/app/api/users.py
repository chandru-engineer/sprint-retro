from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, require_admin, require_pmo
from app.database import get_db
from app.schemas.user import UserCreate, UserOut, UserUpdate
from app.services import user_service

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), current_user: CurrentUser = Depends(require_pmo)):
    return user_service.list_org_users(db, current_user.org_id)


@router.post("", response_model=UserOut, status_code=201)
def create_user(
    payload: UserCreate, db: Session = Depends(get_db), current_user: CurrentUser = Depends(require_admin)
):
    return user_service.create_or_attach_user(db, current_user.org_id, payload)


@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: Session = Depends(get_db), current_user: CurrentUser = Depends(require_admin)):
    user, membership = user_service.get_org_membership(db, current_user.org_id, user_id)
    return user_service.to_user_out(user, membership)


@router.put("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_admin),
):
    return user_service.update_org_user(db, current_user.org_id, user_id, payload)


@router.post("/{user_id}/disable", response_model=UserOut)
def disable_user(user_id: int, db: Session = Depends(get_db), current_user: CurrentUser = Depends(require_admin)):
    return user_service.set_membership_active(db, current_user.org_id, user_id, False)


@router.post("/{user_id}/enable", response_model=UserOut)
def enable_user(user_id: int, db: Session = Depends(get_db), current_user: CurrentUser = Depends(require_admin)):
    return user_service.set_membership_active(db, current_user.org_id, user_id, True)
