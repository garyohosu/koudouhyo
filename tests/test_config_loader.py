"""Tests for ConfigLoader service (two-stage loading)."""
import json
import pytest
from pathlib import Path

from koudouhyo.services.config_loader import ConfigLoader


def write_local_config(path: Path, data: dict) -> str:
    path.mkdir(parents=True, exist_ok=True)
    config_file = path / "config.json"
    config_file.write_text(json.dumps(data), encoding="utf-8")
    return str(config_file)


def write_server_config(shared_root: Path, data: dict) -> None:
    shared_root.mkdir(parents=True, exist_ok=True)
    (shared_root / "config.json").write_text(
        json.dumps(data), encoding="utf-8"
    )


# ---------------------------------------------------------------------------
# Stage 1: local config
# ---------------------------------------------------------------------------

def test_tc_cl_01_local_only_no_server_config(tmp_path):
    """TC-CL-01: Local config with shared_root only; server config absent → admin_users=[]."""
    shared_root = tmp_path / "server"
    config_path = write_local_config(tmp_path / "local", {"shared_root": str(shared_root)})
    settings = ConfigLoader(config_path=config_path).load()
    assert settings.shared_root == str(shared_root)
    assert settings.admin_users == []


def test_tc_cl_02_server_config_provides_admin_users(tmp_path):
    """TC-CL-02: Server config.json supplies admin_users."""
    shared_root = tmp_path / "server"
    write_server_config(shared_root, {"admin_users": ["yamada", "suzuki"]})
    config_path = write_local_config(tmp_path / "local", {"shared_root": str(shared_root)})
    settings = ConfigLoader(config_path=config_path).load()
    assert settings.admin_users == ["yamada", "suzuki"]


def test_tc_cl_03_server_config_empty_admin_users(tmp_path):
    """TC-CL-03: Server config with empty admin_users list."""
    shared_root = tmp_path / "server"
    write_server_config(shared_root, {"admin_users": []})
    config_path = write_local_config(tmp_path / "local", {"shared_root": str(shared_root)})
    settings = ConfigLoader(config_path=config_path).load()
    assert settings.admin_users == []


def test_tc_cl_04_server_config_unreachable_continues(tmp_path):
    """TC-CL-04: Server config unreadable (bad JSON) → continues with admin_users=[]."""
    shared_root = tmp_path / "server"
    shared_root.mkdir(parents=True)
    (shared_root / "config.json").write_text("INVALID JSON", encoding="utf-8")
    config_path = write_local_config(tmp_path / "local", {"shared_root": str(shared_root)})
    settings = ConfigLoader(config_path=config_path).load()
    assert settings.admin_users == []


# ---------------------------------------------------------------------------
# Stage 1 error cases
# ---------------------------------------------------------------------------

def test_tc_cl_05_local_file_not_found(tmp_path):
    """TC-CL-05: Missing local config.json → FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        ConfigLoader(config_path=str(tmp_path / "nonexistent.json")).load()


def test_tc_cl_06_local_invalid_json(tmp_path):
    """TC-CL-06: Invalid local JSON → JSONDecodeError."""
    config_file = tmp_path / "config.json"
    config_file.write_text("not valid json{{{", encoding="utf-8")
    with pytest.raises((json.JSONDecodeError, ValueError)):
        ConfigLoader(config_path=str(config_file)).load()


def test_tc_cl_07_missing_shared_root(tmp_path):
    """TC-CL-07: Local config missing shared_root → KeyError."""
    config_path = write_local_config(tmp_path, {"other_key": "value"})
    with pytest.raises((KeyError, ValueError)):
        ConfigLoader(config_path=config_path).load()
