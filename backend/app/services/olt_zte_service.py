"""
OLT ZTE SSH Service — Middleware for ZTE C320/C300/C600 CLI automation.

Supports dry-run mode (DRY_RUN_MODE=True in config) which logs commands
without executing them. This is the default for Phase 1.
"""
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger("olt_zte")


@dataclass
class OLTResult:
    success: bool
    command: str
    output: str
    error: Optional[str] = None


class OLTZteService:
    """SSH wrapper for ZTE OLT CLI commands."""

    def __init__(self, host: str, port: int, username: str, password: str, dry_run: bool = True):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.dry_run = dry_run
        self._connection = None

    def _exec(self, commands: list[str]) -> OLTResult:
        """Execute a list of CLI commands via SSH (or log in dry-run mode)."""
        full_cmd = "\n".join(commands)

        if self.dry_run:
            logger.info(f"[DRY-RUN] OLT ZTE @ {self.host}:\n{full_cmd}")
            return OLTResult(success=True, command=full_cmd, output="[DRY-RUN] Commands logged but not executed")

        # Production mode — uses Paramiko SSH
        try:
            import paramiko
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(self.host, port=self.port, username=self.username, password=self.password, timeout=30)

            shell = client.invoke_shell()
            import time
            time.sleep(1)

            output_buffer = ""
            for cmd in commands:
                shell.send(cmd + "\n")
                time.sleep(0.5)
                while shell.recv_ready():
                    output_buffer += shell.recv(4096).decode("utf-8", errors="replace")

            client.close()
            return OLTResult(success=True, command=full_cmd, output=output_buffer)

        except Exception as e:
            logger.error(f"OLT SSH error: {e}")
            return OLTResult(success=False, command=full_cmd, output="", error=str(e))

    def discover_unconfigured_onus(self) -> OLTResult:
        """Step 1: Show unconfigured ONUs on the OLT."""
        return self._exec(["show gpon onu unconfigured"])

    def register_onu(
        self,
        rack: int, shelf: int, slot: int, port: int,
        onu_index: int, onu_type: str, serial_number: str,
    ) -> OLTResult:
        """Step 2a: Register ONU with serial number."""
        interface = f"{rack}/{shelf}/{slot}/{port}"
        return self._exec([
            "conf t",
            f"interface gpon-olt_{interface}",
            f" onu {onu_index} type {onu_type} sn {serial_number}",
            "exit",
        ])

    def configure_bandwidth(
        self,
        rack: int, shelf: int, slot: int, port: int,
        onu_index: int, profile_name: str,
        upstream_profile: Optional[str] = None,
        downstream_profile: Optional[str] = None,
    ) -> OLTResult:
        """Step 2b: Configure T-CONT and GEM port bandwidth."""
        interface = f"{rack}/{shelf}/{slot}/{port}"
        cmds = [
            "conf t",
            f"interface gpon-onu_{interface}:{onu_index}",
            f" tcont 1 profile {profile_name}",
            " gemport 1 tcont 1",
        ]
        if upstream_profile and downstream_profile:
            cmds.append(f" gemport 1 traffic-limit upstream {upstream_profile} downstream {downstream_profile}")
        cmds.append("exit")
        return self._exec(cmds)

    def configure_vlan(
        self,
        rack: int, shelf: int, slot: int, port: int,
        onu_index: int, vlan_id: int,
    ) -> OLTResult:
        """Step 3: Configure VLAN tagging and service port."""
        interface = f"{rack}/{shelf}/{slot}/{port}"
        return self._exec([
            "conf t",
            f"pon-onu-mng gpon-onu_{interface}:{onu_index}",
            f" service 1 gemport 1 vlan {vlan_id}",
            f" vlan port eth_0/1 mode tag vlan {vlan_id}",
            "exit",
            f"service-port 1 vport 1 user-vlan {vlan_id} vlan {vlan_id}",
        ])

    def delete_onu(
        self,
        rack: int, shelf: int, slot: int, port: int,
        onu_index: int,
    ) -> OLTResult:
        """Rollback: Remove ONU registration."""
        interface = f"{rack}/{shelf}/{slot}/{port}"
        return self._exec([
            "conf t",
            f"interface gpon-olt_{interface}",
            f" no onu {onu_index}",
            "exit",
        ])

    def get_onu_signal(
        self,
        rack: int, shelf: int, slot: int, port: int,
        onu_index: int,
    ) -> OLTResult:
        """Read optical signal level from ONU."""
        interface = f"{rack}/{shelf}/{slot}/{port}"
        return self._exec([
            f"show pon power attenuation gpon-onu_{interface}:{onu_index}",
        ])
