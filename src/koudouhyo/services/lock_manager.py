"""Lock manager for koudouhyo application."""
from __future__ import annotations

import json
import threading
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

from koudouhyo.exceptions import LockError
from koudouhyo.models import LockInfo
from koudouhyo.services.user_context import UserContext

LOCK_EXPIRE_MINUTES = 60
HEARTBEAT_INTERVAL_SECONDS = 300  # 5 minutes


class LockManager:
    def __init__(
        self,
        lock_path: str,
        user: UserContext,
        app_version: str = "1.0.0",
    ) -> None:
        self._lock_path = Path(lock_path)
        self._user = user
        self._app_version = app_version
        self._session_lock_id: Optional[str] = None
        self._heartbeat_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def try_acquire(self) -> bool:
        """Try to acquire the lock. Returns True if successful."""
        if self._lock_path.exists():
            if not self.is_expired():
                return False
            # Expired lock: overwrite it
        # Create our lock
        self._session_lock_id = str(uuid.uuid4())
        lock_info = {
            "lock_id": self._session_lock_id,
            "user_name": self._user.windows_user_name,
            "pc_name": self._user.pc_name,
            "started_at": datetime.now(timezone.utc).astimezone().isoformat(),
            "app_version": self._app_version,
        }
        self._lock_path.write_text(json.dumps(lock_info), encoding="utf-8")
        self._start_heartbeat()
        return True

    def release(self) -> None:
        """Release the lock if it belongs to this session."""
        if not self._lock_path.exists():
            return
        if self._is_own_lock():
            self._stop_heartbeat()
            try:
                self._lock_path.unlink()
            except FileNotFoundError:
                pass
            self._session_lock_id = None

    def is_locked(self) -> bool:
        """Check if the lock file exists and is not expired."""
        if not self._lock_path.exists():
            return False
        return not self.is_expired()

    def is_expired(self) -> bool:
        """Check if the current lock has expired (older than LOCK_EXPIRE_MINUTES)."""
        if not self._lock_path.exists():
            return True
        try:
            mtime = self._lock_path.stat().st_mtime
            mtime_dt = datetime.fromtimestamp(mtime, tz=timezone.utc)
            now = datetime.now(timezone.utc)
            return (now - mtime_dt) >= timedelta(minutes=LOCK_EXPIRE_MINUTES)
        except OSError:
            return True

    def get_lock_info(self) -> Optional[LockInfo]:
        """Get information about the current lock."""
        if not self._lock_path.exists():
            return None
        try:
            data = json.loads(self._lock_path.read_text(encoding="utf-8"))
            return LockInfo(
                lock_id=data.get("lock_id", ""),
                user_name=data.get("user_name", ""),
                pc_name=data.get("pc_name", ""),
                started_at=data.get("started_at", ""),
                app_version=data.get("app_version", "1.0.0"),
            )
        except (json.JSONDecodeError, OSError):
            return None

    def force_release_if_admin(self, admin_users: list[str]) -> bool:
        """Force release the lock if current user is an admin. Returns True if released."""
        if not self._user.is_admin(admin_users):
            return False
        if self._lock_path.exists():
            try:
                self._lock_path.unlink()
            except FileNotFoundError:
                pass
        return True

    def _start_heartbeat(self) -> None:
        """Start the heartbeat thread if not already running."""
        if self._heartbeat_thread is not None and self._heartbeat_thread.is_alive():
            return
        self._stop_event.clear()
        self._heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop, daemon=True
        )
        self._heartbeat_thread.start()

    def _stop_heartbeat(self) -> None:
        """Stop the heartbeat thread."""
        self._stop_event.set()
        if self._heartbeat_thread is not None:
            self._heartbeat_thread.join(timeout=10)
            self._heartbeat_thread = None

    def _heartbeat_loop(self) -> None:
        """Heartbeat loop: update lock timestamp every HEARTBEAT_INTERVAL_SECONDS."""
        while not self._stop_event.wait(HEARTBEAT_INTERVAL_SECONDS):
            self._update_timestamp()

    def _update_timestamp(self) -> None:
        """Update the lock file's modification time if we own the lock."""
        if not self._lock_path.exists():
            return
        if not self._is_own_lock():
            return
        try:
            import os
            now = datetime.now(timezone.utc).timestamp()
            os.utime(str(self._lock_path), (now, now))
        except OSError:
            pass

    def _is_own_lock(self) -> bool:
        """Check if the current lock belongs to this session."""
        if self._session_lock_id is None:
            return False
        info = self.get_lock_info()
        if info is None:
            return False
        return info.lock_id == self._session_lock_id
