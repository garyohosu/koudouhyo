"""Tests for DatabaseManager."""
import pytest
from koudouhyo.database import DatabaseManager


def test_tc_db_01_connect_in_memory():
    """TC-DB-01: Can connect to :memory: database."""
    db = DatabaseManager(":memory:")
    db.connect()
    assert db.get_connection() is not None
    db.close()


def test_tc_db_02_foreign_keys_enabled():
    """TC-DB-02: PRAGMA foreign_keys is ON after connect."""
    db = DatabaseManager(":memory:")
    db.connect()
    conn = db.get_connection()
    cursor = conn.execute("PRAGMA foreign_keys")
    row = cursor.fetchone()
    assert row[0] == 1
    db.close()


def test_tc_db_03_close():
    """TC-DB-03: After close(), connection is gone."""
    db = DatabaseManager(":memory:")
    db.connect()
    db.close()
    with pytest.raises(RuntimeError):
        db.get_connection()


def test_tc_db_04_new_file_created(tmp_path):
    """TC-DB-04: Specifying a non-existent path creates a new DB file."""
    db_file = tmp_path / "new_db.db"
    assert not db_file.exists()
    db = DatabaseManager(str(db_file))
    db.connect()
    assert db_file.exists()
    db.close()
