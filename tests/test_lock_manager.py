"""Tests for LockManager."""
import json
import os
import time
import pytest
from pathlib import Path
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

from koudouhyo.services.lock_manager import LockManager, LOCK_EXPIRE_MINUTES
from koudouhyo.services.user_context import UserContext


def make_user(username="testuser", pcname="testpc") -> UserContext:
    ctx = UserContext.__new__(UserContext)
    ctx.windows_user_name = username
    ctx.pc_name = pcname
    return ctx


def make_lock_manager(tmp_path, username="testuser", pcname="testpc", version="1.0.0") -> LockManager:
    lock_file = tmp_path / "test.lock"
    user = make_user(username, pcname)
    return LockManager(str(lock_file), user, app_version=version)


def test_tc_lm_01_acquire_when_no_file(tmp_path):
    """TC-LM-01: try_acquire() returns True when no lock file exists."""
    mgr = make_lock_manager(tmp_path)
    result = mgr.try_acquire()
    mgr._stop_heartbeat()
    assert result is True


def test_tc_lm_02_lock_file_contains_required_fields(tmp_path):
    """TC-LM-02: Lock file contains lock_id, user_name, pc_name, started_at, app_version."""
    lock_file = tmp_path / "test.lock"
    user = make_user("yamada", "MYPC")
    mgr = LockManager(str(lock_file), user, app_version="2.0.0")
    mgr.try_acquire()
    mgr._stop_heartbeat()
    data = json.loads(lock_file.read_text(encoding="utf-8"))
    assert "lock_id" in data
    assert data["user_name"] == "yamada"
    assert data["pc_name"] == "MYPC"
    assert "started_at" in data
    assert data["app_version"] == "2.0.0"


def test_tc_lm_03_acquire_fails_when_valid_lock_exists(tmp_path):
    """TC-LM-03: try_acquire() returns False when a valid lock exists."""
    # Create a lock from another session
    lock_file = tmp_path / "test.lock"
    lock_data = {
        "lock_id": "other-session-id",
        "user_name": "otheruser",
        "pc_name": "OTHERPC",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "app_version": "1.0.0",
    }
    lock_file.write_text(json.dumps(lock_data), encoding="utf-8")

    user = make_user("testuser", "TESTPC")
    mgr = LockManager(str(lock_file), user)
    result = mgr.try_acquire()
    assert result is False


def test_tc_lm_04_not_expired_59_minutes(tmp_path):
    """TC-LM-04: Lock created 59 minutes ago is not expired."""
    lock_file = tmp_path / "test.lock"
    lock_data = {
        "lock_id": "some-id",
        "user_name": "user",
        "pc_name": "PC",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "app_version": "1.0.0",
    }
    lock_file.write_text(json.dumps(lock_data), encoding="utf-8")
    # Set mtime to 59 minutes ago
    past = (datetime.now(timezone.utc) - timedelta(minutes=59)).timestamp()
    os.utime(str(lock_file), (past, past))

    user = make_user()
    mgr = LockManager(str(lock_file), user)
    assert mgr.is_expired() is False


def test_tc_lm_05_expired_61_minutes(tmp_path):
    """TC-LM-05: Lock with mtime 61 minutes ago is expired."""
    lock_file = tmp_path / "test.lock"
    lock_data = {
        "lock_id": "some-id",
        "user_name": "user",
        "pc_name": "PC",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "app_version": "1.0.0",
    }
    lock_file.write_text(json.dumps(lock_data), encoding="utf-8")
    # Set mtime to 61 minutes ago
    past = (datetime.now(timezone.utc) - timedelta(minutes=61)).timestamp()
    os.utime(str(lock_file), (past, past))

    user = make_user()
    mgr = LockManager(str(lock_file), user)
    assert mgr.is_expired() is True


def test_tc_lm_06_release_own_lock(tmp_path):
    """TC-LM-06: release() deletes the file when it's the session's own lock."""
    mgr = make_lock_manager(tmp_path)
    mgr.try_acquire()
    assert mgr._lock_path.exists()
    mgr.release()
    assert not mgr._lock_path.exists()


def test_tc_lm_07_release_other_lock(tmp_path):
    """TC-LM-07: release() does not delete the file if it's another session's lock."""
    lock_file = tmp_path / "test.lock"
    lock_data = {
        "lock_id": "other-session-id",
        "user_name": "otheruser",
        "pc_name": "OTHERPC",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "app_version": "1.0.0",
    }
    lock_file.write_text(json.dumps(lock_data), encoding="utf-8")

    user = make_user()
    mgr = LockManager(str(lock_file), user)
    # Don't call try_acquire, so _session_lock_id is None
    mgr.release()
    assert lock_file.exists()


def test_tc_lm_08_force_release_admin_expired(tmp_path):
    """TC-LM-08: Admin + expired lock -> force_release_if_admin() returns True."""
    lock_file = tmp_path / "test.lock"
    lock_data = {
        "lock_id": "other-id",
        "user_name": "someuser",
        "pc_name": "SOMEPC",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "app_version": "1.0.0",
    }
    lock_file.write_text(json.dumps(lock_data), encoding="utf-8")
    past = (datetime.now(timezone.utc) - timedelta(minutes=61)).timestamp()
    os.utime(str(lock_file), (past, past))

    user = make_user(username="adminuser")
    mgr = LockManager(str(lock_file), user)
    result = mgr.force_release_if_admin(admin_users=["adminuser"])
    assert result is True
    assert not lock_file.exists()


def test_tc_lm_09_force_release_non_admin(tmp_path):
    """TC-LM-09: Non-admin -> force_release_if_admin() returns False."""
    lock_file = tmp_path / "test.lock"
    lock_data = {
        "lock_id": "other-id",
        "user_name": "someuser",
        "pc_name": "SOMEPC",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "app_version": "1.0.0",
    }
    lock_file.write_text(json.dumps(lock_data), encoding="utf-8")

    user = make_user(username="regularuser")
    mgr = LockManager(str(lock_file), user)
    result = mgr.force_release_if_admin(admin_users=["adminuser"])
    assert result is False
    assert lock_file.exists()


def test_tc_lm_10_release_no_file(tmp_path):
    """TC-LM-10: release() does not raise when no lock file exists."""
    mgr = make_lock_manager(tmp_path)
    # No try_acquire, no file
    mgr.release()  # Should not raise


def test_tc_lm_11_heartbeat_start_stop(tmp_path):
    """TC-LM-11: Heartbeat thread starts and stops correctly."""
    mgr = make_lock_manager(tmp_path)
    mgr.try_acquire()
    assert mgr._heartbeat_thread is not None
    assert mgr._heartbeat_thread.is_alive()
    # Save reference before stop (stop sets it to None)
    thread_ref = mgr._heartbeat_thread
    mgr._stop_heartbeat()
    assert not thread_ref.is_alive()
    mgr.release()


def test_tc_lm_12_heartbeat_no_duplicate(tmp_path):
    """TC-LM-12: Starting heartbeat twice doesn't create duplicate threads."""
    mgr = make_lock_manager(tmp_path)
    mgr.try_acquire()
    first_thread = mgr._heartbeat_thread
    mgr._start_heartbeat()  # Should be no-op since thread is alive
    assert mgr._heartbeat_thread is first_thread
    mgr._stop_heartbeat()
    mgr.release()
