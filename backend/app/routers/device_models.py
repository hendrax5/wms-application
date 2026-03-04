from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.device_model import DeviceModel
from app.schemas.device_model import DeviceModelCreate, DeviceModelUpdate, DeviceModelRead

router = APIRouter(prefix="/api/device-models", tags=["Device Models"])


@router.get("/", response_model=list[DeviceModelRead])
def list_device_models(
    category: str | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(DeviceModel)
    if category:
        query = query.filter(DeviceModel.category == category)
    if search:
        query = query.filter(
            (DeviceModel.brand.ilike(f"%{search}%")) |
            (DeviceModel.model_name.ilike(f"%{search}%"))
        )
    models = query.order_by(DeviceModel.brand, DeviceModel.model_name).all()

    results = []
    for m in models:
        r = DeviceModelRead.model_validate(m)
        r.instance_count = len(m.instances) if m.instances else 0
        results.append(r)
    return results


@router.get("/{model_id}", response_model=DeviceModelRead)
def get_device_model(model_id: int, db: Session = Depends(get_db)):
    m = db.query(DeviceModel).filter(DeviceModel.id == model_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Device model not found")
    r = DeviceModelRead.model_validate(m)
    r.instance_count = len(m.instances) if m.instances else 0
    return r


@router.post("/", response_model=DeviceModelRead)
def create_device_model(data: DeviceModelCreate, db: Session = Depends(get_db)):
    m = DeviceModel(**data.model_dump())
    db.add(m)
    db.commit()
    db.refresh(m)
    return DeviceModelRead.model_validate(m)


@router.put("/{model_id}", response_model=DeviceModelRead)
def update_device_model(model_id: int, data: DeviceModelUpdate, db: Session = Depends(get_db)):
    m = db.query(DeviceModel).filter(DeviceModel.id == model_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Device model not found")
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(m, key, val)
    db.commit()
    db.refresh(m)
    return DeviceModelRead.model_validate(m)


@router.delete("/{model_id}")
def delete_device_model(model_id: int, db: Session = Depends(get_db)):
    m = db.query(DeviceModel).filter(DeviceModel.id == model_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Device model not found")
    if m.instances:
        raise HTTPException(status_code=400, detail="Cannot delete model with existing device instances")
    db.delete(m)
    db.commit()
    return {"detail": "Deleted"}
