from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class CredIssuerConfig(Base):
    """One CredIssuer connection per organization: the API key used to talk
    to CredIssuer, and the credential template an Admin has chosen to issue
    with. `api_key` is stored as given by mock-integration design — a real
    integration should encrypt it at rest before this ships beyond mock."""

    __tablename__ = "credissuer_configs"

    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False, unique=True)
    api_key: Mapped[str] = mapped_column(String(200), nullable=False)
    template_id: Mapped[str] = mapped_column(String(100), nullable=False)
    template_name: Mapped[str] = mapped_column(String(150), nullable=False)
    configured_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )


class IssuedCredential(Base):
    """A record of one Verifiable Credential issued to a user via CredIssuer.
    Doubles as the issuance notification log shown in the UI. `vc_id` and the
    issuance call itself are mocked for now (see credissuer_service.py) —
    swapping in the real CredIssuer API only touches that one function."""

    __tablename__ = "issued_credentials"

    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    retro_id: Mapped[int | None] = mapped_column(ForeignKey("retrospectives.id"), nullable=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    template_id: Mapped[str] = mapped_column(String(100), nullable=False)
    template_name: Mapped[str] = mapped_column(String(150), nullable=False)
    vc_id: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="issued")
    issued_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    issued_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", foreign_keys=[user_id])
