import random
import string
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.subscription import Subscription
from app.models.customer import Customer
from app.models.service_plan import ServicePlan
from app.models.audit_log import AuditLog
from app.schemas.subscription import SubscriptionCreate, SubscriptionUpdate, SubscriptionOut

router = APIRouter(prefix="/api/subscriptions", tags=["Subscriptions"])


def _generate_pppoe_username(customer_number: str) -> str:
    """Generate PPPoE username from customer number."""
    return customer_number.lower().replace("-", "") if customer_number else f"pppoe_{random.randint(10000, 99999)}"


def _generate_pppoe_password(length: int = 10) -> str:
    """Generate random PPPoE password."""
    chars = string.ascii_letters + string.digits
    return "".join(random.choices(chars, k=length))


@router.get("", response_model=list[SubscriptionOut])
def list_subscriptions(
    status: Optional[str] = Query(None),
    customer_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(Subscription)
    if status:
        q = q.filter(Subscription.status == status)
    if customer_id:
        q = q.filter(Subscription.customer_id == customer_id)

    subs = q.order_by(Subscription.created_at.desc()).all()

    result = []
    for sub in subs:
        out = SubscriptionOut.model_validate(sub)
        out.customer_name = sub.customer.name if sub.customer else None
        out.plan_name = sub.service_plan.name if sub.service_plan else None
        result.append(out)
    return result


@router.get("/{sub_id}", response_model=SubscriptionOut)
def get_subscription(sub_id: int, db: Session = Depends(get_db)):
    sub = db.query(Subscription).filter(Subscription.id == sub_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    out = SubscriptionOut.model_validate(sub)
    out.customer_name = sub.customer.name if sub.customer else None
    out.plan_name = sub.service_plan.name if sub.service_plan else None
    return out


@router.post("", response_model=SubscriptionOut, status_code=201)
def create_subscription(data: SubscriptionCreate, db: Session = Depends(get_db)):
    # Validate customer
    customer = db.query(Customer).filter(Customer.id == data.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # Validate plan
    plan = db.query(ServicePlan).filter(ServicePlan.id == data.service_plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Service plan not found")

    # Auto-generate PPPoE credentials if not provided
    pppoe_user = data.pppoe_username or _generate_pppoe_username(customer.customer_number or f"ISP{customer.id:08d}")
    pppoe_pass = data.pppoe_password or _generate_pppoe_password()

    sub = Subscription(
        customer_id=data.customer_id,
        service_plan_id=data.service_plan_id,
        device_instance_id=data.device_instance_id,
        pppoe_username=pppoe_user,
        pppoe_password=pppoe_pass,
        ont_serial_number=data.ont_serial_number,
        ont_mac_address=data.ont_mac_address,
        olt_info=data.olt_info,
        odp_info=data.odp_info,
        signal_dbm=data.signal_dbm,
        status="PENDING",
    )
    db.add(sub)
    db.flush()

    # Audit
    db.add(AuditLog(
        actor="SYSTEM", action="CREATE", entity_type="Subscription", entity_id=sub.id,
        details={"customer_id": data.customer_id, "plan_id": data.service_plan_id, "pppoe_username": pppoe_user},
    ))
    db.commit()
    db.refresh(sub)

    out = SubscriptionOut.model_validate(sub)
    out.customer_name = customer.name
    out.plan_name = plan.name
    return out


@router.put("/{sub_id}", response_model=SubscriptionOut)
def update_subscription(sub_id: int, data: SubscriptionUpdate, db: Session = Depends(get_db)):
    sub = db.query(Subscription).filter(Subscription.id == sub_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(sub, field, value)
    db.commit()
    db.refresh(sub)

    out = SubscriptionOut.model_validate(sub)
    out.customer_name = sub.customer.name if sub.customer else None
    out.plan_name = sub.service_plan.name if sub.service_plan else None
    return out
