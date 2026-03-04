from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.database import Base


class WorkOrder(Base):
    """Digital E-Work Order (EWO) — technician task assignment for field operations."""

    __tablename__ = "work_orders"

    id = Column(Integer, primary_key=True, index=True)
    ewo_number = Column(String, unique=True, nullable=False, index=True)  # EWO-2026-000001

    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=True)

    order_type = Column(String, nullable=False, index=True)
    # NEW_INSTALL, REPAIR, DISMANTLE, RELOCATION

    status = Column(String, nullable=False, default="CREATED", index=True)
    # CREATED, ASSIGNED, IN_PROGRESS, COMPLETED, CANCELLED

    # Technician assignment
    assigned_technician = Column(String, nullable=True)
    technician_phone = Column(String, nullable=True)
    scheduled_date = Column(DateTime, nullable=True)

    # Field data
    odp_port_info = Column(String, nullable=True)      # ODP-JKT-041 / Port 05
    signal_dbm_measured = Column(Float, nullable=True)  # Technician's measurement

    # Geofencing validation
    gps_lat_completed = Column(Float, nullable=True)
    gps_lng_completed = Column(Float, nullable=True)

    # Evidence
    photo_proof_path = Column(String, nullable=True)
    signature_path = Column(String, nullable=True)

    completed_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_updated = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                          onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    customer = relationship("Customer", back_populates="work_orders")
    subscription = relationship("Subscription", back_populates="work_orders")
