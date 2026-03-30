"""Admin service for koudouhyo application."""
from __future__ import annotations

from koudouhyo.exceptions import LockError
from koudouhyo.models import EmployeeMaster
from koudouhyo.repositories import EmployeeRepository, StatusRepository
from koudouhyo.services.backup_manager import BackupManager
from koudouhyo.services.lock_manager import LockManager


class AdminService:
    def __init__(
        self,
        emp_repo: EmployeeRepository,
        status_repo: StatusRepository,
        backup_mgr: BackupManager,
        lock_mgr: LockManager,
    ) -> None:
        self._emp_repo = emp_repo
        self._status_repo = status_repo
        self._backup_mgr = backup_mgr
        self._lock_mgr = lock_mgr

    def save_employee(self, emp: EmployeeMaster, is_new: bool) -> None:
        """Save employee master data.

        Raises:
            LockError: If lock is not held.
        """
        if not (self._lock_mgr.is_locked() and self._lock_mgr._is_own_lock()):
            raise LockError("Lock is not acquired by this session.")

        self._backup_mgr.run_pre_master_backup()

        if is_new:
            emp_id = self._emp_repo.insert(emp)
            self._status_repo.create_initial_status(
                employee_id=emp_id,
                updated_by="system",
            )
        else:
            self._emp_repo.update(emp)
