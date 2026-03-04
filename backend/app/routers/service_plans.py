from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.service_plan import ServicePlan
from app.schemas.service_plan import ServicePlanCreate, ServicePlanUpdate, ServicePlanOut

router = APIRouter(prefix="/api/service-plans", tags=["Service Plans"])


@router.get("", response_model=list[ServicePlanOut])
def list_service_plans(
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(ServicePlan)
    if is_active is not None:
        q = q.filter(ServicePlan.is_active == is_active)
    return q.order_by(ServicePlan.name).all()


@router.get("/{plan_id}", response_model=ServicePlanOut)
def get_service_plan(plan_id: int, db: Session = Depends(get_db)):
    plan = db.query(ServicePlan).filter(ServicePlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Service plan not found")
    return plan


@router.post("", response_model=ServicePlanOut, status_code=201)
def create_service_plan(data: ServicePlanCreate, db: Session = Depends(get_db)):
    existing = db.query(ServicePlan).filter(ServicePlan.name == data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Plan '{data.name}' already exists")

    plan = ServicePlan(**data.model_dump())
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


@router.put("/{plan_id}", response_model=ServicePlanOut)
def update_service_plan(plan_id: int, data: ServicePlanUpdate, db: Session = Depends(get_db)):
    plan = db.query(ServicePlan).filter(ServicePlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Service plan not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(plan, field, value)
    db.commit()
    db.refresh(plan)
    return plan


@router.delete("/{plan_id}")
def delete_service_plan(plan_id: int, db: Session = Depends(get_db)):
    plan = db.query(ServicePlan).filter(ServicePlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Service plan not found")
    db.delete(plan)
    db.commit()
    return {"detail": "Service plan deleted"}
