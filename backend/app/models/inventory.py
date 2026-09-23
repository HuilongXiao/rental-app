from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class InventoryConfiguration(Base):
    __tablename__ = "inventory_configurations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)
    equipment_spec_id: Mapped[str] = mapped_column(String(36), ForeignKey("equipment_specs.id"), unique=True, nullable=False, index=True)
    total_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    updated_by_user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
