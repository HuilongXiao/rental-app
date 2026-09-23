from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, model_validator
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
        "created_at": customer.created_at,
        "updated_at": customer.updated_at,
    }


def ensure_unique_identity(db: Session, payload: CustomerInput, exclude_id: str | None = None) -> None:
    predicates = []
    if payload.phone:
        predicates.append(Customer.phone == payload.phone)
    if payload.wechat_id:
        predicates.append(Customer.wechat_id == payload.wechat_id)
    if not predicates:
        return
    query = select(Customer).where(or_(*predicates))
    if exclude_id:
        query = query.where(Customer.id != exclude_id)
    if db.scalar(query):
        raise HTTPException(status_code=409, detail="phone or wechat_id already exists")


@router.get("")
def list_customers(q: str | None = None, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    query = select(Customer).order_by(Customer.updated_at.desc())
    if q:
        term = f"%{q}%"
        query = query.where(or_(Customer.name.ilike(term), Customer.wechat_nickname.ilike(term), Customer.wechat_id.ilike(term), Customer.phone.ilike(term)))
    return [serialize_customer(customer) for customer in db.scalars(query).all()]


@router.get("/{customer_id}")
def get_customer(customer_id: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    customer = db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="customer not found")
    return serialize_customer(customer)


@router.post("")
def create_customer(payload: CustomerInput, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    ensure_unique_identity(db, payload)
    customer = Customer(id=str(uuid4()), **payload.model_dump())
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return serialize_customer(customer)


@router.put("/{customer_id}")
def update_customer(customer_id: str, payload: CustomerInput, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    customer = db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="customer not found")
    ensure_unique_identity(db, payload, exclude_id=customer_id)
    for key, value in payload.model_dump().items():
        setattr(customer, key, value)
    db.commit()
    db.refresh(customer)
    return serialize_customer(customer)
