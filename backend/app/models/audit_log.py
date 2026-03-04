from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime, JSON, Text

from app.database import Base


class AuditLog(Base):
    """Immutable system-wide audit trail — every critical action is logged here."""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    actor = Column(String, nullable=False)              # username or "SYSTEM"
    action = Column(String, nullable=False, index=True)  # CREATE, UPDATE, DELETE, PROVISION, ISOLATE, RECONNECT

    entity_type = Column(String, nullable=False)        # Customer, Subscription, WorkOrder, Invoice, etc.
    entity_id = Column(Integer, nullable=True)

    details = Column(JSON, nullable=True)               # Arbitrary JSON payload with action details
    ip_address = Column(String, nullable=True)

    notes = Column(Text, nullable=True)
