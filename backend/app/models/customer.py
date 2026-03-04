from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship

from app.database import Base


class Customer(Base):
    """Customer/company that receives devices and ISP subscriptions."""

    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    customer_number = Column(String, unique=True, nullable=True, index=True)  # ISP-XXXXXXXX (auto)

    name = Column(String, nullable=False)                     # Nama kontak / PIC
    company = Column(String, nullable=True)                   # Nama perusahaan
    customer_type = Column(String, nullable=False, default="CORPORATE")  # CORPORATE, RESIDENTIAL, INTERNAL
    contact_phone = Column(String, nullable=True)
    contact_email = Column(String, nullable=True)
    address = Column(String, nullable=True)

    # E-KYC fields
    ktp_number = Column(String, nullable=True)
    ktp_photo_path = Column(String, nullable=True)

    # GPS location tagging
    gps_latitude = Column(Float, nullable=True)
    gps_longitude = Column(Float, nullable=True)
    coverage_zone = Column(String, nullable=True)             # Resolved from GPS coordinates

    registration_date = Column(DateTime, nullable=True)

    notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    locations = relationship("Location", back_populates="customer")
    device_instances = relationship("DeviceInstance", back_populates="customer")
    subscriptions = relationship("Subscription", back_populates="customer")
    work_orders = relationship("WorkOrder", back_populates="customer")
    invoices = relationship("Invoice", back_populates="customer")
