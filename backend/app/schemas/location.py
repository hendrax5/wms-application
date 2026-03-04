from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class LocationCreate(BaseModel):
    name: str
    type: str  # HEAD_OFFICE, BRANCH, SITE, TECHNICIAN, REPAIR_CENTER
    address: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    pic_name: Optional[str] = None
    pic_phone: Optional[str] = None
    customer_id: Optional[int] = None
    parent_id: Optional[int] = None
    notes: Optional[str] = None


class LocationUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    pic_name: Optional[str] = None
    pic_phone: Optional[str] = None
    customer_id: Optional[int] = None
    parent_id: Optional[int] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class LocationRead(BaseModel):
    id: int
    name: str
    type: str
    address: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    pic_name: Optional[str] = None
    pic_phone: Optional[str] = None
    customer_id: Optional[int] = None
    customer_name: Optional[str] = None
    parent_id: Optional[int] = None
    parent_name: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    device_count: Optional[int] = 0

    class Config:
        from_attributes = True
