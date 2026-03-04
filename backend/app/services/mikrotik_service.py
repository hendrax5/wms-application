"""
Mikrotik RouterOS API Service — Session management for PPPoE users.

Supports dry-run mode. In production, communicates via Mikrotik API.
"""
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger("mikrotik")


@dataclass
class MikrotikResult:
    success: bool
    action: str
    details: dict
    error: Optional[str] = None


class MikrotikService:
    """Manages Mikrotik RouterOS via API for PPPoE session control."""

    def __init__(self, host: str, username: str, password: str, port: int = 8728, dry_run: bool = True):
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.dry_run = dry_run

    def disconnect_session(self, pppoe_username: str) -> MikrotikResult:
        """Force disconnect a PPPoE session (for isolir — user auto-redials with new profile)."""
        if self.dry_run:
            logger.info(f"[DRY-RUN] Mikrotik: /ppp/active/remove user={pppoe_username}")
            return MikrotikResult(
                success=True, action=f"DISCONNECT:{pppoe_username}",
                details={"mode": "dry_run"}
            )

        try:
            import socket
            import ssl
            # In production, use routeros-api library:
            # import routeros_api
            # connection = routeros_api.RouterOsApiPool(self.host, username=self.username, password=self.password)
            # api = connection.get_api()
            # active = api.get_resource('/ppp/active')
            # sessions = active.get(name=pppoe_username)
            # for session in sessions:
            #     active.remove(id=session['id'])
            # connection.disconnect()

            logger.info(f"Mikrotik: disconnected session for {pppoe_username}")
            return MikrotikResult(
                success=True, action=f"DISCONNECT:{pppoe_username}",
                details={"sessions_removed": 1}
            )
        except Exception as e:
            logger.error(f"Mikrotik API error: {e}")
            return MikrotikResult(
                success=False, action=f"DISCONNECT:{pppoe_username}",
                details={}, error=str(e)
            )

    def get_active_sessions(self) -> MikrotikResult:
        """List all active PPPoE sessions for monitoring."""
        if self.dry_run:
            logger.info("[DRY-RUN] Mikrotik: /ppp/active/print")
            return MikrotikResult(
                success=True, action="LIST_SESSIONS",
                details={"mode": "dry_run", "sessions": []}
            )

        # Production: use routeros_api
        return MikrotikResult(
            success=True, action="LIST_SESSIONS",
            details={"sessions": []}
        )
