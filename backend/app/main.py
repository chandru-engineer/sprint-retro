from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, credissuer, dashboard, projects, retros, teams, users
from app.config import get_settings
from app.database import (
    backfill_legacy_org_data,
    drop_password_auth_columns,
    migrate_reaction_question_key,
    sync_schema,
)
from app.utils.logger import get_logger

settings = get_settings()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    migrate_reaction_question_key()
    sync_schema()
    backfill_legacy_org_data()
    drop_password_auth_columns()
    logger.info("%s started (env=%s)", settings.APP_NAME, settings.APP_ENV)
    yield


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(teams.router)
app.include_router(projects.router)
app.include_router(retros.router)
app.include_router(dashboard.router)
app.include_router(credissuer.router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/config")
def public_config():
    return {"app_name": settings.APP_NAME}
