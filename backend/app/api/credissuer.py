from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, require_admin
from app.database import get_db
from app.schemas.credissuer import (
    CredIssuerConfigIn,
    CredIssuerConfigOut,
    CredIssuerTemplate,
    IssueCredentialRequest,
    IssuedCredentialOut,
)
from app.services import credissuer_service, user_service

router = APIRouter(prefix="/api/credissuer", tags=["credissuer"])


def _mask(api_key: str) -> str:
    if len(api_key) <= 8:
        return "*" * len(api_key)
    return f"{api_key[:4]}{'*' * (len(api_key) - 8)}{api_key[-4:]}"


@router.get("/config", response_model=CredIssuerConfigOut)
def get_config(db: Session = Depends(get_db), current_user: CurrentUser = Depends(require_admin)):
    config = credissuer_service.get_config(db, current_user.org_id)
    if not config:
        return CredIssuerConfigOut(configured=False)
    return CredIssuerConfigOut(
        configured=True,
        template_id=config.template_id,
        template_name=config.template_name,
        api_key_masked=_mask(config.api_key),
        updated_at=config.updated_at,
    )


@router.put("/config", response_model=CredIssuerConfigOut)
def save_config(
    payload: CredIssuerConfigIn,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_admin),
):
    config = credissuer_service.save_config(db, current_user.org_id, payload, current_user.id)
    return CredIssuerConfigOut(
        configured=True,
        template_id=config.template_id,
        template_name=config.template_name,
        api_key_masked=_mask(config.api_key),
        updated_at=config.updated_at,
    )


@router.get("/templates", response_model=list[CredIssuerTemplate])
def list_templates(api_key: str = Query(...), current_user: CurrentUser = Depends(require_admin)):
    return credissuer_service.list_templates(api_key)


@router.post("/issue", response_model=IssuedCredentialOut)
def issue_credential(
    payload: IssueCredentialRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_admin),
):
    recipient, _membership = user_service.get_org_membership(db, current_user.org_id, payload.user_id)
    record = credissuer_service.issue_credential(
        db, current_user.org_id, recipient, current_user.id, payload.retro_id
    )
    return IssuedCredentialOut(
        id=record.id,
        user_id=record.user_id,
        user_name=recipient.name,
        template_name=record.template_name,
        vc_id=record.vc_id,
        status=record.status,
        issued_at=record.issued_at,
    )


@router.get("/history", response_model=list[IssuedCredentialOut])
def issuance_history(
    retro_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_admin),
):
    records = credissuer_service.list_issued_credentials(db, current_user.org_id, retro_id)
    return [
        IssuedCredentialOut(
            id=r.id,
            user_id=r.user_id,
            user_name=r.user.name,
            template_name=r.template_name,
            vc_id=r.vc_id,
            status=r.status,
            issued_at=r.issued_at,
        )
        for r in records
    ]
