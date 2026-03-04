from pydantic import BaseModel
from typing import Optional


class DashboardStats(BaseModel):
    total_assets: int = 0
    status_breakdown: dict = {}       # {"AVAILABLE": 10, "DEPLOYED": 25, ...}
    purpose_breakdown: dict = {}      # {"INSTALLED": 15, "LOANED": 5, "SOLD": 5}
    condition_breakdown: dict = {}    # {"GOOD": 30, "DAMAGED": 5}
    branch_breakdown: dict = {}       # {"Cabang JKT": 50, "Cabang SBY": 30}
    ghost_assets: list = []           # Devices in TRANSFER > 7 days
    recent_movements: list = []       # Last 10 movements

    # ISP KPIs
    active_subscribers: int = 0
    pending_activations: int = 0
    isolated_subscribers: int = 0
    monthly_recurring_revenue: float = 0.0
    open_work_orders: int = 0
    overdue_invoices: int = 0


class WorkflowInbound(BaseModel):
    model_id: int
    serial_number: str
    mac_address: Optional[str] = None
    location_id: int                  # Gudang tujuan (HO)
    purchase_date: Optional[str] = None
    warranty_expiry: Optional[str] = None
    reference_doc: Optional[str] = None
    technician_name: Optional[str] = None
    notes: Optional[str] = None


class WorkflowTransfer(BaseModel):
    device_instance_id: int
    to_location_id: int               # Gudang tujuan
    reference_doc: Optional[str] = None
    technician_name: Optional[str] = None
    notes: Optional[str] = None


class WorkflowDeploy(BaseModel):
    device_instance_id: int
    to_location_id: int               # Site lokasi pemasangan (wajib terdaftar)
    deployment_purpose: str           # INSTALLED, LOANED, SOLD (WAJIB)
    customer_id: int                  # Customer penerima (WAJIB)
    reference_doc: Optional[str] = None
    technician_name: Optional[str] = None
    notes: Optional[str] = None


class WorkflowDismantle(BaseModel):
    device_instance_id: int
    to_location_id: int               # Lokasi setelah dicopot (transit/teknisi)
    condition: str = "DAMAGED"        # GOOD or DAMAGED
    reference_doc: Optional[str] = None
    technician_name: Optional[str] = None
    notes: Optional[str] = None


class WorkflowReturn(BaseModel):
    device_instance_id: int
    to_location_id: int               # Gudang Cabang (area karantina)
    reference_doc: Optional[str] = None
    technician_name: Optional[str] = None
    notes: Optional[str] = None


class WorkflowRMA(BaseModel):
    device_instance_id: int
    to_location_id: int               # HO / Repair Center
    reference_doc: Optional[str] = None
    technician_name: Optional[str] = None
    notes: Optional[str] = None
