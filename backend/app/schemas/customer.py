from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class CustomerCreate(BaseModel):
    name: str
    company: Optional[str] = None
    customer_type: str = "CORPORATE"  # CORPORATE, RESIDENTIAL, INTERNAL
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    address: Optional[str] = None
    ktp_number: Optional[str] = None
    gps_latitude: Optional[float] = None
    gps_longitude: Optional[float] = None
    coverage_zone: Optional[str] = None
    notes: Optional[str] = None


class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    company: Optional[str] = None
    customer_type: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    address: Optional[str] = None
    ktp_number: Optional[str] = None
    ktp_photo_path: Optional[str] = None
    gps_latitude: Optional[float] = None
    gps_longitude: Optional[float] = None
    coverage_zone: Optional[str] = None
    notes: Optional[str] = None


class CustomerRead(BaseModel):
    id: int
    customer_number: Optional[str] = None
    name: str
    company: Optional[str] = None
    customer_type: str
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    address: Optional[str] = None
    ktp_number: Optional[str] = None
    ktp_photo_path: Optional[str] = None
    gps_latitude: Optional[float] = None
    gps_longitude: Optional[float] = None
    coverage_zone: Optional[str] = None
    registration_date: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

