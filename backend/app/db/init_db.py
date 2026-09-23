from uuid import uuid4

from sqlalchemy import text

from app.db.base import Base
from app.db.session import engine
from app import models  # noqa: F401 - imports all models before create_all


def initialize_database() -> None:
    """Create missing V1 tables for the development foundation.

    Alembic migrations will replace this startup creation step before production use.
    """
    Base.metadata.create_all(bind=engine)


def check_database_connection() -> bool:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
