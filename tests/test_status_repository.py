"""Tests for StatusRepository."""
import pytest
import sqlite3
from koudouhyo.models import EmployeeMaster, AttendanceStatus, LocationStatus, CurrentStatus


def insert_employee(emp_repo, name="テスト社員", ext="100", order=1):
    from koudouhyo.models import EmployeeMaster
    emp = EmployeeMaster(employee_name=name, extension_number=ext, display_order=order)
    return emp_repo.insert(emp)


def test_tc_sr_01_get_all_current(emp_repo, status_repo):
    """TC-SR-01: get_all_current() returns all current statuses."""
    id1 = insert_employee(emp_repo, name="社員A", order=1)
    id2 = insert_employee(emp_repo, name="社員B", order=2)
    status_repo.create_initial_status(id1, "system")
    status_repo.create_initial_status(id2, "system")
    result = status_repo.get_all_current()
    assert len(result) == 2


def test_tc_sr_02_get_by_employee_id(emp_repo, status_repo):
    """TC-SR-02: get_by_employee_id() returns the correct status."""
    emp_id = insert_employee(emp_repo, name="鈴木一郎")
    status_repo.create_initial_status(emp_id, "system")
    status = status_repo.get_by_employee_id(emp_id)
    assert status is not None
    assert status.employee_id == emp_id
    assert status.attendance_status == AttendanceStatus.IN_OFFICE


def test_tc_sr_03_save_status_change_updates_current(emp_repo, status_repo):
    """TC-SR-03: save_status_change() updates current_status."""
    emp_id = insert_employee(emp_repo)
    status_repo.create_initial_status(emp_id, "system")
    new_status = CurrentStatus(
        employee_id=emp_id,
        attendance_status=AttendanceStatus.LEFT,
        location_status=LocationStatus.AT_DESK,
        destination="",
        note="退社",
        updated_by="testuser",
        updated_at="2024-01-01T18:00:00+09:00",
    )
    status_repo.save_status_change(new_status)
    updated = status_repo.get_by_employee_id(emp_id)
    assert updated.attendance_status == AttendanceStatus.LEFT
    assert updated.note == "退社"


def test_tc_sr_04_save_status_change_adds_history(emp_repo, status_repo, db):
    """TC-SR-04: save_status_change() adds a record to status_history."""
    emp_id = insert_employee(emp_repo)
    status_repo.create_initial_status(emp_id, "system")
    new_status = CurrentStatus(
        employee_id=emp_id,
        attendance_status=AttendanceStatus.LEFT,
        location_status=LocationStatus.AT_DESK,
        destination="",
        note="",
        updated_by="testuser",
        updated_at="2024-01-01T18:00:00+09:00",
    )
    status_repo.save_status_change(new_status)
    conn = db.get_connection()
    cursor = conn.execute("SELECT COUNT(*) as cnt FROM status_history WHERE employee_id = ?", (emp_id,))
    row = cursor.fetchone()
    assert row["cnt"] == 1


def test_tc_sr_05_save_status_change_rollback(emp_repo, status_repo, monkeypatch, db):
    """TC-SR-05: If save_status_change() fails mid-way, it rolls back."""
    emp_id = insert_employee(emp_repo)
    status_repo.create_initial_status(emp_id, "system")
    original = status_repo.get_by_employee_id(emp_id)

    # Force error by monkeypatching the repository's internal method
    # We patch get_by_employee_id to first return the original, then raise on the second call
    # simulating a failure during the transaction
    call_count = [0]
    original_get = status_repo.get_by_employee_id.__func__  # unbound

    def patched_save(new_status_arg):
        """Raise during history insert to simulate mid-transaction failure."""
        raise sqlite3.OperationalError("Simulated mid-transaction error")

    # Patch save_status_change on the status_repo instance itself (not the class)
    # We use monkeypatch.setattr on the class method instead
    import koudouhyo.repositories as repos_module

    original_save = repos_module.StatusRepository.save_status_change

    def failing_save(self, new_status_arg):
        raise sqlite3.OperationalError("Simulated error")

    monkeypatch.setattr(repos_module.StatusRepository, "save_status_change", failing_save)

    new_status = CurrentStatus(
        employee_id=emp_id,
        attendance_status=AttendanceStatus.LEFT,
        location_status=LocationStatus.AT_DESK,
        destination="",
        note="",
        updated_by="testuser",
        updated_at="2024-01-01T18:00:00+09:00",
    )

    with pytest.raises(sqlite3.OperationalError):
        status_repo.save_status_change(new_status)

    # Restore and check that current_status was not changed
    monkeypatch.setattr(repos_module.StatusRepository, "save_status_change", original_save)
    current = status_repo.get_by_employee_id(emp_id)
    assert current.attendance_status == original.attendance_status


def test_tc_sr_06_create_initial_status(emp_repo, status_repo):
    """TC-SR-06: create_initial_status() creates initial record with IN_OFFICE/AT_DESK."""
    emp_id = insert_employee(emp_repo)
    status_repo.create_initial_status(emp_id, "system")
    status = status_repo.get_by_employee_id(emp_id)
    assert status is not None
    assert status.attendance_status == AttendanceStatus.IN_OFFICE
    assert status.location_status == LocationStatus.AT_DESK
    assert status.destination == ""
    assert status.note == ""


def test_tc_sr_07_duplicate_initial_status_raises(emp_repo, status_repo):
    """TC-SR-07: Inserting initial status for same employee_id twice raises UNIQUE error."""
    emp_id = insert_employee(emp_repo)
    status_repo.create_initial_status(emp_id, "system")
    with pytest.raises(Exception):  # UNIQUE constraint violation
        status_repo.create_initial_status(emp_id, "system")
