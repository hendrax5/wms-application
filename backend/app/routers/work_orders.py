from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional

from app.database import get_db
from app.models.work_order import WorkOrder
from app.models.customer import Customer
from app.models.audit_log import AuditLog
from app.schemas.work_order import (
    WorkOrderCreate, WorkOrderUpdate, WorkOrderAssign, WorkOrderComplete, WorkOrderOut,
)

router = APIRouter(prefix="/api/work-orders", tags=["Work Orders"])


def _next_ewo_number(db: Session) -> str:
    """Generate next EWO number: EWO-YYYY-NNNNNN."""
    year = datetime.now().year
    prefix = f"EWO-{year}-"
    last = (
        db.query(WorkOrder)
        .filter(WorkOrder.ewo_number.like(f"{prefix}%"))
        .order_by(WorkOrder.id.desc())
        .first()
    )
    if last:
        seq = int(last.ewo_number.split("-")[-1]) + 1
    else:
        seq = 1
    return f"{prefix}{seq:06d}"


@router.get("", response_model=list[WorkOrderOut])
def list_work_orders(
    status: Optional[str] = Query(None),
    order_type: Optional[str] = Query(None),
    technician: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(WorkOrder)
    if status:
        q = q.filter(WorkOrder.status == status)
    if order_type:
        q = q.filter(WorkOrder.order_type == order_type)
    if technician:
        q = q.filter(WorkOrder.assigned_technician.ilike(f"%{technician}%"))

    orders = q.order_by(WorkOrder.created_at.desc()).all()

    result = []
    for wo in orders:
        out = WorkOrderOut.model_validate(wo)
        out.customer_name = wo.customer.name if wo.customer else None
        result.append(out)
    return result


@router.get("/{wo_id}", response_model=WorkOrderOut)
def get_work_order(wo_id: int, db: Session = Depends(get_db)):
    wo = db.query(WorkOrder).filter(WorkOrder.id == wo_id).first()
    if not wo:
        raise HTTPException(status_code=404, detail="Work order not found")
    out = WorkOrderOut.model_validate(wo)
    out.customer_name = wo.customer.name if wo.customer else None
    return out


@router.post("", response_model=WorkOrderOut, status_code=201)
def create_work_order(data: WorkOrderCreate, db: Session = Depends(get_db)):
    # Validate customer
    customer = db.query(Customer).filter(Customer.id == data.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    valid_types = ["NEW_INSTALL", "REPAIR", "DISMANTLE", "RELOCATION"]
    if data.order_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"order_type must be one of {valid_types}")

    ewo_number = _next_ewo_number(db)

    wo = WorkOrder(
        ewo_number=ewo_number,
        customer_id=data.customer_id,
        subscription_id=data.subscription_id,
        order_type=data.order_type,
        status="CREATED",
        assigned_technician=data.assigned_technician,
        technician_phone=data.technician_phone,
        scheduled_date=datetime.fromisoformat(data.scheduled_date) if data.scheduled_date else None,
        odp_port_info=data.odp_port_info,
        notes=data.notes,
    )

    # If technician is already assigned, set status to ASSIGNED
    if data.assigned_technician:
        wo.status = "ASSIGNED"

    db.add(wo)
    db.flush()

    db.add(AuditLog(
        actor="SYSTEM", action="CREATE", entity_type="WorkOrder", entity_id=wo.id,
        details={"ewo_number": ewo_number, "order_type": data.order_type, "customer_id": data.customer_id},
    ))
    db.commit()
    db.refresh(wo)

    out = WorkOrderOut.model_validate(wo)
    out.customer_name = customer.name
    return out


@router.put("/{wo_id}", response_model=WorkOrderOut)
def update_work_order(wo_id: int, data: WorkOrderUpdate, db: Session = Depends(get_db)):
    wo = db.query(WorkOrder).filter(WorkOrder.id == wo_id).first()
    if not wo:
        raise HTTPException(status_code=404, detail="Work order not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        if field == "scheduled_date" and value:
            value = datetime.fromisoformat(value)
        setattr(wo, field, value)
    db.commit()
    db.refresh(wo)

    out = WorkOrderOut.model_validate(wo)
    out.customer_name = wo.customer.name if wo.customer else None
    return out


@router.post("/{wo_id}/assign", response_model=WorkOrderOut)
def assign_work_order(wo_id: int, data: WorkOrderAssign, db: Session = Depends(get_db)):
    wo = db.query(WorkOrder).filter(WorkOrder.id == wo_id).first()
    if not wo:
        raise HTTPException(status_code=404, detail="Work order not found")
    if wo.status not in ("CREATED", "ASSIGNED"):
        raise HTTPException(status_code=400, detail=f"Cannot assign WO in status '{wo.status}'")

    wo.assigned_technician = data.assigned_technician
    wo.technician_phone = data.technician_phone
    wo.scheduled_date = datetime.fromisoformat(data.scheduled_date) if data.scheduled_date else wo.scheduled_date
    wo.status = "ASSIGNED"

    db.add(AuditLog(
        actor=data.assigned_technician, action="UPDATE", entity_type="WorkOrder", entity_id=wo.id,
        details={"action": "ASSIGN", "technician": data.assigned_technician},
    ))
    db.commit()
    db.refresh(wo)

    out = WorkOrderOut.model_validate(wo)
    out.customer_name = wo.customer.name if wo.customer else None
    return out


@router.post("/{wo_id}/start", response_model=WorkOrderOut)
def start_work_order(wo_id: int, db: Session = Depends(get_db)):
    wo = db.query(WorkOrder).filter(WorkOrder.id == wo_id).first()
    if not wo:
        raise HTTPException(status_code=404, detail="Work order not found")
    if wo.status != "ASSIGNED":
        raise HTTPException(status_code=400, detail=f"Cannot start WO in status '{wo.status}'")

    wo.status = "IN_PROGRESS"
    db.commit()
    db.refresh(wo)

    out = WorkOrderOut.model_validate(wo)
    out.customer_name = wo.customer.name if wo.customer else None
    return out


@router.post("/{wo_id}/complete", response_model=WorkOrderOut)
def complete_work_order(wo_id: int, data: WorkOrderComplete, db: Session = Depends(get_db)):
    wo = db.query(WorkOrder).filter(WorkOrder.id == wo_id).first()
    if not wo:
        raise HTTPException(status_code=404, detail="Work order not found")
    if wo.status != "IN_PROGRESS":
        raise HTTPException(status_code=400, detail=f"Cannot complete WO in status '{wo.status}'")

    # Optical signal validation: reject if signal is worse than -27 dBm
    if data.signal_dbm_measured is not None and data.signal_dbm_measured < -27.0:
        raise HTTPException(
            status_code=400,
            detail=f"Signal too weak ({data.signal_dbm_measured} dBm). Must be > -27 dBm to complete installation."
        )

    wo.signal_dbm_measured = data.signal_dbm_measured
    wo.gps_lat_completed = data.gps_lat_completed
    wo.gps_lng_completed = data.gps_lng_completed
    wo.photo_proof_path = data.photo_proof_path
    wo.signature_path = data.signature_path
    wo.notes = data.notes or wo.notes
    wo.status = "COMPLETED"
    wo.completed_at = datetime.now(timezone.utc)

    db.add(AuditLog(
        actor=wo.assigned_technician or "SYSTEM",
        action="UPDATE", entity_type="WorkOrder", entity_id=wo.id,
        details={"action": "COMPLETE", "signal_dbm": data.signal_dbm_measured},
    ))
    db.commit()
    db.refresh(wo)

    out = WorkOrderOut.model_validate(wo)
    out.customer_name = wo.customer.name if wo.customer else None
    return out
