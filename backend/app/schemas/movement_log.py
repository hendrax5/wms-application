from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class MovementLogRead(BaseModel):
    id: int
    device_instance_id: int
    from_location_id: Optional[int] = None
    to_location_id: int
    activity_type: str
    deployment_purpose: Optional[str] = None
    customer_id: Optional[int] = None
    reference_doc: Optional[str] = None
    technician_name: Optional[str] = None
    notes: Optional[str] = None
    timestamp: Optional[datetime] = None

    # Joined fields
    from_location_name: Optional[str] = None
    to_location_name: Optional[str] = None
    serial_number: Optional[str] = None
    customer_name: Optional[str] = None

    class Config:
        from_attributes = True
