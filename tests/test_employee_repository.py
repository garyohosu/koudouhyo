"""Tests for EmployeeRepository."""
import pytest
from koudouhyo.models import EmployeeMaster


def make_employee(**kwargs) -> EmployeeMaster:
    defaults = dict(employee_name="テスト太郎", extension_number="100", display_order=1)
    defaults.update(kwargs)
    return EmployeeMaster(**defaults)


def test_tc_er_01_get_all_active_only(emp_repo):
    """TC-ER-01: get_all_active() returns only is_active=1."""
    emp_repo.insert(make_employee(employee_name="有効社員", is_active=1, display_order=1))
    emp_repo.insert(make_employee(employee_name="無効社員", is_active=0, display_order=2))
    result = emp_repo.get_all_active()
    names = [e.employee_name for e in result]
    assert "有効社員" in names
    assert "無効社員" not in names


def test_tc_er_02_get_all(emp_repo):
    """TC-ER-02: get_all() returns all employees regardless of is_active."""
    emp_repo.insert(make_employee(employee_name="有効社員", is_active=1, display_order=1))
    emp_repo.insert(make_employee(employee_name="無効社員", is_active=0, display_order=2))
    result = emp_repo.get_all()
    assert len(result) == 2


def test_tc_er_03_get_by_id(emp_repo):
    """TC-ER-03: get_by_id() returns a single employee."""
    emp_id = emp_repo.insert(make_employee(employee_name="山田花子"))
    emp = emp_repo.get_by_id(emp_id)
    assert emp is not None
    assert emp.employee_name == "山田花子"
    assert emp.id == emp_id


def test_tc_er_04_not_found_returns_none(emp_repo):
    """TC-ER-04: get_by_id() returns None for nonexistent ID."""
    result = emp_repo.get_by_id(9999)
    assert result is None


def test_tc_er_05_insert(emp_repo):
    """TC-ER-05: insert() adds a new employee and returns an ID."""
    emp = make_employee(employee_name="新規社員")
    emp_id = emp_repo.insert(emp)
    assert emp_id is not None
    assert emp_id > 0
    fetched = emp_repo.get_by_id(emp_id)
    assert fetched.employee_name == "新規社員"


def test_tc_er_06_update(emp_repo):
    """TC-ER-06: update() modifies an existing employee."""
    emp_id = emp_repo.insert(make_employee(employee_name="旧名前"))
    emp = emp_repo.get_by_id(emp_id)
    emp.employee_name = "新名前"
    emp.department = "営業部"
    emp_repo.update(emp)
    updated = emp_repo.get_by_id(emp_id)
    assert updated.employee_name == "新名前"
    assert updated.department == "営業部"


def test_tc_er_07_display_order_asc(emp_repo):
    """TC-ER-07: get_all_active() returns employees sorted by display_order ascending."""
    emp_repo.insert(make_employee(employee_name="C", display_order=3))
    emp_repo.insert(make_employee(employee_name="A", display_order=1))
    emp_repo.insert(make_employee(employee_name="B", display_order=2))
    result = emp_repo.get_all_active()
    names = [e.employee_name for e in result]
    assert names == ["A", "B", "C"]
