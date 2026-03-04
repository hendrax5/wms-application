from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class InvoiceCreate(BaseModel):
    subscription_id: int
    customer_id: int
    billing_period_start: str   # ISO date
    billing_period_end: str     # ISO date
    amount: float
    pro_rata_days: Optional[int] = None
    due_date: str               # ISO date
    notes: Optional[str] = None


class InvoicePayment(BaseModel):
    payment_method: str     # CASH, TRANSFER, VA, QRIS
    payment_reference: Optional[str] = None
    notes: Optional[str] = None


class InvoiceOut(BaseModel):
    id: int
    invoice_number: str
    subscription_id: int
    customer_id: int
    billing_period_start: Optional[datetime]
    billing_period_end: Optional[datetime]
    amount: float
    pro_rata_days: Optional[int]
    status: str
    due_date: Optional[datetime]
    paid_at: Optional[datetime]
    payment_method: Optional[str]
    payment_reference: Optional[str]
    notes: Optional[str]
    created_at: Optional[datetime]

    # Joined fields
    customer_name: Optional[str] = None

    class Config:
        from_attributes = True
