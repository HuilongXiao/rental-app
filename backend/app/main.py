from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db.init_db import check_database_connection, initialize_database


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield


app = FastAPI(title="Rental App API", version="0.1.0", lifespan=lifespan)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "rental-app-api"}


@app.get("/api/health/database")
def database_health() -> dict[str, bool | str]:
    connected = check_database_connection()
    return {
        "status": "ok" if connected else "error",
        "database": "connected" if connected else "unavailable",
    }
