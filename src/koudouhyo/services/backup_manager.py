"""Backup manager for koudouhyo application."""
from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

from koudouhyo.exceptions import BackupError

MAX_GENERATIONS = 30


class BackupManager:
    def __init__(self, db_path: str, backup_dir: str) -> None:
        self._db_path = Path(db_path)
        self._backup_dir = Path(backup_dir)

    def run_startup_backup(self) -> None:
        """Run backup at startup. Skip if today's backup already exists."""
        if self._has_today_backup():
            return
        self._create_backup()
        self._rotate()

    def run_pre_master_backup(self) -> None:
        """Run backup before master data changes. Always creates a new backup."""
        self._create_backup()
        self._rotate()

    def _has_today_backup(self) -> bool:
        """Check if a backup for today already exists."""
        today_str = datetime.now().strftime("%Y%m%d")
        prefix = f"koudouhyo_{today_str}_"
        if not self._backup_dir.exists():
            return False
        for f in self._backup_dir.iterdir():
            if f.name.startswith(prefix) and f.name.endswith(".db"):
                return True
        return False

    def _create_backup(self) -> None:
        """Create a new backup of the database."""
        if not self._db_path.exists():
            raise FileNotFoundError(f"Database file not found: {self._db_path}")
        self._backup_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"koudouhyo_{timestamp}.db"
        dest = self._backup_dir / backup_name
        shutil.copy2(str(self._db_path), str(dest))

    def _rotate(self) -> None:
        """Remove oldest backups if count exceeds MAX_GENERATIONS."""
        if not self._backup_dir.exists():
            return
        backups = sorted(
            [f for f in self._backup_dir.iterdir() if f.name.startswith("koudouhyo_") and f.name.endswith(".db")],
            key=lambda f: f.name,
        )
        while len(backups) > MAX_GENERATIONS:
            oldest = backups.pop(0)
            try:
                oldest.unlink()
            except OSError:
                pass
