"""
Provisioning Orchestrator — The core pipeline that connects Warehouse → OLT → Radius.

This service validates warehouse status, configures the OLT ZTE, creates Radius accounts,
and handles rollback if any step fails. All actions are logged to the AuditLog.
"""
import logging
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Optional

from sqlalchemy.orm import Session

from app.models.subscription import Subscription
from app.models.device_instance import DeviceInstance
from app.models.service_plan import ServicePlan
from app.models.audit_log import AuditLog
from app.services.olt_zte_service import OLTZteService
from app.services.radius_service import RadiusService
from app.services.mikrotik_service import MikrotikService

logger = logging.getLogger("provisioning")


@dataclass
class ProvisioningResult:
    success: bool
    steps_completed: list[str]
    message: str
    error: Optional[str] = None


class ProvisioningService:
    """Orchestrates the full provisioning pipeline with rollback."""

    def __init__(self, olt: OLTZteService, radius: RadiusService, mikrotik: MikrotikService):
        self.olt = olt
        self.radius = radius
        self.mikrotik = mikrotik

    def activate(self, db: Session, subscription_id: int, actor: str = "SYSTEM") -> ProvisioningResult:
        """
        Full activation pipeline:
        1. Validate ONT is assigned (outbound from warehouse)
        2. Register ONU on OLT ZTE
        3. Configure bandwidth (T-CONT)
        4. Configure VLAN
        5. Create Radius PPPoE user with MAC binding
        6. Update subscription status to ACTIVE
        """
        steps = []

        # --- Load subscription and related data ---
        sub = db.query(Subscription).filter(Subscription.id == subscription_id).first()
        if not sub:
            return ProvisioningResult(False, steps, "Subscription not found")

        if sub.status not in ("PENDING",):
            return ProvisioningResult(False, steps, f"Subscription status is '{sub.status}', expected PENDING")

        plan = db.query(ServicePlan).filter(ServicePlan.id == sub.service_plan_id).first()
        if not plan:
            return ProvisioningResult(False, steps, "Service plan not found")

        # --- Step 1: Validate warehouse (ONT device exists and is DEPLOYED/AVAILABLE) ---
        device = None
        if sub.device_instance_id:
            device = db.query(DeviceInstance).filter(DeviceInstance.id == sub.device_instance_id).first()
            if not device:
                return ProvisioningResult(False, steps, "Linked ONT device not found in inventory")
            if device.status not in ("AVAILABLE", "DEPLOYED"):
                return ProvisioningResult(
                    False, steps,
                    f"ONT SN {device.serial_number} has status '{device.status}'. "
                    "Device must be AVAILABLE or DEPLOYED (outbound from warehouse)."
                )
            # Bind SN and MAC from device
            sub.ont_serial_number = device.serial_number
            sub.ont_mac_address = device.mac_address
        elif sub.ont_serial_number:
            # Validate SN exists in warehouse
            device = db.query(DeviceInstance).filter(
                DeviceInstance.serial_number == sub.ont_serial_number
            ).first()
            if not device:
                return ProvisioningResult(False, steps, f"ONT SN {sub.ont_serial_number} not found in warehouse")
        else:
            return ProvisioningResult(False, steps, "No ONT device linked to this subscription")

        steps.append("✅ Warehouse validation passed")

        # --- Step 2: Register ONU on OLT ---
        olt_info = sub.olt_info or {}
        rack = olt_info.get("rack", 1)
        shelf = olt_info.get("shelf", 1)
        slot = olt_info.get("slot", 1)
        port = olt_info.get("port", 1)
        onu_index = olt_info.get("onu_index", 1)
        onu_type = olt_info.get("onu_type", "ZTE-F660")

        result_onu = self.olt.register_onu(rack, shelf, slot, port, onu_index, onu_type, sub.ont_serial_number)
        if not result_onu.success:
            return ProvisioningResult(False, steps, "OLT ONU registration failed", result_onu.error)
        steps.append("✅ ONU registered on OLT")

        # --- Step 3: Configure bandwidth ---
        profile = plan.olt_profile_name or f"PRO_{plan.speed_down_mbps}MBPS"
        result_bw = self.olt.configure_bandwidth(rack, shelf, slot, port, onu_index, profile)
        if not result_bw.success:
            # Rollback: remove ONU
            self.olt.delete_onu(rack, shelf, slot, port, onu_index)
            return ProvisioningResult(False, steps, "OLT bandwidth config failed, rolled back ONU", result_bw.error)
        steps.append("✅ Bandwidth profile configured")

        # --- Step 4: Configure VLAN ---
        vlan_id = plan.vlan_id or 100
        result_vlan = self.olt.configure_vlan(rack, shelf, slot, port, onu_index, vlan_id)
        if not result_vlan.success:
            self.olt.delete_onu(rack, shelf, slot, port, onu_index)
            return ProvisioningResult(False, steps, "VLAN config failed, rolled back ONU", result_vlan.error)
        steps.append("✅ VLAN configured")

        # --- Step 5: Create Radius account ---
        mikrotik_group = plan.mikrotik_group or f"PRO_{plan.speed_down_mbps}MBPS"
        framed_pool = plan.framed_pool or "pool_default"
        result_radius = self.radius.create_pppoe_user(
            username=sub.pppoe_username,
            password=sub.pppoe_password,
            mac_address=sub.ont_mac_address,
            mikrotik_group=mikrotik_group,
            framed_pool=framed_pool,
        )
        if not result_radius.success:
            # Rollback: remove ONU from OLT
            self.olt.delete_onu(rack, shelf, slot, port, onu_index)
            return ProvisioningResult(False, steps, "Radius account creation failed, rolled back OLT", result_radius.error)
        steps.append("✅ Radius PPPoE account created")

        # --- Step 6: Update subscription ---
        sub.status = "ACTIVE"
        sub.activation_date = datetime.now(timezone.utc)

        db.add(AuditLog(
            actor=actor, action="PROVISION",
            entity_type="Subscription", entity_id=sub.id,
            details={
                "steps": steps,
                "olt_interface": f"gpon-olt_{rack}/{shelf}/{slot}/{port}:{onu_index}",
                "pppoe_username": sub.pppoe_username,
                "mikrotik_group": mikrotik_group,
                "vlan_id": vlan_id,
            },
        ))
        db.commit()
        steps.append("✅ Subscription activated")

        return ProvisioningResult(True, steps, f"Activation successful. PPPoE: {sub.pppoe_username}")

    def isolate(self, db: Session, subscription_id: int, reason: str = "OVERDUE_PAYMENT", actor: str = "SYSTEM") -> ProvisioningResult:
        """
        Isolate a subscriber:
        1. Update Radius Mikrotik-Group to ISOLIR profile
        2. Force disconnect PPPoE session on Mikrotik
        3. User auto-redials → gets redirect to payment page
        """
        steps = []

        sub = db.query(Subscription).filter(Subscription.id == subscription_id).first()
        if not sub:
            return ProvisioningResult(False, steps, "Subscription not found")
        if sub.status != "ACTIVE":
            return ProvisioningResult(False, steps, f"Cannot isolate — status is '{sub.status}'")

        # Step 1: Update Radius group
        result = self.radius.update_user_group(sub.pppoe_username, "PRO_ISOLIR")
        if not result.success:
            return ProvisioningResult(False, steps, "Radius group update failed", result.error)
        steps.append("✅ Radius group changed to PRO_ISOLIR")

        # Step 2: Force disconnect
        result_mk = self.mikrotik.disconnect_session(sub.pppoe_username)
        steps.append("✅ PPPoE session disconnected" if result_mk.success else "⚠️ Mikrotik disconnect failed (non-critical)")

        # Step 3: Update subscription
        sub.status = "ISOLATED"
        db.add(AuditLog(
            actor=actor, action="ISOLATE",
            entity_type="Subscription", entity_id=sub.id,
            details={"reason": reason, "pppoe_username": sub.pppoe_username},
        ))
        db.commit()
        steps.append("✅ Subscription status set to ISOLATED")

        return ProvisioningResult(True, steps, f"Subscriber {sub.pppoe_username} isolated ({reason})")

    def reconnect(self, db: Session, subscription_id: int, actor: str = "SYSTEM") -> ProvisioningResult:
        """
        Reconnect a subscriber after payment:
        1. Update Radius Mikrotik-Group back to active profile
        2. Force disconnect (user redials with restored profile)
        """
        steps = []

        sub = db.query(Subscription).filter(Subscription.id == subscription_id).first()
        if not sub:
            return ProvisioningResult(False, steps, "Subscription not found")
        if sub.status != "ISOLATED":
            return ProvisioningResult(False, steps, f"Cannot reconnect — status is '{sub.status}'")

        plan = db.query(ServicePlan).filter(ServicePlan.id == sub.service_plan_id).first()
        active_group = plan.mikrotik_group or f"PRO_{plan.speed_down_mbps}MBPS"

        # Step 1: Restore Radius group
        result = self.radius.update_user_group(sub.pppoe_username, active_group)
        if not result.success:
            return ProvisioningResult(False, steps, "Radius group restore failed", result.error)
        steps.append(f"✅ Radius group restored to {active_group}")

        # Step 2: Force disconnect
        result_mk = self.mikrotik.disconnect_session(sub.pppoe_username)
        steps.append("✅ PPPoE session disconnected (user will redial with active profile)")

        # Step 3: Update subscription
        sub.status = "ACTIVE"
        db.add(AuditLog(
            actor=actor, action="RECONNECT",
            entity_type="Subscription", entity_id=sub.id,
            details={"pppoe_username": sub.pppoe_username, "restored_group": active_group},
        ))
        db.commit()
        steps.append("✅ Subscription status restored to ACTIVE")

        return ProvisioningResult(True, steps, f"Subscriber {sub.pppoe_username} reconnected")
