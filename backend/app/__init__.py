from app.api.auth import router as auth_router
from app.api.catalog import router as catalog_router
from app.api.customers import router as customers_router
from app.api.inventory import router as inventory_router
from app.api.orders import router as orders_router
from app.api.payments import router as payments_router

__all__ = [
    "auth_router",
    "catalog_router",
    "customers_router",
    "inventory_router",
    "orders_router",
    "payments_router",
]
