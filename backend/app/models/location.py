from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class Location(Base):
    """Fully registered location — warehouses, branches, customer sites, technician bags."""

    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)                               # Gudang Jakarta, POP Surabaya
    type = Column(String, nullable=False, index=True)                   # HEAD_OFFICE, BRANCH, SITE, TECHNICIAN, REPAIR_CENTER
    address = Column(String, nullable=True)
    city = Column(String, nullable=True)
    province = Column(String, nullable=True)

    # GPS coordinates for map tracking
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    # Person-in-Charge at this location
    pic_name = Column(String, nullable=True)
    pic_phone = Column(String, nullable=True)

    # Link to customer (for SITE type locations)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)

    # Branch Hierarchy
    parent_id = Column(Integer, ForeignKey("locations.id"), nullable=True)

    notes = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    parent = relationship("Location", remote_side=[id], back_populates="children")
    children = relationship("Location", back_populates="parent")
    customer = relationship("Customer", back_populates="locations")
    devices_here = relationship("DeviceInstance", back_populates="current_location")
