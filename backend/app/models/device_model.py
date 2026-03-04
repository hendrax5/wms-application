from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, JSON, DateTime
from sqlalchemy.orm import relationship

from app.database import Base


class DeviceModel(Base):
    """Master data for device types (e.g. Juniper MX204, Huawei NE40E)."""

    __tablename__ = "device_models"

    id = Column(Integer, primary_key=True, index=True)
    brand = Column(String, nullable=False, index=True)       # Juniper, Huawei, Mikrotik
    model_name = Column(String, nullable=False)               # MX204, CCR1036
    category = Column(String, nullable=False, index=True)     # ROUTER, SWITCH, MODEM, ONT, OLT, AP, OTHER
    specifications = Column(JSON, nullable=True)              # {"ports": 4, "power": "AC", ...}
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    instances = relationship("DeviceInstance", back_populates="model")
