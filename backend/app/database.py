import os
from datetime import datetime, timezone

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

settings = get_settings()

connect_args = {}
db_url = settings.DATABASE_URL
if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
    if db_url.startswith("sqlite:///./"):
        db_path = db_url.replace("sqlite:///./", "")
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)

engine = create_engine(db_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def migrate_reaction_question_key() -> None:
    """Reactions moved from being scoped to a whole feedback response to
    being scoped to one question within it (a new `question_key` column with
    a wider unique constraint). SQLite can't add a column into an existing
    composite UNIQUE constraint, so an old `feedback_reactions` table is
    dropped and let `sync_schema()` recreate it fresh with the new shape —
    safe because this feature is new enough that no deployment should have
    accumulated real rows yet; if it ever does, this only re-migrates once
    and logs how many reactions were discarded. Idempotent — a no-op once
    the column exists.
    """
    inspector = inspect(engine)
    if not inspector.has_table("feedback_reactions"):
        return
    if "question_key" in {col["name"] for col in inspector.get_columns("feedback_reactions")}:
        return

    with engine.begin() as conn:
        count = conn.execute(text("SELECT COUNT(*) FROM feedback_reactions")).scalar()
        conn.execute(text("DROP TABLE feedback_reactions"))
    logger.info("Recreated feedback_reactions with question_key column (discarded %d old row(s))", count or 0)


def sync_schema() -> None:
    """Additive-only schema sync: creates missing tables, and adds any
    columns a model has that the live table doesn't (no drops/renames).
    Keeps existing deployments upgradable without a full migration tool.
    """
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    with engine.begin() as conn:
        for table in Base.metadata.sorted_tables:
            if not inspector.has_table(table.name):
                continue
            existing_columns = {col["name"] for col in inspector.get_columns(table.name)}
            for column in table.columns:
                if column.name in existing_columns:
                    continue
                ddl_type = column.type.compile(dialect=engine.dialect)
                conn.execute(text(f'ALTER TABLE "{table.name}" ADD COLUMN "{column.name}" {ddl_type}'))


def backfill_legacy_org_data() -> None:
    """One-time upgrade path for pre-multi-tenant deployments: any existing
    user without an org membership gets folded into a default organization,
    using their old global `role` column value (left over from before this
    migration; additive-only sync_schema never drops it, and SQLite enforces
    that column's original NOT NULL, so it must be dropped once it's no
    longer needed — otherwise every new signup fails). Existing users are
    marked verified so they aren't locked out by the new signup/OTP flow.
    Idempotent — a no-op once the legacy `role` column is gone.
    """
    inspector = inspect(engine)
    if not inspector.has_table("users"):
        return
    if "role" not in {col["name"] for col in inspector.get_columns("users")}:
        return  # fresh install, or already migrated and cleaned up

    with engine.begin() as conn:
        orphans = conn.execute(
            text(
                """
                SELECT u.id, u.role FROM users u
                LEFT JOIN org_memberships m ON m.user_id = u.id
                WHERE m.id IS NULL
                """
            )
        ).fetchall()

        if orphans:
            now = datetime.now(timezone.utc)
            default_org_id = conn.execute(text("SELECT id FROM organizations ORDER BY id LIMIT 1")).scalar()
            if default_org_id is None:
                conn.execute(
                    text("INSERT INTO organizations (name, created_at) VALUES (:name, :now)"),
                    {"name": "Acme Corp", "now": now},
                )
                default_org_id = conn.execute(text("SELECT id FROM organizations ORDER BY id DESC LIMIT 1")).scalar()

            for user_id, role in orphans:
                conn.execute(
                    text(
                        """
                        INSERT INTO org_memberships (org_id, user_id, role, is_active, created_at)
                        VALUES (:org_id, :user_id, :role, 1, :now)
                        """
                    ),
                    {"org_id": default_org_id, "user_id": user_id, "role": role or "MEMBER", "now": now},
                )

            conn.execute(text("UPDATE teams SET org_id = :org_id WHERE org_id IS NULL"), {"org_id": default_org_id})
            conn.execute(text("UPDATE projects SET org_id = :org_id WHERE org_id IS NULL"), {"org_id": default_org_id})
            conn.execute(
                text("UPDATE retrospectives SET org_id = :org_id WHERE org_id IS NULL"), {"org_id": default_org_id}
            )
            logger.info("Backfilled %d legacy user(s) into org_id=%s", len(orphans), default_org_id)

        # Always drop the now-unused legacy column once reachable here, even
        # on a run where there were no orphans left to backfill (e.g. an
        # interrupted upgrade that backfilled memberships but never got to
        # this step).
        conn.execute(text('ALTER TABLE users DROP COLUMN "role"'))
        logger.info("Dropped legacy users.role column")


def drop_password_auth_columns() -> None:
    """Login moved from password+OTP to OTP-only. Deployments that went
    through the earlier password-based multi-tenant migration have
    `password_hash` (NOT NULL — blocks every new user insert until dropped,
    same failure mode as the legacy `role` column) and `is_verified` sitting
    unused on `users`. Idempotent — a no-op once both are gone.
    """
    inspector = inspect(engine)
    if not inspector.has_table("users"):
        return
    existing = {col["name"] for col in inspector.get_columns("users")}
    to_drop = [c for c in ("password_hash", "is_verified") if c in existing]
    if not to_drop:
        return

    with engine.begin() as conn:
        for column in to_drop:
            conn.execute(text(f'ALTER TABLE users DROP COLUMN "{column}"'))
    logger.info("Dropped legacy password-auth column(s): %s", ", ".join(to_drop))
