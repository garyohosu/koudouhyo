"""Tests for VersionChecker."""
import json
import pytest
from pathlib import Path

from koudouhyo.services.version_checker import VersionChecker


def write_version_json(tmp_path: Path, data: dict) -> str:
    json_file = tmp_path / "latest.json"
    json_file.write_text(json.dumps(data), encoding="utf-8")
    return str(json_file)


def test_tc_vc_01_has_update(tmp_path):
    """TC-VC-01: current=1.0.0, latest=1.1.0 -> has_update=True."""
    json_path = write_version_json(tmp_path, {"version": "1.1.0", "path": "/path/to/app", "notes": "update"})
    checker = VersionChecker(json_path, "1.0.0")
    result = checker.check()
    assert result.has_update is True
    assert result.latest.version == "1.1.0"


def test_tc_vc_02_no_update_same_version(tmp_path):
    """TC-VC-02: current=1.1.0, latest=1.1.0 -> has_update=False."""
    json_path = write_version_json(tmp_path, {"version": "1.1.0", "path": "", "notes": ""})
    checker = VersionChecker(json_path, "1.1.0")
    result = checker.check()
    assert result.has_update is False


def test_tc_vc_03_no_update_current_newer(tmp_path):
    """TC-VC-03: current=1.2.0, latest=1.1.0 -> has_update=False."""
    json_path = write_version_json(tmp_path, {"version": "1.1.0", "path": "", "notes": ""})
    checker = VersionChecker(json_path, "1.2.0")
    result = checker.check()
    assert result.has_update is False


def test_tc_vc_04_file_not_found(tmp_path):
    """TC-VC-04: File not found -> has_update=False (no exception)."""
    checker = VersionChecker(str(tmp_path / "nonexistent.json"), "1.0.0")
    result = checker.check()
    assert result.has_update is False


def test_tc_vc_05_invalid_json(tmp_path):
    """TC-VC-05: Invalid JSON raises an exception."""
    json_file = tmp_path / "latest.json"
    json_file.write_text("not json{{", encoding="utf-8")
    checker = VersionChecker(str(json_file), "1.0.0")
    with pytest.raises(Exception):
        checker.check()
