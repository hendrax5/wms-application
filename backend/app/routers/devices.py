from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.device_instance import DeviceInstance
from app.models.movement_log import MovementLog
from app.schemas.device_instance import DeviceInstanceRead, DeviceInstanceUpdate
from app.schemas.movement_log import MovementLogRead
from app.services.qrcode_service import generate_qr_code

router = APIRouter(prefix="/api/devices", tags=["Devices"])


def _to_read(d: DeviceInstance) -> DeviceInstanceRead:
    """Convert DeviceInstance ORM object to Pydantic read schema with joined fields."""
    r = DeviceInstanceRead.model_validate(d)
    r.model_brand = d.model.brand if d.model else None
    r.model_name = d.model.model_name if d.model else None
    r.model_category = d.model.category if d.model else None
    r.location_name = d.current_location.name if d.current_location else None
    r.customer_name = d.customer.name if d.customer else None
    return r


@router.get("/", response_model=list[DeviceInstanceRead])
def list_devices(
    status: str | None = None,
    condition: str | None = None,
    deployment_purpose: str | None = None,
    location_id: int | None = None,
    customer_id: int | None = None,
    model_id: int | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(DeviceInstance).options(
        joinedload(DeviceInstance.model),
        joinedload(DeviceInstance.current_location),
        joinedload(DeviceInstance.customer),
    )
    if status:
        query = query.filter(DeviceInstance.status == status)
    if condition:
        query = query.filter(DeviceInstance.condition == condition)
    if deployment_purpose:
        query = query.filter(DeviceInstance.deployment_purpose == deployment_purpose)
    if location_id:
        from app.models.location import Location
        # Find all child locations of this location_id
        child_locs = db.query(Location.id).filter(Location.parent_id == location_id).all()
        child_ids = [r[0] for r in child_locs]
        all_target_locs = [location_id] + child_ids
        query = query.filter(DeviceInstance.current_location_id.in_(all_target_locs))
    if customer_id:
        query = query.filter(DeviceInstance.customer_id == customer_id)
    if model_id:
        query = query.filter(DeviceInstance.model_id == model_id)
    if search:
        query = query.filter(
            (DeviceInstance.serial_number.ilike(f"%{search}%")) |
            (DeviceInstance.mac_address.ilike(f"%{search}%"))
        )

    devices = query.order_by(DeviceInstance.last_updated.desc()).all()
    return [_to_read(d) for d in devices]


@router.get("/{device_id}", response_model=DeviceInstanceRead)
def get_device(device_id: int, db: Session = Depends(get_db)):
    d = db.query(DeviceInstance).options(
        joinedload(DeviceInstance.model),
        joinedload(DeviceInstance.current_location),
        joinedload(DeviceInstance.customer),
    ).filter(DeviceInstance.id == device_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Device not found")
    return _to_read(d)


@router.get("/by-sn/{serial_number}", response_model=DeviceInstanceRead)
def get_device_by_sn(serial_number: str, db: Session = Depends(get_db)):
    d = db.query(DeviceInstance).options(
        joinedload(DeviceInstance.model),
        joinedload(DeviceInstance.current_location),
        joinedload(DeviceInstance.customer),
    ).filter(DeviceInstance.serial_number == serial_number).first()
    if not d:
        raise HTTPException(status_code=404, detail="Device not found")
    return _to_read(d)


@router.put("/{device_id}", response_model=DeviceInstanceRead)
def update_device(device_id: int, data: DeviceInstanceUpdate, db: Session = Depends(get_db)):
    d = db.query(DeviceInstance).options(
        joinedload(DeviceInstance.model),
        joinedload(DeviceInstance.current_location),
        joinedload(DeviceInstance.customer),
    ).filter(DeviceInstance.id == device_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Device not found")
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(d, key, val)
    db.commit()
    db.refresh(d)
    return _to_read(d)


@router.get("/{device_id}/history", response_model=list[MovementLogRead])
def get_device_history(device_id: int, db: Session = Depends(get_db)):
    logs = db.query(MovementLog).filter(
        MovementLog.device_instance_id == device_id
    ).order_by(MovementLog.timestamp.desc()).all()

    results = []
    for log in logs:
        r = MovementLogRead.model_validate(log)
        r.from_location_name = log.from_location.name if log.from_location else None
        r.to_location_name = log.to_location.name if log.to_location else None
        r.serial_number = log.device_instance.serial_number if log.device_instance else None
        r.customer_name = log.customer.name if log.customer else None
        results.append(r)
    return results


@router.get("/{device_id}/qrcode")
def get_device_qrcode(device_id: int, db: Session = Depends(get_db)):
    d = db.query(DeviceInstance).filter(DeviceInstance.id == device_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Device not found")
    return generate_qr_code(d.serial_number)
