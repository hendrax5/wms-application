"""
Radius Database Service — Manages FreeRadius radcheck/radreply tables.

Supports dry-run mode which logs SQL without executing.
In production, connects directly to the FreeRadius MySQL/PostgreSQL database.
"""
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger("radius")


@dataclass
class RadiusResult:
    success: bool
    action: str
    details: dict
    error: Optional[str] = None


class RadiusService:
    """Manages FreeRadius radcheck/radreply tables for PPPoE authentication."""

    def __init__(self, db_url: str, dry_run: bool = True):
        self.db_url = db_url
        self.dry_run = dry_run
        self._engine = None

    def _get_engine(self):
        """Lazy-init SQLAlchemy engine for Radius DB."""
        if not self._engine and not self.dry_run and self.db_url:
            from sqlalchemy import create_engine
            self._engine = create_engine(self.db_url)
        return self._engine

    def _exec_sql(self, statements: list[tuple[str, dict]], action: str) -> RadiusResult:
        """Execute SQL statements against the Radius database."""
        if self.dry_run:
            for sql, params in statements:
                logger.info(f"[DRY-RUN] Radius SQL: {sql} | params={params}")
            return RadiusResult(
                success=True, action=action,
                details={"mode": "dry_run", "statements": len(statements)}
            )

        engine = self._get_engine()
        if not engine:
            return RadiusResult(success=False, action=action, details={}, error="Radius DB not configured")

        try:
            from sqlalchemy import text
            with engine.connect() as conn:
                for sql, params in statements:
                    conn.execute(text(sql), params)
                conn.commit()
            return RadiusResult(success=True, action=action, details={"statements": len(statements)})
        except Exception as e:
            logger.error(f"Radius DB error: {e}")
            return RadiusResult(success=False, action=action, details={}, error=str(e))

    def create_pppoe_user(
        self,
        username: str,
        password: str,
        mac_address: Optional[str],
        mikrotik_group: str,
        framed_pool: str,
    ) -> RadiusResult:
        """Create PPPoE user in Radius with MAC binding (Caller-ID)."""
        statements = [
            # radcheck: Password
            (
                "INSERT INTO radcheck (username, attribute, op, value) VALUES (:user, 'Cleartext-Password', ':=', :pwd)",
                {"user": username, "pwd": password},
            ),
            # radreply: Mikrotik-Group
            (
                "INSERT INTO radreply (username, attribute, op, value) VALUES (:user, 'Mikrotik-Group', ':=', :grp)",
                {"user": username, "grp": mikrotik_group},
            ),
            # radreply: Framed-Pool
            (
                "INSERT INTO radreply (username, attribute, op, value) VALUES (:user, 'Framed-Pool', ':=', :pool)",
                {"user": username, "pool": framed_pool},
            ),
        ]

        # Add MAC binding if provided (anti-fraud: Caller-ID)
        if mac_address:
            statements.append((
                "INSERT INTO radcheck (username, attribute, op, value) VALUES (:user, 'Calling-Station-Id', ':=', :mac)",
                {"user": username, "mac": mac_address},
            ))

        return self._exec_sql(statements, f"CREATE_USER:{username}")

    def update_user_group(self, username: str, new_group: str) -> RadiusResult:
        """Update Mikrotik-Group for isolir/reconnect."""
        statements = [
            (
                "UPDATE radreply SET value = :grp WHERE username = :user AND attribute = 'Mikrotik-Group'",
                {"user": username, "grp": new_group},
            ),
        ]
        return self._exec_sql(statements, f"UPDATE_GROUP:{username}→{new_group}")

    def delete_user(self, username: str) -> RadiusResult:
        """Delete all Radius entries for a user (rollback/cleanup)."""
        statements = [
            ("DELETE FROM radcheck WHERE username = :user", {"user": username}),
            ("DELETE FROM radreply WHERE username = :user", {"user": username}),
        ]
        return self._exec_sql(statements, f"DELETE_USER:{username}")
