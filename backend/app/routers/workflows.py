from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.dashboard import (
    WorkflowInbound, WorkflowTransfer, WorkflowDeploy,
    WorkflowDismantle, WorkflowReturn, WorkflowRMA,
)
from app.services import workflow_service
from app.services.bulk_import import process_bulk_import

router = APIRouter(prefix="/api/workflows", tags=["Workflows"])


@router.post("/inbound")
def workflow_inbound(data: WorkflowInbound, db: Session = Depends(get_db)):
    device = workflow_service.inbound(db, data)
    return {"detail": "Inbound successful", "device_id": device.id, "serial_number": device.serial_number}


@router.post("/transfer")
def workflow_transfer(data: WorkflowTransfer, db: Session = Depends(get_db)):
    device = workflow_service.transfer(db, data)
    return {"detail": "Transfer successful", "device_id": device.id, "serial_number": device.serial_number}


@router.post("/deploy")
def workflow_deploy(data: WorkflowDeploy, db: Session = Depends(get_db)):
    device = workflow_service.deploy(db, data)
    return {
        "detail": "Deployment successful",
        "device_id": device.id,
        "serial_number": device.serial_number,
        "purpose": device.deployment_purpose,
    }


@router.post("/dismantle")
def workflow_dismantle(data: WorkflowDismantle, db: Session = Depends(get_db)):
    device = workflow_service.dismantle(db, data)
    return {"detail": "Dismantle successful", "device_id": device.id, "serial_number": device.serial_number}


@router.post("/return")
def workflow_return(data: WorkflowReturn, db: Session = Depends(get_db)):
    device = workflow_service.return_device(db, data)
    return {"detail": "Return successful", "device_id": device.id, "serial_number": device.serial_number}


@router.post("/rma")
def workflow_rma(data: WorkflowRMA, db: Session = Depends(get_db)):
    device = workflow_service.rma(db, data)
    return {"detail": "RMA successful", "device_id": device.id, "serial_number": device.serial_number}


@router.post("/bulk-import")
def workflow_bulk_import(
    file: UploadFile = File(...),
    location_id: int = Form(...),
    db: Session = Depends(get_db),
):
    result = process_bulk_import(db, file, location_id)
    return result
