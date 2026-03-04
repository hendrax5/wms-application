from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.device_instance import DeviceInstance
from app.models.movement_log import MovementLog
from app.models.location import Location
from app.schemas.dashboard import (
    WorkflowInbound, WorkflowTransfer, WorkflowDeploy,
    WorkflowDismantle, WorkflowReturn, WorkflowRMA,
)


def _validate_device(db: Session, device_id: int, expected_statuses: list[str] | None = None) -> DeviceInstance:
    """Fetch device and validate its status."""
    device = db.query(DeviceInstance).filter(DeviceInstance.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail=f"Device instance #{device_id} not found")
    if expected_statuses and device.status not in expected_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Device SN {device.serial_number} has status '{device.status}', expected one of {expected_statuses}"
        )
    return device


def _validate_location(db: Session, location_id: int) -> Location:
    """Fetch and validate location exists and is active."""
    loc = db.query(Location).filter(Location.id == location_id).first()
    if not loc:
        raise HTTPException(status_code=404, detail=f"Location #{location_id} not found")
    if not loc.is_active:
        raise HTTPException(status_code=400, detail=f"Location '{loc.name}' is not active")
    return loc


def _create_log(db: Session, device: DeviceInstance, from_loc_id: int | None,
                to_loc_id: int, activity_type: str, purpose: str | None = None,
                customer_id: int | None = None, reference_doc: str | None = None,
                technician_name: str | None = None, notes: str | None = None):
    """Create an immutable movement log entry."""
    log = MovementLog(
        device_instance_id=device.id,
        from_location_id=from_loc_id,
        to_location_id=to_loc_id,
        activity_type=activity_type,
        deployment_purpose=purpose,
        customer_id=customer_id,
        reference_doc=reference_doc,
        technician_name=technician_name,
        notes=notes,
    )
    db.add(log)
    return log


# ── Workflow 1: INBOUND (Vendor → Gudang) ───────────────────────────────

def inbound(db: Session, data: WorkflowInbound) -> DeviceInstance:
    """Register a new device from vendor into warehouse."""
    # Check duplicate SN
    existing = db.query(DeviceInstance).filter(DeviceInstance.serial_number == data.serial_number).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Serial number '{data.serial_number}' already exists")

    _validate_location(db, data.location_id)

    device = DeviceInstance(
        model_id=data.model_id,
        serial_number=data.serial_number,
        mac_address=data.mac_address,
        current_location_id=data.location_id,
        status="AVAILABLE",
        condition="GOOD",
        purchase_date=datetime.fromisoformat(data.purchase_date) if data.purchase_date else None,
        warranty_expiry=datetime.fromisoformat(data.warranty_expiry) if data.warranty_expiry else None,
        notes=data.notes,
    )
    db.add(device)
    db.flush()

    _create_log(db, device, None, data.location_id, "INBOUND",
                reference_doc=data.reference_doc, technician_name=data.technician_name,
                notes=data.notes)
    db.commit()
    db.refresh(device)
    return device


# ── Workflow 2: TRANSFER (Gudang → Gudang Cabang) ───────────────────────

def transfer(db: Session, data: WorkflowTransfer) -> DeviceInstance:
    """Transfer device between warehouses. Device must be AVAILABLE."""
    device = _validate_device(db, data.device_instance_id, ["AVAILABLE"])
    _validate_location(db, data.to_location_id)

    from_loc_id = device.current_location_id
    device.current_location_id = data.to_location_id
    device.last_updated = datetime.now(timezone.utc)

    _create_log(db, device, from_loc_id, data.to_location_id, "TRANSFER",
                reference_doc=data.reference_doc, technician_name=data.technician_name,
                notes=data.notes)
    db.commit()
    db.refresh(device)
    return device


# ── Workflow 3: DEPLOY (Gudang/Cabang → Site Customer) ──────────────────

def deploy(db: Session, data: WorkflowDeploy) -> DeviceInstance:
    """Deploy device to customer site. Requires purpose and customer."""
    device = _validate_device(db, data.device_instance_id, ["AVAILABLE"])
    location = _validate_location(db, data.to_location_id)

    # Validate deployment_purpose
    valid_purposes = ["INSTALLED", "LOANED", "SOLD"]
    if data.deployment_purpose not in valid_purposes:
        raise HTTPException(
            status_code=400,
            detail=f"deployment_purpose must be one of {valid_purposes}, got '{data.deployment_purpose}'"
        )

    # Validate customer exists
    from app.models.customer import Customer
    customer = db.query(Customer).filter(Customer.id == data.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail=f"Customer #{data.customer_id} not found")

    from_loc_id = device.current_location_id
    device.current_location_id = data.to_location_id
    device.status = "DEPLOYED"
    device.deployment_purpose = data.deployment_purpose
    device.customer_id = data.customer_id
    device.last_updated = datetime.now(timezone.utc)

    _create_log(db, device, from_loc_id, data.to_location_id, "DEPLOY",
                purpose=data.deployment_purpose, customer_id=data.customer_id,
                reference_doc=data.reference_doc, technician_name=data.technician_name,
                notes=data.notes)
    db.commit()
    db.refresh(device)
    return device


# ── Workflow 4A: DISMANTLE (Copot dari Site) ─────────────────────────────

def dismantle(db: Session, data: WorkflowDismantle) -> DeviceInstance:
    """Remove device from deployed site. Sets status to FAULTY."""
    device = _validate_device(db, data.device_instance_id, ["DEPLOYED"])
    _validate_location(db, data.to_location_id)

    from_loc_id = device.current_location_id
    device.current_location_id = data.to_location_id
    device.status = "FAULTY"
    device.condition = data.condition
    device.deployment_purpose = None  # Clear purpose
    device.customer_id = None         # Clear customer assignment
    device.last_updated = datetime.now(timezone.utc)

    _create_log(db, device, from_loc_id, data.to_location_id, "DISMANTLE",
                reference_doc=data.reference_doc, technician_name=data.technician_name,
                notes=data.notes)
    db.commit()
    db.refresh(device)
    return device


# ── Workflow 4B: RETURN (Teknisi → Gudang Cabang Karantina) ──────────────

def return_device(db: Session, data: WorkflowReturn) -> DeviceInstance:
    """Return device to branch warehouse (quarantine area)."""
    device = _validate_device(db, data.device_instance_id, ["FAULTY", "DEPLOYED"])
    _validate_location(db, data.to_location_id)

    from_loc_id = device.current_location_id
    device.current_location_id = data.to_location_id
    device.last_updated = datetime.now(timezone.utc)

    _create_log(db, device, from_loc_id, data.to_location_id, "RETURN",
                reference_doc=data.reference_doc, technician_name=data.technician_name,
                notes=data.notes)
    db.commit()
    db.refresh(device)
    return device


# ── Workflow 4C: RMA (Cabang → HO / Repair Center) ──────────────────────

def rma(db: Session, data: WorkflowRMA) -> DeviceInstance:
    """Send device for RMA / repair at HO or vendor."""
    device = _validate_device(db, data.device_instance_id, ["FAULTY"])
    _validate_location(db, data.to_location_id)

    from_loc_id = device.current_location_id
    device.current_location_id = data.to_location_id
    device.status = "RMA"
    device.last_updated = datetime.now(timezone.utc)

    _create_log(db, device, from_loc_id, data.to_location_id, "RMA",
                reference_doc=data.reference_doc, technician_name=data.technician_name,
                notes=data.notes)
    db.commit()
    db.refresh(device)
    return device
