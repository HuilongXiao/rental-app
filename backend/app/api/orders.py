from datetime import datetime, timedelta
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.db.session import get_db
from app.models.customer import Customer
from app.models.equipment import EquipmentSpec, SaleItem
from app.models.order import Order, OrderItem
from app.models.user import User

router = APIRouter(prefix="/api/orders", tags=["orders"])


class OrderItemInput(BaseModel):
    equipment_spec_id: str | None = None
    sale_item_id: str | None = None
    quantity: int = Field(ge=1)


class OrderInput(BaseModel):
    customer_id: str
    start_at: datetime
    adult_count: int = Field(ge=0)
    child_count: int = Field(ge=0)
    note: str | None = None
    items: list[OrderItemInput] = Field(min_length=1)


def serialize_order(order: Order, items: list[OrderItem]) -> dict:
    return {
        "id": order.id,
        "order_number": order.order_number,
        "customer_id": order.customer_id,
        "status": order.status,
        "start_at": order.start_at,
        "end_at": order.end_at,
        "adult_count": order.adult_count,
        "child_count": order.child_count,
        "note": order.note,
        "items": [
            {
                "id": item.id,
                "equipment_spec_id": item.equipment_spec_id,
                "sale_item_id": item.sale_item_id,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
            }
            for item in items
        ],
    }


@router.get("")
def list_orders(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    orders = db.scalars(select(Order).order_by(Order.start_at.desc())).all()
    items_by_order = {}
    for item in db.scalars(select(OrderItem).order_by(OrderItem.created_at.desc())).all():
        items_by_order.setdefault(item.order_id, []).append(item)
    return [serialize_order(order, items_by_order.get(order.id, [])) for order in orders]


@router.post("")
def create_order(payload: OrderInput, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    customer = db.get(Customer, payload.customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="customer not found")
    if payload.adult_count + payload.child_count < 1:
        raise HTTPException(status_code=422, detail="at least one person is required")

    order = Order(
        id=str(uuid4()),
        order_number=f"O{datetime.now():%Y%m%d%H%M%S}{uuid4().hex[:4].upper()}",
        customer_id=customer.id,
        customer_snapshot=customer.name or customer.wechat_nickname,
        status="active",
        start_at=payload.start_at,
        end_at=payload.start_at + timedelta(hours=2),
        adult_count=payload.adult_count,
        child_count=payload.child_count,
        note=payload.note,
        created_by_user_id=user.id,
        updated_by_user_id=user.id,
    )
    db.add(order)
    db.flush()

    for item in payload.items:
        if bool(item.equipment_spec_id) == bool(item.sale_item_id):
            raise HTTPException(status_code=422, detail="each order item must reference exactly one catalog item")

        if item.equipment_spec_id:
            catalog = db.get(EquipmentSpec, item.equipment_spec_id)
            if not catalog or not catalog.is_active:
                raise HTTPException(status_code=422, detail="equipment spec unavailable")
        else:
            catalog = db.get(SaleItem, item.sale_item_id)
            if not catalog or not catalog.is_active:
                raise HTTPException(status_code=422, detail="sale item unavailable")

        db.add(
            OrderItem(
                id=str(uuid4()),
                order_id=order.id,
                equipment_spec_id=item.equipment_spec_id,
                sale_item_id=item.sale_item_id,
                quantity=item.quantity,
                unit_price=catalog.price,
                created_by_user_id=user.id,
                updated_by_user_id=user.id,
            )
        )

    db.commit()
    db.refresh(order)
    return serialize_order(order, list(db.scalars(select(OrderItem).where(OrderItem.order_id == order.id)).all()))
