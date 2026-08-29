"""CredIssuer integration.

Everything in this file that talks to CredIssuer itself is mocked — there is
no real CredIssuer account behind this yet. The mock boundary is deliberately
narrow (`_mock_list_templates` and `_mock_issue_credential`) so that wiring in
the real CredIssuer REST API later is a matter of replacing those two
functions with real HTTP calls (using the same api_key / template_id
signature) and leaving everything else — config storage, permissions,
issuance history, the one-click UI — unchanged.
"""

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.credissuer import CredIssuerConfig, IssuedCredential
from app.models.user import User
from app.schemas.credissuer import CredIssuerConfigIn, CredIssuerTemplate
from app.services import hero_vote_service
from app.utils.logger import get_logger

logger = get_logger(__name__)

_MOCK_TEMPLATES = [
    CredIssuerTemplate(
        id="tpl_sprint_completion",
        name="Sprint Completion Certificate",
        description="Awarded to every participant who submitted their retro response for the sprint.",
    ),
    CredIssuerTemplate(
        id="tpl_sprint_hero",
        name="Sprint Hero Award",
        description="Awarded to the teammate voted Sprint Hero for the retro.",
    ),
    CredIssuerTemplate(
        id="tpl_retro_participation",
        name="Retro Participation Badge",
        description="A lightweight badge confirming participation in a retrospective.",
    ),
]


def _mock_list_templates(api_key: str) -> list[CredIssuerTemplate]:
    """Stand-in for `GET {CREDISSUER_BASE_URL}/templates` using the org's
    api_key. Real integration: forward the key as a bearer token and return
    the templates CredIssuer reports for this issuer account."""
    if not api_key.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="API key is required")
    return _MOCK_TEMPLATES


def _mock_issue_credential(api_key: str, template_id: str, recipient: User) -> str:
    """Stand-in for `POST {CREDISSUER_BASE_URL}/credentials/issue`. Real
    integration: send {template_id, subject: {name, email}} with the api_key
    as bearer auth, and return the vc id/URI CredIssuer responds with."""
    logger.info(
        "MOCK CredIssuer issue: template=%s recipient=%s (api_key=%s...)",
        template_id,
        recipient.email,
        api_key[:6],
    )
    return f"vc_mock_{uuid.uuid4().hex[:16]}"


def list_templates(api_key: str) -> list[CredIssuerTemplate]:
    return _mock_list_templates(api_key)


def get_config(db: Session, org_id: int) -> CredIssuerConfig | None:
    return db.query(CredIssuerConfig).filter(CredIssuerConfig.org_id == org_id).first()


def save_config(db: Session, org_id: int, payload: CredIssuerConfigIn, configured_by: int) -> CredIssuerConfig:
    # Validate the key actually resolves a template list before saving —
    # catches a typo'd key immediately rather than at the first issuance.
    templates = _mock_list_templates(payload.api_key)
    if not any(t.id == payload.template_id for t in templates):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown template for this API key")

    config = get_config(db, org_id)
    if not config:
        config = CredIssuerConfig(org_id=org_id, configured_by=configured_by)
        db.add(config)

    config.api_key = payload.api_key
    config.template_id = payload.template_id
    config.template_name = payload.template_name
    config.configured_by = configured_by
    db.commit()
    db.refresh(config)
    return config


def _require_config(db: Session, org_id: int) -> CredIssuerConfig:
    config = get_config(db, org_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CredIssuer isn't configured yet. Set it up in Settings first.",
        )
    return config


def _require_sprint_hero(db: Session, retro_id: int, recipient_id: int) -> None:
    """Credential issuance is reserved for the Sprint Hero — the participant
    with the most votes in that retro's hero vote — not every participant."""
    results = hero_vote_service.get_results(db, retro_id)
    winner_id = results.results[0].user_id if results.results else None
    if winner_id != recipient_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Credentials can only be issued to this retro's Sprint Hero.",
        )


def issue_credential(
    db: Session, org_id: int, recipient: User, issued_by: int, retro_id: int | None = None
) -> IssuedCredential:
    config = _require_config(db, org_id)
    if retro_id is not None:
        _require_sprint_hero(db, retro_id, recipient.id)
    vc_id = _mock_issue_credential(config.api_key, config.template_id, recipient)

    record = IssuedCredential(
        org_id=org_id,
        retro_id=retro_id,
        user_id=recipient.id,
        template_id=config.template_id,
        template_name=config.template_name,
        vc_id=vc_id,
        status="issued",
        issued_by=issued_by,
        issued_at=datetime.now(timezone.utc),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    logger.info(
        "Credential issued org_id=%s recipient=%s template=%s vc_id=%s",
        org_id,
        recipient.email,
        config.template_id,
        vc_id,
    )
    return record


def list_issued_credentials(db: Session, org_id: int, retro_id: int | None = None) -> list[IssuedCredential]:
    query = db.query(IssuedCredential).filter(IssuedCredential.org_id == org_id)
    if retro_id is not None:
        query = query.filter(IssuedCredential.retro_id == retro_id)
    return query.order_by(IssuedCredential.issued_at.desc()).all()
