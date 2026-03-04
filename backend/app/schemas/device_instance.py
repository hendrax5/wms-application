from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class DeviceInstanceCreate(BaseModel):
    model_id: int
    serial_number: str
    mac_address: Optional[str] = None
    current_location_id: Optional[int] = None
    purchase_date: Optional[datetime] = None
    warranty_expiry: Optional[datetime] = None
    notes: Optional[str] = None


class DeviceInstanceUpdate(BaseModel):
    mac_address: Optional[str] = None
    notes: Optional[str] = None
    purchase_date: Optional[datetime] = None
    warranty_expiry: Optional[datetime] = None


class DeviceInstanceRead(BaseModel):
    id: int
    model_id: int
    serial_number: str
    mac_address: Optional[str] = None
    current_location_id: Optional[int] = None
    customer_id: Optional[int] = None
    status: str
    condition: str
    deployment_purpose: Optional[str] = None
    purchase_date: Optional[datetime] = None
    warranty_expiry: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    last_updated: Optional[datetime] = None

    # Joined fields for display
    model_brand: Optional[str] = None
    model_name: Optional[str] = None
    model_category: Optional[str] = None
    location_name: Optional[str] = None
    customer_name: Optional[str] = None

    class Config:
        from_attributes = True
