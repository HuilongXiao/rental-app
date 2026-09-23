from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import INITIAL_ADMIN_PASSWORD, INITIAL_ADMIN_USERNAME
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.customer import Customer
from app.models.equipment import EquipmentSpec, EquipmentType, SaleItem
from app.models.inventory import InventoryConfiguration
from app.models.settings import Setting
from app.models.user import User


def seed_system_data() -> None:
    db: Session = SessionLocal()
    try:
        admin_exists = db.query(User).filter(User.username == INITIAL_ADMIN_USERNAME).first()
        if admin_exists is None:
            db.add(
                User(
                    id=str(uuid4()),
                    username=INITIAL_ADMIN_USERNAME,
                    display_name="Administrator",
                    password_hash=hash_password(INITIAL_ADMIN_PASSWORD),
                    is_active=True,
                    is_system=True,
                )
            )

        guest_exists = db.query(Customer).filter(Customer.name == "游客").first()
        if guest_exists is None:
            db.add(
                Customer(
                    id=str(uuid4()),
                    name="游客",
                    gender=None,
                    wechat_nickname=None,
                    wechat_id="system_customer_guest",
                    phone=None,
                )
            )

        if db.query(EquipmentType).count() == 0:
            type_lantern = EquipmentType(id=str(uuid4()), name="灯具")
            type_tent = EquipmentType(id=str(uuid4()), name="帐篷")
            db.add_all([type_lantern, type_tent])
            db.flush()

            db.add_all(
                [
                    EquipmentSpec(id=str(uuid4()), equipment_type_id=type_lantern.id, name="LED 灯组", price=2000, capacity=3, is_active=True),
                    EquipmentSpec(id=str(uuid4()), equipment_type_id=type_tent.id, name="双人帐篷", price=5000, capacity=2, is_active=True),
                ]
            )
            db.flush()

            for item in db.query(EquipmentSpec).all():
                if db.query(InventoryConfiguration).filter(InventoryConfiguration.equipment_spec_id == item.id).count() == 0:
                    db.add(InventoryConfiguration(id=str(uuid4()), equipment_spec_id=item.id, total_quantity=3))

        if db.query(SaleItem).count() == 0:
            db.add_all(
                [
                    SaleItem(id=str(uuid4()), name="场地清洁服务", price=3000, is_active=True),
                    SaleItem(id=str(uuid4()), name="外送服务", price=1500, is_active=True),
                ]
            )

        default_settings = {
            "auto_return_after_minutes": "120",
            "business_timezone": "Asia/Shanghai",
            "daily_forced_return_start": "23:59:01",
            "daily_forced_return_end": "23:59:59",
        }
        for key, value in default_settings.items():
            if db.query(Setting).filter(Setting.key == key).first() is None:
                db.add(Setting(id=str(uuid4()), key=key, value=value))

        db.commit()
    finally:
        db.close()


def check_database_connection() -> bool:
    try:
        with SessionLocal() as session:
            session.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
