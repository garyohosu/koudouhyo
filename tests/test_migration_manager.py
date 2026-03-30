"""Tests for MigrationManager."""
import pytest
from unittest.mock import patch, MagicMock

from koudouhyo.services.migration_manager import MigrationManager, CURRENT_SCHEMA_VERSION


def test_tc_mm_01_no_migration_if_current(db, config_repo):
    """TC-MM-01: No migration if schema_version is already current."""
    config_repo.set_schema_version(CURRENT_SCHEMA_VERSION)
    mgr = MigrationManager(db, config_repo)
    # Should not change anything
    mgr.run_if_needed()
    assert config_repo.get_schema_version() == CURRENT_SCHEMA_VERSION


def test_tc_mm_02_migration_runs_if_none(db, config_repo):
    """TC-MM-02: Migration runs when schema_version is None."""
    assert config_repo.get_schema_version() is None
    mgr = MigrationManager(db, config_repo)
    mgr.run_if_needed()
    assert config_repo.get_schema_version() == CURRENT_SCHEMA_VERSION


def test_tc_mm_03_schema_version_updated_after_migration(db, config_repo):
    """TC-MM-03: schema_version is set to CURRENT_SCHEMA_VERSION after migration."""
    mgr = MigrationManager(db, config_repo)
    mgr.run_if_needed()
    assert config_repo.get_schema_version() == CURRENT_SCHEMA_VERSION


def test_tc_mm_04_migration_rollback_on_failure(db, config_repo, monkeypatch):
    """TC-MM-04: If _apply_migrations() raises, schema_version is not updated."""
    def failing_apply(from_version):
        raise RuntimeError("Migration failed")

    mgr = MigrationManager(db, config_repo)
    monkeypatch.setattr(mgr, "_apply_migrations", failing_apply)

    with pytest.raises(RuntimeError):
        mgr.run_if_needed()

    # schema_version should still be None since migration failed
    assert config_repo.get_schema_version() is None
