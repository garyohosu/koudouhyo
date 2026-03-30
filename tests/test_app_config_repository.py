"""Tests for AppConfigRepository."""
import pytest


def test_tc_ac_01_get_schema_version_none(config_repo):
    """TC-AC-01: get_schema_version() returns None when not set."""
    result = config_repo.get_schema_version()
    assert result is None


def test_tc_ac_02_set_and_get_schema_version(config_repo):
    """TC-AC-02: set_schema_version() then get_schema_version() returns the set value."""
    config_repo.set_schema_version("1.0.0")
    result = config_repo.get_schema_version()
    assert result == "1.0.0"


def test_tc_ac_03_get_nonexistent_key_returns_none(config_repo):
    """TC-AC-03: Getting a non-existent key returns None."""
    result = config_repo.get("nonexistent_key")
    assert result is None


def test_tc_ac_upsert(config_repo):
    """AppConfigRepository.set() is an upsert."""
    config_repo.set("my_key", "value1")
    config_repo.set("my_key", "value2")
    result = config_repo.get("my_key")
    assert result == "value2"
