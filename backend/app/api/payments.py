from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.db.session import get_db
from app.models.equipment import EquipmentSpec, SaleItem
from app.models.order import Order, OrderItem
from app.models.payment import Payment, PaymentItem
from app.models.user import User

router = APIRouter(prefix="/api/orders", tags=["payments"])


class AdjustmentInput(BaseModel):
    quantity: int = Field(ge=1)
    unit_amount: int = Field(ge=-1_000_000)
    note: str = Field(min_length=1)


def compute_total_amount(db: Session, order_id: str) -> int:
    normal_total = db.scalar(select(func.coalesce(func.sum(OrderItem.quantity * OrderItem.unit_price), 0)).where(OrderItem.order_id == order_id)) or 0
    adjustment_total = db.scalar(select(func.coalesce(func.sum(PaymentItem.amount), 0)).join(Payment, Payment.id == PaymentItem.payment_id).where(Payment.order_id == order_id)) or 0
    return int(normal_total + adjustment_total)


def payment_view(db: Session, order: Order) -> dict:
    payment = db.scalar(select(Payment).where(Payment.order_id == order.id))
    items = list(db.scalars(select(PaymentItem).where(PaymentItem.payment_id == payment.id).order_by(PaymentItem.created_at)).all()) if payment else []
    return {"order_id": order.id, "payment_id": payment.id if payment else None, "amount_fen": compute_total_amount(db, order.id), "adjustments": [{"id": item.id, "quantity": item.quantity, "unit_amount": item.unit_amount, "amount": item.amount, "note": item.note} for item in items]}


@router.get("/{order_id}/payment")
def get_payment(order_id: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="order not found")
    return payment_view(db, order)


@router.post("/{order_id}/payment/adjustments")
def add_adjustment(order_id: str, payload: AdjustmentInput, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="order not found")
    payment = db.scalar(select(Payment).where(Payment.order_id == order_id))
    if not payment:
        payment = Payment(id=str(uuid4()), order_id=order_id, created_by_user_id=user.id, updated_by_user_id=user.id)
        db.add(payment)
        db.flush()
    item = PaymentItem(id=str(uuid4()), payment_id=payment.id, quantity=payload.quantity, unit_amount=payload.unit_amount, amount=payload.quantity * payload.unit_amount, note=payload.note, created_by_user_id=user.id)
    db.add(item)
    payment.updated_by_user_id = user.id
    db.commit()
    return payment_view(db, order)
