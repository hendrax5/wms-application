from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.customer import Customer
from app.schemas.customer import CustomerCreate, CustomerUpdate, CustomerRead

router = APIRouter(prefix="/api/customers", tags=["Customers"])


@router.get("/", response_model=list[CustomerRead])
def list_customers(
    customer_type: str | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(Customer)
    if customer_type:
        query = query.filter(Customer.customer_type == customer_type)
    if search:
        query = query.filter(
            (Customer.name.ilike(f"%{search}%")) |
            (Customer.company.ilike(f"%{search}%"))
        )
    return query.order_by(Customer.name).all()


@router.get("/{customer_id}", response_model=CustomerRead)
def get_customer(customer_id: int, db: Session = Depends(get_db)):
    c = db.query(Customer).filter(Customer.id == customer_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Customer not found")
    return c


@router.post("/", response_model=CustomerRead)
def create_customer(data: CustomerCreate, db: Session = Depends(get_db)):
    c = Customer(**data.model_dump())
    c.registration_date = datetime.now(timezone.utc)
    db.add(c)
    db.flush()  # Get ID for auto-numbering
    c.customer_number = f"ISP{c.id:08d}"
    db.commit()
    db.refresh(c)
    return c


@router.put("/{customer_id}", response_model=CustomerRead)
def update_customer(customer_id: int, data: CustomerUpdate, db: Session = Depends(get_db)):
    c = db.query(Customer).filter(Customer.id == customer_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Customer not found")
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(c, key, val)
    db.commit()
    db.refresh(c)
    return c


@router.delete("/{customer_id}")
def delete_customer(customer_id: int, db: Session = Depends(get_db)):
    c = db.query(Customer).filter(Customer.id == customer_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Customer not found")
    if c.device_instances:
        raise HTTPException(status_code=400, detail="Cannot delete customer with assigned devices")
    db.delete(c)
    db.commit()
    return {"detail": "Deleted"}
