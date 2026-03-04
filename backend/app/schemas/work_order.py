from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class WorkOrderCreate(BaseModel):
    customer_id: int
    subscription_id: Optional[int] = None
    order_type: str  # NEW_INSTALL, REPAIR, DISMANTLE, RELOCATION
    assigned_technician: Optional[str] = None
    technician_phone: Optional[str] = None
    scheduled_date: Optional[str] = None  # ISO datetime string
    odp_port_info: Optional[str] = None
    notes: Optional[str] = None


class WorkOrderUpdate(BaseModel):
    order_type: Optional[str] = None
    status: Optional[str] = None
    assigned_technician: Optional[str] = None
    technician_phone: Optional[str] = None
    scheduled_date: Optional[str] = None
    odp_port_info: Optional[str] = None
    signal_dbm_measured: Optional[float] = None
    gps_lat_completed: Optional[float] = None
    gps_lng_completed: Optional[float] = None
    notes: Optional[str] = None


class WorkOrderAssign(BaseModel):
    assigned_technician: str
    technician_phone: Optional[str] = None
    scheduled_date: Optional[str] = None


class WorkOrderComplete(BaseModel):
    signal_dbm_measured: Optional[float] = None
    gps_lat_completed: Optional[float] = None
    gps_lng_completed: Optional[float] = None
    photo_proof_path: Optional[str] = None
    signature_path: Optional[str] = None
    notes: Optional[str] = None


class WorkOrderOut(BaseModel):
    id: int
    ewo_number: str
    customer_id: int
    subscription_id: Optional[int]
    order_type: str
    status: str
    assigned_technician: Optional[str]
    technician_phone: Optional[str]
    scheduled_date: Optional[datetime]
    odp_port_info: Optional[str]
    signal_dbm_measured: Optional[float]
    gps_lat_completed: Optional[float]
    gps_lng_completed: Optional[float]
    photo_proof_path: Optional[str]
    signature_path: Optional[str]
    completed_at: Optional[datetime]
    notes: Optional[str]
    created_at: Optional[datetime]

    # Joined fields
    customer_name: Optional[str] = None

    class Config:
        from_attributes = True
