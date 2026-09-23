from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.db.session import get_db
from app.models.customer import Customer
from app.models.user import User

router = APIRouter(prefix="/api/customers", tags=["customers"])


class CustomerInput(BaseModel):
    name: str | None = None
    gender: str | None = None
    wechat_nickname: str | None = None
    wechat_id: str | None = None
    phone: str | None = None

    @model_validator(mode="after")
    def validate_identity(self):
        if not ((self.name and self.phone) or (self.wechat_nickname and self.wechat_id)):
            raise ValueError("name+phone or wechat_nickname+wechat_id is required")
        return self


def serialize_customer(customer: Customer) -> dict:
    return {
        "id": customer.id,
        "name": customer.name,
        "gender": customer.gender,
        "wechat_nickname": customer.wechat_nickname,
        "wechat_id": customer.wechat_id,
        "phone": customer.phone,
    }


@router.get("")
def list_customers(q: str | None = None, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    query = select(Customer).order_by(Customer.updated_at.desc())
    if q:
        term = f"%{q}%"
        query = query.where(
            or_(
                Customer.name.ilike(term),
                Customer.wechat_nickname.ilike(term),
                Customer.wechat_id.ilike(term),
                Customer.phone.ilike(term),
            )
        )
    return [serialize_customer(c) for c in db.scalars(query).all()]


@router.post("")
def create_customer(payload: CustomerInput, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    if payload.phone and db.scalar(select(Customer).where(Customer.phone == payload.phone)):
        raise HTTPException(status_code=409, detail="phone already exists")
    if payload.wechat_id and db.scalar(select(Customer).where(Customer.wechat_id == payload.wechat_id)):
        raise HTTPException(status_code=409, detail="wechat_id already exists")

    customer = Customer(id=str(uuid4()), **payload.model_dump())
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return serialize_customer(customer)
