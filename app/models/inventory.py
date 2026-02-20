"""
Inventory Models - Stock tracking
"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy import String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.extensions import db
from app.models.base import BaseModelMixin, TimestampMixin


class Inventory(db.Model, BaseModelMixin, TimestampMixin):
    """Tracks stock levels for parts per tenant"""

    __tablename__ = 'inventory'

    # Transaction type constants (used by InventoryTransaction)
    TX_RECEIVED = 'received'
    TX_SOLD = 'sold'
    TX_ADJUSTED = 'adjusted'
    TX_RETURNED = 'returned'

    inventory_id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('tenant.tenant_id'), nullable=False, index=True
    )
    part_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('part.part_id'), nullable=False
    )
    quantity_on_hand: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reorder_level: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reorder_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    location: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant")
    part: Mapped["Part"] = relationship("Part")
    transactions: Mapped[List["InventoryTransaction"]] = relationship(
        "InventoryTransaction", back_populates="inventory", lazy="dynamic"
    )

    @property
    def needs_reorder(self) -> bool:
        """Check if stock is at or below reorder level"""
        return self.quantity_on_hand <= self.reorder_level

    def __repr__(self) -> str:
        return f"<Inventory part={self.part_id} qty={self.quantity_on_hand}>"


class InventoryTransaction(db.Model, BaseModelMixin):
    """Records individual stock movements"""

    __tablename__ = 'inventory_transaction'

    VALID_TYPES = ['received', 'sold', 'adjusted', 'returned']

    transaction_id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('tenant.tenant_id'), nullable=False, index=True
    )
    inventory_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('inventory.inventory_id'), nullable=False
    )
    transaction_type: Mapped[str] = mapped_column(String(20), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    reference_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    reference_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    performed_by: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey('user.user_id'), nullable=True
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    # Relationships
    inventory: Mapped["Inventory"] = relationship(
        "Inventory", back_populates="transactions"
    )
    performer: Mapped[Optional["User"]] = relationship("User")

    def __repr__(self) -> str:
        return f"<InventoryTransaction {self.transaction_type} qty={self.quantity}>"
