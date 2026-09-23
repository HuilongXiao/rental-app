from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.db.session import get_db
from app.models.equipment import EquipmentSpec, EquipmentType, SaleItem
from app.models.user import User

router = APIRouter(prefix="/api/catalog", tags=["catalog"])


class EquipmentTypeInput(BaseModel):
    name: str = Field(min_length=1, max_length=128)


class EquipmentSpecInput(BaseModel):
    equipment_type_id: str
    name: str = Field(min_length=1, max_length=128)
    price: int = Field(ge=0)
    capacity: int = Field(ge=1)
    is_active: bool = True


class SaleItemInput(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    price: int = Field(ge=0)
    is_active: bool = True


def catalog_item(item: EquipmentSpec | SaleItem, kind: str) -> dict:
    payload = {"id": item.id, "type": kind, "name": item.name, "price": item.price, "is_active": item.is_active}
    if kind == "equipment":
        payload.update({"capacity": item.capacity, "equipment_type_id": item.equipment_type_id})
    return payload


@router.get("")
def list_catalog(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    equipment = [catalog_item(item, "equipment") for item in db.scalars(select(EquipmentSpec).order_by(EquipmentSpec.name)).all()]
    sale_items = [catalog_item(item, "sale") for item in db.scalars(select(SaleItem).order_by(SaleItem.name)).all()]
    types = [{"id": item.id, "name": item.name} for item in db.scalars(select(EquipmentType).order_by(EquipmentType.name)).all()]
    return {"equipment_types": types, "equipment": equipment, "sale_items": sale_items}


@router.post("/equipment-types")
def create_equipment_type(payload: EquipmentTypeInput, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    if db.scalar(select(EquipmentType).where(EquipmentType.name == payload.name)):
        raise HTTPException(status_code=409, detail="equipment type already exists")
    item = EquipmentType(id=str(uuid4()), name=payload.name)
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"id": item.id, "name": item.name}


@router.post("/equipment-specs")
def create_equipment_spec(payload: EquipmentSpecInput, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    if not db.get(EquipmentType, payload.equipment_type_id):
        raise HTTPException(status_code=404, detail="equipment type not found")
    item = EquipmentSpec(
        id=str(uuid4()),
        equipment_type_id=payload.equipment_type_id,
        name=payload.name,
        price=payload.price,
        capacity=payload.capacity,
        is_active=payload.is_active,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return catalog_item(item, "equipment")


@router.post("/sale-items")
def create_sale_item(payload: SaleItemInput, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    if db.scalar(select(SaleItem).where(SaleItem.name == payload.name)):
        raise HTTPException(status_code=409, detail="sale item already exists")
    item = SaleItem(id=str(uuid4()), name=payload.name, price=payload.price, is_active=payload.is_active)
    db.add(item)
    db.commit()
    db.refresh(item)
    return catalog_item(item, "sale")
