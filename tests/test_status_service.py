"""Tests for StatusService."""
import pytest
from unittest.mock import MagicMock, patch

from koudouhyo.exceptions import LockError
from koudouhyo.models import AttendanceStatus, CurrentStatus, LocationStatus
from koudouhyo.services.status_service import StatusService
from koudouhyo.services.user_context import UserContext


def make_user(username="testuser"):
    ctx = UserContext.__new__(UserContext)
    ctx.windows_user_name = username
    ctx.pc_name = "TESTPC"
    return ctx


def make_lock_mgr(is_locked=True, is_own=True):
    mgr = MagicMock()
    mgr.is_locked.return_value = is_locked
    mgr._is_own_lock.return_value = is_own
    return mgr


def make_status_repo(has_current=True, emp_id=1):
    repo = MagicMock()
    if has_current:
        repo.get_by_employee_id.return_value = CurrentStatus(
            employee_id=emp_id,
            attendance_status=AttendanceStatus.IN_OFFICE,
            location_status=LocationStatus.AT_DESK,
            destination="",
            note="",
            updated_by="system",
            updated_at="2024-01-01T09:00:00+09:00",
        )
    else:
        repo.get_by_employee_id.return_value = None
    return repo


def test_tc_ss_01_change_status_with_lock(db, emp_repo, status_repo):
    """TC-SS-01: change_status() updates DB when lock is held."""
    from koudouhyo.models import EmployeeMaster
    emp = EmployeeMaster(employee_name="田中", extension_number="200", display_order=1)
    emp_id = emp_repo.insert(emp)
    status_repo.create_initial_status(emp_id, "system")

    user = make_user("yamada")
    lock_mgr = make_lock_mgr(is_locked=True, is_own=True)
    service = StatusService(status_repo, lock_mgr, user)

    service.change_status(
        employee_id=emp_id,
        attendance_status=AttendanceStatus.LEFT,
        location_status=LocationStatus.AT_DESK,
        destination="",
        note="退社",
    )
    updated = status_repo.get_by_employee_id(emp_id)
    assert updated.attendance_status == AttendanceStatus.LEFT


def test_tc_ss_02_change_to_left(db, emp_repo, status_repo):
    """TC-SS-02: Changing to LEFT updates attendance_status to LEFT."""
    from koudouhyo.models import EmployeeMaster
    emp = EmployeeMaster(employee_name="鈴木", extension_number="201", display_order=1)
    emp_id = emp_repo.insert(emp)
    status_repo.create_initial_status(emp_id, "system")

    user = make_user()
    lock_mgr = make_lock_mgr()
    service = StatusService(status_repo, lock_mgr, user)

    service.change_status(
        employee_id=emp_id,
        attendance_status=AttendanceStatus.LEFT,
        location_status=LocationStatus.AT_DESK,
        destination="",
        note="",
    )
    updated = status_repo.get_by_employee_id(emp_id)
    assert updated.attendance_status == AttendanceStatus.LEFT


def test_tc_ss_03_updated_by_is_username(db, emp_repo, status_repo):
    """TC-SS-03: updated_by is set to UserContext.windows_user_name."""
    from koudouhyo.models import EmployeeMaster
    emp = EmployeeMaster(employee_name="佐藤", extension_number="202", display_order=1)
    emp_id = emp_repo.insert(emp)
    status_repo.create_initial_status(emp_id, "system")

    user = make_user("specific_user")
    lock_mgr = make_lock_mgr()
    service = StatusService(status_repo, lock_mgr, user)

    service.change_status(
        employee_id=emp_id,
        attendance_status=AttendanceStatus.IN_OFFICE,
        location_status=LocationStatus.OUT,
        destination="client",
        note="",
    )
    updated = status_repo.get_by_employee_id(emp_id)
    assert updated.updated_by == "specific_user"


def test_tc_ss_04_raises_if_lock_not_held():
    """TC-SS-04: change_status() raises LockError when lock is not held."""
    repo = make_status_repo(has_current=True)
    lock_mgr = make_lock_mgr(is_locked=False, is_own=False)
    user = make_user()
    service = StatusService(repo, lock_mgr, user)

    with pytest.raises(LockError):
        service.change_status(
            employee_id=1,
            attendance_status=AttendanceStatus.IN_OFFICE,
            location_status=LocationStatus.AT_DESK,
            destination="",
            note="",
        )


def test_tc_ss_05_raises_if_employee_not_found():
    """TC-SS-05: change_status() raises ValueError for nonexistent employee_id."""
    repo = make_status_repo(has_current=False)
    lock_mgr = make_lock_mgr()
    user = make_user()
    service = StatusService(repo, lock_mgr, user)

    with pytest.raises(ValueError):
        service.change_status(
            employee_id=9999,
            attendance_status=AttendanceStatus.IN_OFFICE,
            location_status=LocationStatus.AT_DESK,
            destination="",
            note="",
        )
