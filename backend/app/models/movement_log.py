from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class MovementLog(Base):
    """Immutable log of every device movement — never deleted, only appended."""

    __tablename__ = "movement_logs"

    id = Column(Integer, primary_key=True, index=True)
    device_instance_id = Column(Integer, ForeignKey("device_instances.id"), nullable=False)

    from_location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)   # null for inbound
    to_location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)

    activity_type = Column(String, nullable=False, index=True)
    # INBOUND, TRANSFER, DEPLOY, DISMANTLE, RETURN, RMA, SCRAP

    # Snapshot of purpose at time of movement
    deployment_purpose = Column(String, nullable=True)
    # INSTALLED, LOANED, SOLD

    # Who received the device (snapshot)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)

    reference_doc = Column(String, nullable=True)   # No. Surat Jalan / Tiket
    technician_name = Column(String, nullable=True)
    notes = Column(String, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    device_instance = relationship("DeviceInstance", back_populates="movement_logs")
    from_location = relationship("Location", foreign_keys=[from_location_id])
    to_location = relationship("Location", foreign_keys=[to_location_id])
    customer = relationship("Customer")
