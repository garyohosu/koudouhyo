"""Status service for koudouhyo application."""
from __future__ import annotations

from datetime import datetime, timezone

from koudouhyo.exceptions import LockError
from koudouhyo.models import AttendanceStatus, CurrentStatus, LocationStatus
from koudouhyo.repositories import StatusRepository
from koudouhyo.services.lock_manager import LockManager
from koudouhyo.services.user_context import UserContext


class StatusService:
    def __init__(
        self,
        status_repo: StatusRepository,
        lock_mgr: LockManager,
        user_ctx: UserContext,
    ) -> None:
        self._status_repo = status_repo
        self._lock_mgr = lock_mgr
        self._user_ctx = user_ctx

    def change_status(
        self,
        employee_id: int,
        attendance_status: AttendanceStatus,
        location_status: LocationStatus,
        destination: str,
        note: str,
    ) -> None:
        """Change an employee's status.

        Raises:
            LockError: If the lock is not held by this session.
            ValueError: If the employee_id doesn't exist.
        """
        if not (self._lock_mgr.is_locked() and self._lock_mgr._is_own_lock()):
            raise LockError("Lock is not acquired by this session.")

        # Check employee exists
        current = self._status_repo.get_by_employee_id(employee_id)
        if current is None:
            raise ValueError(f"Employee with id {employee_id} not found in current_status.")

        now = datetime.now(timezone.utc).astimezone().isoformat()
        new_status = CurrentStatus(
            employee_id=employee_id,
            attendance_status=attendance_status,
            location_status=location_status,
            destination=destination,
            note=note,
            updated_by=self._user_ctx.windows_user_name,
            updated_at=now,
        )
        self._status_repo.save_status_change(new_status)
