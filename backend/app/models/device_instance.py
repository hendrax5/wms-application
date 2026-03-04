from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class DeviceInstance(Base):
    """A single physical device unit tracked by serial number through its lifecycle."""

    __tablename__ = "device_instances"

    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("device_models.id"), nullable=False)

    # Unique identity
    serial_number = Column(String, unique=True, nullable=False, index=True)
    mac_address = Column(String, nullable=True)

    # Current position
    current_location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)

    # Customer assignment (who received this device)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)

    # Lifecycle status
    status = Column(String, nullable=False, default="NEW", index=True)
    # NEW, AVAILABLE, DEPLOYED, FAULTY, RMA, SCRAPPED
    condition = Column(String, nullable=False, default="GOOD")
    # GOOD, DAMAGED

    # Deployment purpose — filled when device leaves warehouse
    deployment_purpose = Column(String, nullable=True)
    # INSTALLED (dipasang, milik perusahaan), LOANED (dipinjamkan), SOLD (dijual)

    # Procurement info
    purchase_date = Column(DateTime, nullable=True)
    warranty_expiry = Column(DateTime, nullable=True)
    notes = Column(String, nullable=True)

    # Audit
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_updated = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                          onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    model = relationship("DeviceModel", back_populates="instances")
    current_location = relationship("Location", back_populates="devices_here")
    customer = relationship("Customer", back_populates="device_instances")
    movement_logs = relationship("MovementLog", back_populates="device_instance",
                                 order_by="MovementLog.timestamp.desc()")
