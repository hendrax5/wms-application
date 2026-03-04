from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Invoice(Base):
    """Billing invoice with pro-rata support for ISP subscriptions."""

    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String, unique=True, nullable=False, index=True)  # INV-2026-000001

    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)

    billing_period_start = Column(DateTime, nullable=False)
    billing_period_end = Column(DateTime, nullable=False)

    amount = Column(Float, nullable=False)
    pro_rata_days = Column(Integer, nullable=True)  # null = full month

    status = Column(String, nullable=False, default="DRAFT", index=True)
    # DRAFT, SENT, PAID, OVERDUE, CANCELLED

    due_date = Column(DateTime, nullable=False)
    paid_at = Column(DateTime, nullable=True)
    payment_method = Column(String, nullable=True)    # CASH, TRANSFER, VA, QRIS
    payment_reference = Column(String, nullable=True)  # Reference / receipt number

    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_updated = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                          onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    subscription = relationship("Subscription", back_populates="invoices")
    customer = relationship("Customer", back_populates="invoices")
