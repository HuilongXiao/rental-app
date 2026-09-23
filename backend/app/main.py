from sqlalchemy import text

from app.db.base import Base
from app.db.session import engine


def initialize_database() -> None:
    Base.metadata.create_all(bind=engine)


def check_database_connection() -> bool:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
