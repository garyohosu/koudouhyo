import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from koudouhyo.database import DatabaseManager
from koudouhyo.repositories import EmployeeRepository, StatusRepository, AppConfigRepository


@pytest.fixture
def db():
    """In-memory DB for unit tests."""
    db = DatabaseManager(":memory:")
    db.connect()
    yield db
    db.close()


@pytest.fixture
def emp_repo(db):
    return EmployeeRepository(db)


@pytest.fixture
def status_repo(db):
    return StatusRepository(db)


@pytest.fixture
def config_repo(db):
    return AppConfigRepository(db)


@pytest.fixture
def tmp_db(tmp_path):
    """Real file DB for integration tests."""
    db_path = tmp_path / "test.db"
    db = DatabaseManager(str(db_path))
    db.connect()
    yield db
    db.close()


@pytest.fixture
def sample_employee():
    from koudouhyo.models import EmployeeMaster
    return EmployeeMaster(employee_name="山田太郎", extension_number="101", display_order=1)
