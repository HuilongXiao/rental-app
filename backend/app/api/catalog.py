from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.db.session import get_db
from app.models.equipment import EquipmentSpec, EquipmentType, SaleItem
from app.models.user import User

router = APIRouter(prefix="/api/catalog", tags=["catalog"])


def catalog_item(item: EquipmentSpec | SaleItem, kind: str) -> dict:
    return {"id": item.id, "type": kind, "name": item.name, "price": item.price, "is_active": item.is_active, **({"capacity": item.capacity, "equipment_type_id": item.equipment_type_id} if kind == "equipment" else {})}


@router.get("")
def list_catalog(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    equipment = [catalog_item(item, "equipment") for item in db.scalars(select(EquipmentSpec).order_by(EquipmentSpec.name)).all()]
    sale_items = [catalog_item(item, "sale") for item in db.scalars(select(SaleItem).order_by(SaleItem.name)).all()]
    types = [{"id": item.id, "name": item.name} for item in db.scalars(select(EquipmentType).order_by(EquipmentType.name)).all()]
    return {"equipment_types": types, "equipment": equipment, "sale_items": sale_items}
