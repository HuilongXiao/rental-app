from datetime import datetime, timedelta, timezone
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
    end_at: datetime | None = None
    adult_count: int = Field(ge=0)
    child_count: int = Field(ge=0)
    note: str | None = None
    items: list[OrderItemInput] = Field(min_length=1)


class CheckInInput(BaseModel):
    at: datetime | None = None


class ReturnInput(BaseModel):
    at: datetime | None = None
    reason: str | None = None


def serialize_item(item: OrderItem) -> dict:
    return {"id": item.id, "equipment_spec_id": item.equipment_spec_id, "sale_item_id": item.sale_item_id, "quantity": item.quantity, "unit_price": item.unit_price}


def serialize_order(order: Order, items: list[OrderItem]) -> dict:
    return {"id": order.id, "order_number": order.order_number, "customer_id": order.customer_id, "customer_snapshot": order.customer_snapshot, "status": order.status, "start_at": order.start_at, "end_at": order.end_at, "adult_count": order.adult_count, "child_count": order.child_count, "note": order.note, "check_in_at": order.check_in_at, "return_at": order.return_at, "auto_return_at": order.auto_return_at, "auto_return_occurred": order.auto_return_occurred, "daily_forced_return_occurred": order.daily_forced_return_occurred, "items": [serialize_item(item) for item in items]}


def items_for_order(db: Session, order_id: str) -> list[OrderItem]:
    return list(db.scalars(select(OrderItem).where(OrderItem.order_id == order_id).order_by(OrderItem.created_at)).all())


def get_order_or_404(db: Session, order_id: str) -> Order:
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="order not found")
    return order


@router.get("")
def list_orders(status_filter: str | None = None, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    query = select(Order).order_by(Order.start_at.desc())
    if status_filter:
        query = query.where(Order.status == status_filter)
    return [serialize_order(order, items_for_order(db, order.id)) for order in db.scalars(query).all()]


@router.get("/{order_id}")
def get_order(order_id: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    order = get_order_or_404(db, order_id)
    return serialize_order(order, items_for_order(db, order.id))


@router.post("")
def create_order(payload: OrderInput, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    customer = db.get(Customer, payload.customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="customer not found")
    if payload.adult_count + payload.child_count < 1:
        raise HTTPException(status_code=422, detail="at least one person is required")
    end_at = payload.end_at or payload.start_at + timedelta(hours=2)
    if end_at <= payload.start_at:
        raise HTTPException(status_code=422, detail="end_at must be after start_at")

    order = Order(id=str(uuid4()), order_number=f"O{datetime.now():%Y%m%d%H%M%S}{uuid4().hex[:4].upper()}", customer_id=customer.id, customer_snapshot=customer.name or customer.wechat_nickname, status="active", start_at=payload.start_at, end_at=end_at, adult_count=payload.adult_count, child_count=payload.child_count, note=payload.note, created_by_user_id=user.id, updated_by_user_id=user.id)
    db.add(order)
    db.flush()
    for item in payload.items:
        if bool(item.equipment_spec_id) == bool(item.sale_item_id):
            raise HTTPException(status_code=422, detail="each order item must reference exactly one catalog item")
        catalog = db.get(EquipmentSpec if item.equipment_spec_id else SaleItem, item.equipment_spec_id or item.sale_item_id)
        if not catalog or not catalog.is_active:
            raise HTTPException(status_code=422, detail="catalog item unavailable")
        db.add(OrderItem(id=str(uuid4()), order_id=order.id, equipment_spec_id=item.equipment_spec_id, sale_item_id=item.sale_item_id, quantity=item.quantity, unit_price=catalog.price, created_by_user_id=user.id, updated_by_user_id=user.id))
    db.commit()
    db.refresh(order)
    return serialize_order(order, items_for_order(db, order.id))


@router.post("/{order_id}/check-in")
def check_in(order_id: str, payload: CheckInInput | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    order = get_order_or_404(db, order_id)
    if order.status != "active" or order.check_in_at or order.return_at:
        raise HTTPException(status_code=409, detail="order cannot be checked in")
    order.check_in_at = (payload.at if payload else None) or datetime.now(timezone.utc)
    order.check_in_by_user_id = user.id
    db.commit()
    return serialize_order(order, items_for_order(db, order.id))


@router.post("/{order_id}/return")
def return_order(order_id: str, payload: ReturnInput | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    order = get_order_or_404(db, order_id)
    if not order.check_in_at or order.return_at:
        raise HTTPException(status_code=409, detail="order cannot be returned")
    order.return_at = (payload.at if payload else None) or datetime.now(timezone.utc)
    order.return_by_user_id = user.id
    order.status = "returned"
    if payload and payload.reason:
        order.note = f"{order.note or ''}\nReturn: {payload.reason}".strip()
    db.commit()
    return serialize_order(order, items_for_order(db, order.id))
