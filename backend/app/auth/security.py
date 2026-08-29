import secrets
from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext

from app.config import get_settings

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"
PENDING_TOKEN_EXPIRE_MINUTES = 10
OTP_EXPIRE_MINUTES = 10
OTP_MAX_ATTEMPTS = 5


def create_access_token(subject: str, extra_claims: dict | None = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": subject, "exp": expire}
    if extra_claims:
        to_encode.update(extra_claims)
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)


def create_pending_token(subject: str) -> str:
    """Short-lived, org-less token issued after OTP verification when a
    user belongs to multiple orgs and still needs to pick one."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=PENDING_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": subject, "exp": expire, "pending": True}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])


def generate_otp_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def hash_otp_code(code: str) -> str:
    return pwd_context.hash(code)


def verify_otp_code(code: str, code_hash: str) -> bool:
    return pwd_context.verify(code, code_hash)
