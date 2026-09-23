from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import INITIAL_ADMIN_PASSWORD, INITIAL_ADMIN_USERNAME
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.customer import Customer
from app.models.settings import Setting
from app.models.user import User


def seed_system_data() -> None:
    db: Session = SessionLocal()
    try:
        existing_admin = db.query(User).filter(User.username == INITIAL_ADMIN_USERNAME).first()
        if existing_admin is None:
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

        existing_guest = db.query(Customer).filter(Customer.name == "游客").first()
        if existing_guest is None:
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

        settings = {
            "auto_return_after_minutes": "120",
            "business_timezone": "Asia/Shanghai",
            "daily_forced_return_start": "23:59:01",
            "daily_forced_return_end": "23:59:59",
        }
        for key, value in settings.items():
            if db.query(Setting).filter(Setting.key == key).first() is None:
                db.add(
                    Setting(
                        id=str(uuid4()),
                        key=key,
                        value=value,
                    )
                )

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
