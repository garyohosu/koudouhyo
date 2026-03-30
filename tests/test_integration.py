"""Integration tests for koudouhyo application."""
import pytest
from pathlib import Path
from unittest.mock import MagicMock

from koudouhyo.database import DatabaseManager
from koudouhyo.repositories import EmployeeRepository, StatusRepository, AppConfigRepository
from koudouhyo.models import EmployeeMaster, AttendanceStatus, LocationStatus
from koudouhyo.services.migration_manager import MigrationManager, CURRENT_SCHEMA_VERSION
from koudouhyo.services.status_service import StatusService
from koudouhyo.services.admin_service import AdminService
from koudouhyo.services.user_context import UserContext
from koudouhyo.services.lock_manager import LockManager


def make_user(username="integtest"):
    ctx = UserContext.__new__(UserContext)
    ctx.windows_user_name = username
    ctx.pc_name = "INTEGPC"
    return ctx


def make_lock_mgr(is_locked=True, is_own=True):
    mgr = MagicMock()
    mgr.is_locked.return_value = is_locked
    mgr._is_own_lock.return_value = is_own
    return mgr


@pytest.fixture
def integration_db(tmp_path):
    """Real file DB for integration tests."""
    db_path = tmp_path / "integ_test.db"
    db = DatabaseManager(str(db_path))
    db.connect()
    yield db
    db.close()


def test_tc_int_01_full_migration_and_schema_version(integration_db):
    """TC-INT-01: Migration runs and sets schema version."""
    config_repo = AppConfigRepository(integration_db)
    mgr = MigrationManager(integration_db, config_repo)
    mgr.run_if_needed()
    assert config_repo.get_schema_version() == CURRENT_SCHEMA_VERSION


def test_tc_int_02_add_employee_and_check_status(integration_db):
    """TC-INT-02: Adding an employee via AdminService creates initial status."""
    emp_repo = EmployeeRepository(integration_db)
    status_repo = StatusRepository(integration_db)
    backup_mgr = MagicMock()
    lock_mgr = make_lock_mgr()
    admin_service = AdminService(emp_repo, status_repo, backup_mgr, lock_mgr)

    emp = EmployeeMaster(employee_name="統合テスト社員", extension_number="300", display_order=1)
    admin_service.save_employee(emp, is_new=True)

    employees = emp_repo.get_all_active()
    assert len(employees) == 1
    emp_id = employees[0].id

    status = status_repo.get_by_employee_id(emp_id)
    assert status is not None
    assert status.attendance_status == AttendanceStatus.IN_OFFICE
    assert status.location_status == LocationStatus.AT_DESK


def test_tc_int_03_change_status_recorded_in_history(integration_db):
    """TC-INT-03: Status change is recorded in status_history."""
    emp_repo = EmployeeRepository(integration_db)
    status_repo = StatusRepository(integration_db)
    backup_mgr = MagicMock()
    lock_mgr = make_lock_mgr()
    user = make_user("integ_user")

    # Add employee
    admin_service = AdminService(emp_repo, status_repo, backup_mgr, lock_mgr)
    emp = EmployeeMaster(employee_name="履歴テスト", extension_number="301", display_order=1)
    admin_service.save_employee(emp, is_new=True)
    emp_id = emp_repo.get_all()[0].id

    # Change status
    status_service = StatusService(status_repo, lock_mgr, user)
    status_service.change_status(
        employee_id=emp_id,
        attendance_status=AttendanceStatus.LEFT,
        location_status=LocationStatus.AT_DESK,
        destination="",
        note="退社テスト",
    )

    # Check history
    conn = integration_db.get_connection()
    cursor = conn.execute("SELECT COUNT(*) as cnt FROM status_history WHERE employee_id = ?", (emp_id,))
    row = cursor.fetchone()
    assert row["cnt"] == 1


def test_tc_int_04_update_employee_master(integration_db):
    """TC-INT-04: Updating employee master works correctly."""
    emp_repo = EmployeeRepository(integration_db)
    status_repo = StatusRepository(integration_db)
    backup_mgr = MagicMock()
    lock_mgr = make_lock_mgr()
    admin_service = AdminService(emp_repo, status_repo, backup_mgr, lock_mgr)

    # Insert
    emp = EmployeeMaster(employee_name="更新テスト", extension_number="302", display_order=1)
    admin_service.save_employee(emp, is_new=True)
    emp_id = emp_repo.get_all()[0].id

    # Update
    existing = emp_repo.get_by_id(emp_id)
    existing.employee_name = "更新後の名前"
    existing.department = "開発部"
    admin_service.save_employee(existing, is_new=False)

    updated = emp_repo.get_by_id(emp_id)
    assert updated.employee_name == "更新後の名前"
    assert updated.department == "開発部"


def test_tc_int_05_multiple_employees_and_statuses(integration_db):
    """TC-INT-05: Multiple employees with different statuses."""
    emp_repo = EmployeeRepository(integration_db)
    status_repo = StatusRepository(integration_db)
    backup_mgr = MagicMock()
    lock_mgr = make_lock_mgr()
    user = make_user("multi_user")

    admin_service = AdminService(emp_repo, status_repo, backup_mgr, lock_mgr)
    status_service = StatusService(status_repo, lock_mgr, user)

    # Add 3 employees
    for i in range(3):
        emp = EmployeeMaster(employee_name=f"社員{i+1}", extension_number=str(400 + i), display_order=i + 1)
        admin_service.save_employee(emp, is_new=True)

    employees = emp_repo.get_all_active()
    assert len(employees) == 3

    # Change one employee's status
    emp_id = employees[0].id
    status_service.change_status(
        employee_id=emp_id,
        attendance_status=AttendanceStatus.LEFT,
        location_status=LocationStatus.AT_DESK,
        destination="",
        note="",
    )

    all_statuses = status_repo.get_all_current()
    assert len(all_statuses) == 3

    changed = status_repo.get_by_employee_id(emp_id)
    assert changed.attendance_status == AttendanceStatus.LEFT

    # The other employees should still be IN_OFFICE
    for emp in employees[1:]:
        st = status_repo.get_by_employee_id(emp.id)
        assert st.attendance_status == AttendanceStatus.IN_OFFICE
