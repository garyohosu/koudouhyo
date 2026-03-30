"""Tests for ConfigLoader service."""
import json
import pytest
from pathlib import Path

from koudouhyo.services.config_loader import ConfigLoader


def write_config(path: Path, data: dict) -> str:
    config_file = path / "config.json"
    config_file.write_text(json.dumps(data), encoding="utf-8")
    return str(config_file)


def test_tc_cl_01_normal_config(tmp_path):
    """TC-CL-01: Normal config.json returns shared_root and admin_users."""
    config_path = write_config(tmp_path, {
        "shared_root": "\\\\server\\share\\koudouhyo",
        "admin_users": ["yamada"],
    })
    loader = ConfigLoader(config_path=config_path)
    settings = loader.load()
    assert settings.shared_root == "\\\\server\\share\\koudouhyo"
    assert settings.admin_users == ["yamada"]


def test_tc_cl_02_empty_admin_users(tmp_path):
    """TC-CL-02: admin_users can be an empty list."""
    config_path = write_config(tmp_path, {
        "shared_root": "\\\\server\\share",
        "admin_users": [],
    })
    loader = ConfigLoader(config_path=config_path)
    settings = loader.load()
    assert settings.admin_users == []


def test_tc_cl_03_file_not_found(tmp_path):
    """TC-CL-03: Non-existent file raises FileNotFoundError."""
    loader = ConfigLoader(config_path=str(tmp_path / "nonexistent.json"))
    with pytest.raises(FileNotFoundError):
        loader.load()


def test_tc_cl_04_invalid_json(tmp_path):
    """TC-CL-04: Invalid JSON raises JSONDecodeError or ValueError."""
    config_file = tmp_path / "config.json"
    config_file.write_text("not valid json{{{", encoding="utf-8")
    loader = ConfigLoader(config_path=str(config_file))
    with pytest.raises((json.JSONDecodeError, ValueError)):
        loader.load()


def test_tc_cl_05_missing_shared_root(tmp_path):
    """TC-CL-05: Missing shared_root key raises KeyError or ValueError."""
    config_path = write_config(tmp_path, {"admin_users": ["yamada"]})
    loader = ConfigLoader(config_path=config_path)
    with pytest.raises((KeyError, ValueError)):
        loader.load()
