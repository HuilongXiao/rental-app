import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/rental_app.db")

if DATABASE_URL.startswith("sqlite"):
    SQLITE_PATH = DATABASE_URL.replace("sqlite:///", "")
    if not SQLITE_PATH.startswith("/"):
        SQLITE_PATH = str((PROJECT_ROOT / SQLITE_PATH).resolve())
    Path(SQLITE_PATH).parent.mkdir(parents=True, exist_ok=True)
