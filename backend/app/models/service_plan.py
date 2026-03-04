from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.orm import relationship

from app.database import Base


class ServicePlan(Base):
    """Internet service package master data (e.g. Home Pro 50Mbps)."""

    __tablename__ = "service_plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)          # Home Pro 50Mbps
    speed_down_mbps = Column(Integer, nullable=False)           # 50
    speed_up_mbps = Column(Integer, nullable=False)             # 25

    monthly_price = Column(Float, nullable=False)               # 350000.0 (IDR)

    # Network mapping
    vlan_id = Column(Integer, nullable=True)                    # VLAN for this plan
    olt_profile_name = Column(String, nullable=True)            # ZTE T-CONT profile name
    mikrotik_group = Column(String, nullable=True)              # Radius Mikrotik-Group value
    framed_pool = Column(String, nullable=True)                 # Radius Framed-Pool value

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    subscriptions = relationship("Subscription", back_populates="service_plan")
