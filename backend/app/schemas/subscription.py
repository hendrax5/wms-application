from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class SubscriptionCreate(BaseModel):
    customer_id: int
    service_plan_id: int
    device_instance_id: Optional[int] = None
    pppoe_username: Optional[str] = None
    pppoe_password: Optional[str] = None
    ont_serial_number: Optional[str] = None
    ont_mac_address: Optional[str] = None
    olt_info: Optional[dict] = None
    odp_info: Optional[str] = None
    signal_dbm: Optional[float] = None


class SubscriptionUpdate(BaseModel):
    service_plan_id: Optional[int] = None
    device_instance_id: Optional[int] = None
    pppoe_username: Optional[str] = None
    pppoe_password: Optional[str] = None
    ont_serial_number: Optional[str] = None
    ont_mac_address: Optional[str] = None
    olt_info: Optional[dict] = None
    odp_info: Optional[str] = None
    signal_dbm: Optional[float] = None
    status: Optional[str] = None


class SubscriptionOut(BaseModel):
    id: int
    customer_id: int
    service_plan_id: int
    device_instance_id: Optional[int]
    pppoe_username: Optional[str]
    ont_serial_number: Optional[str]
    ont_mac_address: Optional[str]
    olt_info: Optional[dict]
    odp_info: Optional[str]
    signal_dbm: Optional[float]
    status: str
    activation_date: Optional[datetime]
    termination_date: Optional[datetime]
    created_at: Optional[datetime]

    # Joined fields
    customer_name: Optional[str] = None
    plan_name: Optional[str] = None

    class Config:
        from_attributes = True


class ProvisionActivateRequest(BaseModel):
    subscription_id: int
    actor: str = "SYSTEM"


class ProvisionIsolateRequest(BaseModel):
    subscription_id: int
    reason: str = "OVERDUE_PAYMENT"
    actor: str = "SYSTEM"


class ProvisionReconnectRequest(BaseModel):
    subscription_id: int
    actor: str = "SYSTEM"
