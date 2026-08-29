from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "Sprint Retro"
    APP_ENV: str = "development"

    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000

    FRONTEND_URL: str = "http://localhost:3000"

    DATABASE_URL: str = "sqlite:///./data/sprint_retro.db"

    SECRET_KEY: str = "change-me"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 12
    OTP_RESEND_COOLDOWN_SECONDS: int = 30

    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""
    SMTP_USE_TLS: bool = True

    CORS_ORIGINS: str = "http://localhost:3000"

    LOG_LEVEL: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
