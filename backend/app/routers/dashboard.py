from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.database import get_db
from app.models.device_instance import DeviceInstance
from app.models.movement_log import MovementLog
from app.models.subscription import Subscription
from app.models.service_plan import ServicePlan
from app.models.work_order import WorkOrder
from app.models.invoice import Invoice
from app.schemas.dashboard import DashboardStats
from app.schemas.movement_log import MovementLogRead

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db)):
    # Total assets (excluding SCRAPPED)
    total = db.query(func.count(DeviceInstance.id)).filter(
        DeviceInstance.status != "SCRAPPED"
    ).scalar() or 0

    # Status breakdown
    status_rows = db.query(
        DeviceInstance.status, func.count(DeviceInstance.id)
    ).group_by(DeviceInstance.status).all()
    status_breakdown = {row[0]: row[1] for row in status_rows}

    # Purpose breakdown (only deployed devices)
    purpose_rows = db.query(
        DeviceInstance.deployment_purpose, func.count(DeviceInstance.id)
    ).filter(
        DeviceInstance.deployment_purpose.isnot(None)
    ).group_by(DeviceInstance.deployment_purpose).all()
    purpose_breakdown = {row[0]: row[1] for row in purpose_rows}

    # Condition breakdown
    condition_rows = db.query(
        DeviceInstance.condition, func.count(DeviceInstance.id)
    ).group_by(DeviceInstance.condition).all()
    condition_breakdown = {row[0]: row[1] for row in condition_rows}

    # Branch breakdown logic
    # Find all devices and their locations to resolve to top-level branches
    branch_breakdown = {}
    from app.models.location import Location
    all_devices = db.query(DeviceInstance).options(joinedload(DeviceInstance.current_location)).filter(
        DeviceInstance.status != "SCRAPPED",
        DeviceInstance.current_location_id.isnot(None)
    ).all()
    
    # We need a quick way to find the "branch" (parent) of any location
    locations = db.query(Location).all()
    loc_dict = {loc.id: loc for loc in locations}
    
    for d in all_devices:
        loc = d.current_location
        # Traverse up to find the branch or head office
        while loc and loc.parent_id and loc.type not in ("HEAD_OFFICE", "BRANCH"):
            loc = loc_dict.get(loc.parent_id)
        
        if loc and loc.type in ("HEAD_OFFICE", "BRANCH"):
            branch_breakdown[loc.name] = branch_breakdown.get(loc.name, 0) + 1

    # Ghost assets: devices transferred > 7 days ago that haven't been deployed
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    ghost_logs = db.query(MovementLog).options(
        joinedload(MovementLog.device_instance),
        joinedload(MovementLog.to_location),
    ).filter(
        MovementLog.activity_type == "TRANSFER",
        MovementLog.timestamp < seven_days_ago,
    ).order_by(MovementLog.timestamp.desc()).limit(20).all()

    ghost_assets = []
    seen_devices = set()
    for log in ghost_logs:
        device = log.device_instance
        if device and device.id not in seen_devices and device.status == "AVAILABLE":
            seen_devices.add(device.id)
            ghost_assets.append({
                "device_id": device.id,
                "serial_number": device.serial_number,
                "location": log.to_location.name if log.to_location else "Unknown",
                "transfer_date": log.timestamp.isoformat() if log.timestamp else None,
            })

    # Recent movements
    recent_logs = db.query(MovementLog).options(
        joinedload(MovementLog.device_instance),
        joinedload(MovementLog.from_location),
        joinedload(MovementLog.to_location),
        joinedload(MovementLog.customer),
    ).order_by(MovementLog.timestamp.desc()).limit(10).all()

    recent_movements = []
    for log in recent_logs:
        r = MovementLogRead.model_validate(log)
        r.from_location_name = log.from_location.name if log.from_location else None
        r.to_location_name = log.to_location.name if log.to_location else None
        r.serial_number = log.device_instance.serial_number if log.device_instance else None
        r.customer_name = log.customer.name if log.customer else None
        recent_movements.append(r)

    # ── ISP KPIs ──
    active_subs = db.query(func.count(Subscription.id)).filter(Subscription.status == "ACTIVE").scalar() or 0
    pending_subs = db.query(func.count(Subscription.id)).filter(Subscription.status == "PENDING").scalar() or 0
    isolated_subs = db.query(func.count(Subscription.id)).filter(Subscription.status == "ISOLATED").scalar() or 0

    # MRR: sum of monthly_price for all active subscriptions
    mrr = db.query(func.sum(ServicePlan.monthly_price)).join(
        Subscription, Subscription.service_plan_id == ServicePlan.id
    ).filter(Subscription.status == "ACTIVE").scalar() or 0.0

    open_wos = db.query(func.count(WorkOrder.id)).filter(
        WorkOrder.status.in_(["CREATED", "ASSIGNED", "IN_PROGRESS"])
    ).scalar() or 0

    overdue_invs = db.query(func.count(Invoice.id)).filter(
        Invoice.status == "OVERDUE"
    ).scalar() or 0

    return DashboardStats(
        total_assets=total,
        status_breakdown=status_breakdown,
        purpose_breakdown=purpose_breakdown,
        condition_breakdown=condition_breakdown,
        branch_breakdown=branch_breakdown,
        ghost_assets=ghost_assets,
        recent_movements=recent_movements,
        active_subscribers=active_subs,
        pending_activations=pending_subs,
        isolated_subscribers=isolated_subs,
        monthly_recurring_revenue=mrr,
        open_work_orders=open_wos,
        overdue_invoices=overdue_invs,
    )
