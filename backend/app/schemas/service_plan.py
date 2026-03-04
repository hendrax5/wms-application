from pydantic import BaseModel
from typing import Optional


class ServicePlanCreate(BaseModel):
    name: str
    speed_down_mbps: int
    speed_up_mbps: int
    monthly_price: float
    vlan_id: Optional[int] = None
    olt_profile_name: Optional[str] = None
    mikrotik_group: Optional[str] = None
    framed_pool: Optional[str] = None
    is_active: bool = True


class ServicePlanUpdate(BaseModel):
    name: Optional[str] = None
    speed_down_mbps: Optional[int] = None
    speed_up_mbps: Optional[int] = None
    monthly_price: Optional[float] = None
    vlan_id: Optional[int] = None
    olt_profile_name: Optional[str] = None
    mikrotik_group: Optional[str] = None
    framed_pool: Optional[str] = None
    is_active: Optional[bool] = None


class ServicePlanOut(BaseModel):
    id: int
    name: str
    speed_down_mbps: int
    speed_up_mbps: int
    monthly_price: float
    vlan_id: Optional[int]
    olt_profile_name: Optional[str]
    mikrotik_group: Optional[str]
    framed_pool: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True
