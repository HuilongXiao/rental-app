from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.db.session import get_db
from app.models.equipment import EquipmentSpec
from app.models.inventory import InventoryConfiguration
from app.models.order import Order, OrderItem
from app.models.user import User

router = APIRouter(prefix="/api/inventory", tags=["inventory"])


class InventoryInput(BaseModel):
    total_quantity: int = Field(ge=0)


@router.get("")
def list_inventory(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    configs = db.scalars(select(InventoryConfiguration)).all()
    result = []
    for config in configs:
        occupied = (
            db.scalar(
                select(func.coalesce(func.sum(OrderItem.quantity), 0)).join(Order, Order.id == OrderItem.order_id).where(
                    OrderItem.equipment_spec_id == config.equipment_spec_id,
                    Order.check_in_at.is_not(None),
                    Order.return_at.is_(None),
                )
            )
            or 0
        )
        result.append(
            {
                "equipment_spec_id": config.equipment_spec_id,
                "total_quantity": config.total_quantity,
                "occupied_quantity": occupied,
                "available_quantity": config.total_quantity - occupied,
            }
        )
    return result


@router.put("/{equipment_spec_id}")
def set_inventory(equipment_spec_id: str, payload: InventoryInput, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not db.get(EquipmentSpec, equipment_spec_id):
        raise HTTPException(status_code=404, detail="equipment spec not found")

    occupied = (
        db.scalar(
            select(func.coalesce(func.sum(OrderItem.quantity), 0)).join(Order, Order.id == OrderItem.order_id).where(
                OrderItem.equipment_spec_id == equipment_spec_id,
                Order.check_in_at.is_not(None),
                Order.return_at.is_(None),
            )
        )
        or 0
    )
    if payload.total_quantity < occupied:
        raise HTTPException(status_code=422, detail="total inventory cannot be below occupied quantity")

    config = db.scalar(select(InventoryConfiguration).where(InventoryConfiguration.equipment_spec_id == equipment_spec_id))
    if not config:
        config = InventoryConfiguration(id=str(uuid4()), equipment_spec_id=equipment_spec_id)
        db.add(config)
    config.total_quantity = payload.total_quantity
    config.updated_by_user_id = user.id
    db.commit()
    return {
        "equipment_spec_id": equipment_spec_id,
        "total_quantity": config.total_quantity,
        "occupied_quantity": occupied,
        "available_quantity": config.total_quantity - occupied,
    }
