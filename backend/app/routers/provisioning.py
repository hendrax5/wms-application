from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import settings
from app.schemas.subscription import ProvisionActivateRequest, ProvisionIsolateRequest, ProvisionReconnectRequest
from app.services.provisioning_service import ProvisioningService
from app.services.olt_zte_service import OLTZteService
from app.services.radius_service import RadiusService
from app.services.mikrotik_service import MikrotikService

router = APIRouter(prefix="/api/provisioning", tags=["Provisioning"])


def _get_provisioning_service() -> ProvisioningService:
    """Build provisioning service with current config."""
    olt = OLTZteService(
        host=settings.OLT_HOST,
        port=settings.OLT_PORT,
        username=settings.OLT_USERNAME,
        password=settings.OLT_PASSWORD,
        dry_run=settings.DRY_RUN_MODE,
    )
    radius = RadiusService(
        db_url=settings.RADIUS_DB_URL,
        dry_run=settings.DRY_RUN_MODE,
    )
    mikrotik = MikrotikService(
        host=settings.MIKROTIK_HOST,
        username=settings.MIKROTIK_USERNAME,
        password=settings.MIKROTIK_PASSWORD,
        dry_run=settings.DRY_RUN_MODE,
    )
    return ProvisioningService(olt=olt, radius=radius, mikrotik=mikrotik)


@router.post("/activate")
def activate_subscription(data: ProvisionActivateRequest, db: Session = Depends(get_db)):
    """
    Trigger full provisioning pipeline:
    Warehouse validation → OLT ONU registration → VLAN/BW config → Radius account creation → Activate.
    """
    service = _get_provisioning_service()
    result = service.activate(db, data.subscription_id, data.actor)
    return {
        "success": result.success,
        "steps": result.steps_completed,
        "message": result.message,
        "error": result.error,
        "dry_run": settings.DRY_RUN_MODE,
    }


@router.post("/isolate")
def isolate_subscription(data: ProvisionIsolateRequest, db: Session = Depends(get_db)):
    """
    Isolate subscriber: Update Radius group → Force disconnect PPPoE → Redirect to payment page.
    """
    service = _get_provisioning_service()
    result = service.isolate(db, data.subscription_id, data.reason, data.actor)
    return {
        "success": result.success,
        "steps": result.steps_completed,
        "message": result.message,
        "error": result.error,
        "dry_run": settings.DRY_RUN_MODE,
    }


@router.post("/reconnect")
def reconnect_subscription(data: ProvisionReconnectRequest, db: Session = Depends(get_db)):
    """
    Reconnect subscriber after payment: Restore Radius group → Force disconnect → User redials with active profile.
    """
    service = _get_provisioning_service()
    result = service.reconnect(db, data.subscription_id, data.actor)
    return {
        "success": result.success,
        "steps": result.steps_completed,
        "message": result.message,
        "error": result.error,
        "dry_run": settings.DRY_RUN_MODE,
    }
