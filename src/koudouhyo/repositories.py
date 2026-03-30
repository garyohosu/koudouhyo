"""Repository classes for koudouhyo application."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from koudouhyo.database import DatabaseManager
from koudouhyo.models import (
    AppConfig,
    AttendanceStatus,
    CurrentStatus,
    EmployeeMaster,
    LocationStatus,
    StatusHistory,
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat()


class EmployeeRepository:
    def __init__(self, db: DatabaseManager) -> None:
        self._db = db

    def get_all_active(self) -> list[EmployeeMaster]:
        """Return all active employees ordered by display_order."""
        conn = self._db.get_connection()
        cursor = conn.execute(
            "SELECT * FROM employee_master WHERE is_active = 1 ORDER BY display_order ASC"
        )
        return [self._row_to_employee(row) for row in cursor.fetchall()]

    def get_all(self) -> list[EmployeeMaster]:
        """Return all employees regardless of is_active."""
        conn = self._db.get_connection()
        cursor = conn.execute(
            "SELECT * FROM employee_master ORDER BY display_order ASC"
        )
        return [self._row_to_employee(row) for row in cursor.fetchall()]

    def get_by_id(self, id: int) -> Optional[EmployeeMaster]:
        """Return employee by id, or None if not found."""
        conn = self._db.get_connection()
        cursor = conn.execute(
            "SELECT * FROM employee_master WHERE id = ?", (id,)
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return self._row_to_employee(row)

    def insert(self, emp: EmployeeMaster) -> int:
        """Insert a new employee and return the created id."""
        now = _now_iso()
        created_at = emp.created_at or now
        updated_at = emp.updated_at or now
        conn = self._db.get_connection()
        cursor = conn.execute(
            """INSERT INTO employee_master
               (employee_name, department, extension_number, display_order, is_active, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                emp.employee_name,
                emp.department,
                emp.extension_number,
                emp.display_order,
                emp.is_active,
                created_at,
                updated_at,
            ),
        )
        conn.commit()
        return cursor.lastrowid

    def update(self, emp: EmployeeMaster) -> None:
        """Update an existing employee."""
        now = _now_iso()
        updated_at = emp.updated_at or now
        conn = self._db.get_connection()
        conn.execute(
            """UPDATE employee_master
               SET employee_name = ?, department = ?, extension_number = ?,
                   display_order = ?, is_active = ?, updated_at = ?
               WHERE id = ?""",
            (
                emp.employee_name,
                emp.department,
                emp.extension_number,
                emp.display_order,
                emp.is_active,
                updated_at,
                emp.id,
            ),
        )
        conn.commit()

    @staticmethod
    def _row_to_employee(row) -> EmployeeMaster:
        return EmployeeMaster(
            id=row["id"],
            employee_name=row["employee_name"],
            department=row["department"] or "",
            extension_number=row["extension_number"] or "",
            display_order=row["display_order"],
            is_active=row["is_active"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


class StatusRepository:
    def __init__(self, db: DatabaseManager) -> None:
        self._db = db

    def get_all_current(self) -> list[CurrentStatus]:
        """Return all current statuses."""
        conn = self._db.get_connection()
        cursor = conn.execute("SELECT * FROM current_status")
        return [self._row_to_status(row) for row in cursor.fetchall()]

    def get_by_employee_id(self, employee_id: int) -> Optional[CurrentStatus]:
        """Return current status for a specific employee."""
        conn = self._db.get_connection()
        cursor = conn.execute(
            "SELECT * FROM current_status WHERE employee_id = ?", (employee_id,)
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return self._row_to_status(row)

    def save_status_change(self, new_status: CurrentStatus) -> None:
        """
        Save a status change in a single transaction:
        - INSERT into status_history
        - UPDATE current_status
        """
        conn = self._db.get_connection()
        old = self.get_by_employee_id(new_status.employee_id)

        with conn:
            # Insert history
            conn.execute(
                """INSERT INTO status_history
                   (employee_id, old_attendance_status, new_attendance_status,
                    old_location_status, new_location_status,
                    old_destination, new_destination,
                    old_note, new_note,
                    updated_by, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    new_status.employee_id,
                    old.attendance_status.value if old else None,
                    new_status.attendance_status.value
                    if isinstance(new_status.attendance_status, AttendanceStatus)
                    else new_status.attendance_status,
                    old.location_status.value if old else None,
                    new_status.location_status.value
                    if isinstance(new_status.location_status, LocationStatus)
                    else new_status.location_status,
                    old.destination if old else "",
                    new_status.destination,
                    old.note if old else "",
                    new_status.note,
                    new_status.updated_by,
                    new_status.updated_at,
                ),
            )
            # Update current status
            conn.execute(
                """UPDATE current_status
                   SET attendance_status = ?, location_status = ?,
                       destination = ?, note = ?,
                       updated_by = ?, updated_at = ?
                   WHERE employee_id = ?""",
                (
                    new_status.attendance_status.value
                    if isinstance(new_status.attendance_status, AttendanceStatus)
                    else new_status.attendance_status,
                    new_status.location_status.value
                    if isinstance(new_status.location_status, LocationStatus)
                    else new_status.location_status,
                    new_status.destination,
                    new_status.note,
                    new_status.updated_by,
                    new_status.updated_at,
                    new_status.employee_id,
                ),
            )

    def create_initial_status(self, employee_id: int, updated_by: str) -> None:
        """Create initial status record (IN_OFFICE, AT_DESK) for a new employee."""
        now = _now_iso()
        conn = self._db.get_connection()
        conn.execute(
            """INSERT INTO current_status
               (employee_id, attendance_status, location_status,
                destination, note, updated_by, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                employee_id,
                AttendanceStatus.IN_OFFICE.value,
                LocationStatus.AT_DESK.value,
                "",
                "",
                updated_by,
                now,
            ),
        )
        conn.commit()

    @staticmethod
    def _row_to_status(row) -> CurrentStatus:
        return CurrentStatus(
            id=row["id"],
            employee_id=row["employee_id"],
            attendance_status=AttendanceStatus(row["attendance_status"]),
            location_status=LocationStatus(row["location_status"]),
            destination=row["destination"] or "",
            note=row["note"] or "",
            updated_by=row["updated_by"],
            updated_at=row["updated_at"],
        )


class AppConfigRepository:
    def __init__(self, db: DatabaseManager) -> None:
        self._db = db

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get a config value by key, returning default if not found."""
        conn = self._db.get_connection()
        cursor = conn.execute(
            "SELECT config_value FROM app_config WHERE config_key = ?", (key,)
        )
        row = cursor.fetchone()
        if row is None:
            return default
        return row["config_value"]

    def set(self, key: str, value: str) -> None:
        """Upsert a config value."""
        now = _now_iso()
        conn = self._db.get_connection()
        conn.execute(
            """INSERT INTO app_config (config_key, config_value, updated_at)
               VALUES (?, ?, ?)
               ON CONFLICT(config_key) DO UPDATE SET config_value = excluded.config_value,
                                                      updated_at = excluded.updated_at""",
            (key, value, now),
        )
        conn.commit()

    def get_schema_version(self) -> Optional[str]:
        """Get the current schema version."""
        return self.get("schema_version")

    def set_schema_version(self, version: str) -> None:
        """Set the schema version."""
        self.set("schema_version", version)
