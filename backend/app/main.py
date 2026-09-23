from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.catalog import router as catalog_router
from app.api.customers import router as customers_router
from app.api.inventory import router as inventory_router
from app.api.orders import router as orders_router
from app.api.payments import router as payments_router
from app.db.init_db import check_database_connection, initialize_database
from app.db.seed import seed_system_data


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    seed_system_data()
    yield


app = FastAPI(title="Rental App API", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(auth_router)
app.include_router(catalog_router)
app.include_router(customers_router)
app.include_router(orders_router)
app.include_router(inventory_router)
app.include_router(payments_router)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "rental-app-api"}


@app.get("/api/health/database")
def database_health() -> dict[str, str]:
    connected = check_database_connection()
    return {"status": "ok" if connected else "error", "database": "connected" if connected else "unavailable"}
