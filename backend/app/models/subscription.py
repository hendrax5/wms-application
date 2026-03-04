from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.database import Base


class Subscription(Base):
    """Links a customer to a service plan and their ONT device (PPPoE account)."""

    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)

    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    service_plan_id = Column(Integer, ForeignKey("service_plans.id"), nullable=False)
    device_instance_id = Column(Integer, ForeignKey("device_instances.id"), nullable=True)  # ONT

    # PPPoE credentials
    pppoe_username = Column(String, unique=True, nullable=True, index=True)
    pppoe_password = Column(String, nullable=True)

    # ONT binding (security — Caller-ID)
    ont_serial_number = Column(String, nullable=True, index=True)
    ont_mac_address = Column(String, nullable=True)

    # OLT placement info
    olt_info = Column(JSON, nullable=True)
    # {"host": "...", "rack": 1, "shelf": 1, "slot": 3, "port": 1, "onu_index": 5}

    # Physical layer
    odp_info = Column(String, nullable=True)        # ODP-JKT-041 / Port 05
    signal_dbm = Column(Float, nullable=True)       # Optical power reading

    # Lifecycle
    status = Column(String, nullable=False, default="PENDING", index=True)
    # PENDING, ACTIVE, ISOLATED, SUSPENDED, TERMINATED

    activation_date = Column(DateTime, nullable=True)
    termination_date = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_updated = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                          onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    customer = relationship("Customer", back_populates="subscriptions")
    service_plan = relationship("ServicePlan", back_populates="subscriptions")
    device_instance = relationship("DeviceInstance", backref="subscription_link")
    work_orders = relationship("WorkOrder", back_populates="subscription")
    invoices = relationship("Invoice", back_populates="subscription")
