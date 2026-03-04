from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class DeviceModelCreate(BaseModel):
    brand: str
    model_name: str
    category: str  # ROUTER, SWITCH, MODEM, ONT, OLT, AP, OTHER
    specifications: Optional[dict] = None


class DeviceModelUpdate(BaseModel):
    brand: Optional[str] = None
    model_name: Optional[str] = None
    category: Optional[str] = None
    specifications: Optional[dict] = None


class DeviceModelRead(BaseModel):
    id: int
    brand: str
    model_name: str
    category: str
    specifications: Optional[dict] = None
    created_at: Optional[datetime] = None
    instance_count: Optional[int] = 0

    class Config:
        from_attributes = True
