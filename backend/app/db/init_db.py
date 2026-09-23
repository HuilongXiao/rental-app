from sqlalchemy import text

# Importing the model package registers every mapped class on Base.metadata.
from app import models  # noqa: F401
from app.db.base import Base
from app.db.session import engine


def initialize_database() -> None:
    """Create missing tables during development startup.

    Alembic migrations should replace this for production schema upgrades.
    """
    Base.metadata.create_all(bind=engine)


def check_database_connection() -> bool:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
