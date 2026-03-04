from datetime import datetime, timezone, timedelta
import calendar

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.invoice import Invoice
from app.models.subscription import Subscription
from app.models.customer import Customer
from app.models.audit_log import AuditLog
from app.schemas.invoice import InvoiceCreate, InvoicePayment, InvoiceOut

router = APIRouter(prefix="/api/invoices", tags=["Invoices"])


def _next_invoice_number(db: Session) -> str:
    """Generate next invoice number: INV-YYYY-NNNNNN."""
    year = datetime.now().year
    prefix = f"INV-{year}-"
    last = (
        db.query(Invoice)
        .filter(Invoice.invoice_number.like(f"{prefix}%"))
        .order_by(Invoice.id.desc())
        .first()
    )
    if last:
        seq = int(last.invoice_number.split("-")[-1]) + 1
    else:
        seq = 1
    return f"{prefix}{seq:06d}"


@router.get("", response_model=list[InvoiceOut])
def list_invoices(
    status: Optional[str] = Query(None),
    customer_id: Optional[int] = Query(None),
    subscription_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(Invoice)
    if status:
        q = q.filter(Invoice.status == status)
    if customer_id:
        q = q.filter(Invoice.customer_id == customer_id)
    if subscription_id:
        q = q.filter(Invoice.subscription_id == subscription_id)

    invoices = q.order_by(Invoice.created_at.desc()).all()

    result = []
    for inv in invoices:
        out = InvoiceOut.model_validate(inv)
        out.customer_name = inv.customer.name if inv.customer else None
        result.append(out)
    return result


@router.get("/{inv_id}", response_model=InvoiceOut)
def get_invoice(inv_id: int, db: Session = Depends(get_db)):
    inv = db.query(Invoice).filter(Invoice.id == inv_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    out = InvoiceOut.model_validate(inv)
    out.customer_name = inv.customer.name if inv.customer else None
    return out


@router.post("", response_model=InvoiceOut, status_code=201)
def create_invoice(data: InvoiceCreate, db: Session = Depends(get_db)):
    # Validate subscription and customer
    sub = db.query(Subscription).filter(Subscription.id == data.subscription_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    customer = db.query(Customer).filter(Customer.id == data.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    inv = Invoice(
        invoice_number=_next_invoice_number(db),
        subscription_id=data.subscription_id,
        customer_id=data.customer_id,
        billing_period_start=datetime.fromisoformat(data.billing_period_start),
        billing_period_end=datetime.fromisoformat(data.billing_period_end),
        amount=data.amount,
        pro_rata_days=data.pro_rata_days,
        due_date=datetime.fromisoformat(data.due_date),
        status="DRAFT",
        notes=data.notes,
    )
    db.add(inv)
    db.flush()

    db.add(AuditLog(
        actor="SYSTEM", action="CREATE", entity_type="Invoice", entity_id=inv.id,
        details={"invoice_number": inv.invoice_number, "amount": data.amount},
    ))
    db.commit()
    db.refresh(inv)

    out = InvoiceOut.model_validate(inv)
    out.customer_name = customer.name
    return out


@router.post("/{inv_id}/pay", response_model=InvoiceOut)
def pay_invoice(inv_id: int, data: InvoicePayment, db: Session = Depends(get_db)):
    """Record payment for an invoice. Triggers reconnection if subscription was isolated."""
    inv = db.query(Invoice).filter(Invoice.id == inv_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if inv.status == "PAID":
        raise HTTPException(status_code=400, detail="Invoice already paid")
    if inv.status == "CANCELLED":
        raise HTTPException(status_code=400, detail="Cannot pay cancelled invoice")

    inv.status = "PAID"
    inv.paid_at = datetime.now(timezone.utc)
    inv.payment_method = data.payment_method
    inv.payment_reference = data.payment_reference
    if data.notes:
        inv.notes = data.notes

    # Check if subscription was isolated — trigger reconnect
    sub = db.query(Subscription).filter(Subscription.id == inv.subscription_id).first()
    reconnect_triggered = False
    if sub and sub.status == "ISOLATED":
        sub.status = "ACTIVE"
        reconnect_triggered = True

    db.add(AuditLog(
        actor="SYSTEM", action="UPDATE", entity_type="Invoice", entity_id=inv.id,
        details={
            "action": "PAYMENT",
            "method": data.payment_method,
            "reference": data.payment_reference,
            "reconnect_triggered": reconnect_triggered,
        },
    ))
    db.commit()
    db.refresh(inv)

    out = InvoiceOut.model_validate(inv)
    out.customer_name = inv.customer.name if inv.customer else None
    return out


@router.post("/generate-prorata", response_model=InvoiceOut)
def generate_prorata_invoice(subscription_id: int, db: Session = Depends(get_db)):
    """Generate a pro-rata invoice for a newly activated subscription."""
    sub = db.query(Subscription).filter(Subscription.id == subscription_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    if not sub.activation_date:
        raise HTTPException(status_code=400, detail="Subscription not yet activated")

    plan = sub.service_plan
    activation = sub.activation_date

    # Calculate pro-rata: remaining days in the activation month
    days_in_month = calendar.monthrange(activation.year, activation.month)[1]
    remaining_days = days_in_month - activation.day + 1
    prorata_amount = round((plan.monthly_price / days_in_month) * remaining_days, 2)

    period_start = activation
    period_end = activation.replace(day=days_in_month, hour=23, minute=59, second=59)
    due_date = period_end + timedelta(days=7)

    inv = Invoice(
        invoice_number=_next_invoice_number(db),
        subscription_id=sub.id,
        customer_id=sub.customer_id,
        billing_period_start=period_start,
        billing_period_end=period_end,
        amount=prorata_amount,
        pro_rata_days=remaining_days,
        due_date=due_date,
        status="SENT",
    )
    db.add(inv)
    db.flush()

    db.add(AuditLog(
        actor="SYSTEM", action="CREATE", entity_type="Invoice", entity_id=inv.id,
        details={"type": "PRO_RATA", "days": remaining_days, "amount": prorata_amount},
    ))
    db.commit()
    db.refresh(inv)

    out = InvoiceOut.model_validate(inv)
    out.customer_name = sub.customer.name if sub.customer else None
    return out
