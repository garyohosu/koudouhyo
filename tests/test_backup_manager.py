"""Tests for BackupManager."""
import re
import time
import pytest
from pathlib import Path
from datetime import datetime
from unittest.mock import patch

from koudouhyo.services.backup_manager import BackupManager, MAX_GENERATIONS


def make_db_file(tmp_path: Path) -> Path:
    db_file = tmp_path / "koudouhyo.db"
    db_file.write_bytes(b"SQLite test data")
    return db_file


def make_backup_dir(tmp_path: Path) -> Path:
    backup_dir = tmp_path / "backup"
    backup_dir.mkdir()
    return backup_dir


def test_tc_bm_01_startup_backup_no_existing(tmp_path):
    """TC-BM-01: run_startup_backup() creates backup when no today's backup exists."""
    db_file = make_db_file(tmp_path)
    backup_dir = make_backup_dir(tmp_path)
    mgr = BackupManager(str(db_file), str(backup_dir))
    mgr.run_startup_backup()
    backups = list(backup_dir.iterdir())
    assert len(backups) == 1


def test_tc_bm_02_startup_backup_skips_if_today_exists(tmp_path):
    """TC-BM-02: run_startup_backup() skips if today's backup already exists."""
    db_file = make_db_file(tmp_path)
    backup_dir = make_backup_dir(tmp_path)
    # Create a fake today's backup
    today_str = datetime.now().strftime("%Y%m%d")
    existing = backup_dir / f"koudouhyo_{today_str}_120000.db"
    existing.write_bytes(b"old backup")
    mgr = BackupManager(str(db_file), str(backup_dir))
    mgr.run_startup_backup()
    backups = list(backup_dir.iterdir())
    assert len(backups) == 1  # Still only one (no new backup was created)


def test_tc_bm_03_pre_master_backup_always_creates(tmp_path):
    """TC-BM-03: run_pre_master_backup() always creates a new backup."""
    db_file = make_db_file(tmp_path)
    backup_dir = make_backup_dir(tmp_path)
    # Create a fake today's backup
    today_str = datetime.now().strftime("%Y%m%d")
    existing = backup_dir / f"koudouhyo_{today_str}_120000.db"
    existing.write_bytes(b"old backup")
    mgr = BackupManager(str(db_file), str(backup_dir))
    mgr.run_pre_master_backup()
    backups = list(backup_dir.iterdir())
    assert len(backups) == 2  # Original + new one


def test_tc_bm_04_rotation_deletes_oldest(tmp_path):
    """TC-BM-04: When backup count exceeds 30, oldest is deleted."""
    db_file = make_db_file(tmp_path)
    backup_dir = make_backup_dir(tmp_path)
    # Create MAX_GENERATIONS existing backups
    for i in range(MAX_GENERATIONS):
        fname = f"koudouhyo_2024010{i // 10}{i % 10}_120000.db"
        (backup_dir / fname).write_bytes(b"old backup")
    mgr = BackupManager(str(db_file), str(backup_dir))
    mgr.run_pre_master_backup()
    backups = sorted([f.name for f in backup_dir.iterdir()])
    assert len(backups) == MAX_GENERATIONS
    # The oldest (20240100_120000) should be gone, newer ones remain
    assert not (backup_dir / "koudouhyo_20240100_120000.db").exists()


def test_tc_bm_05_backup_filename_format(tmp_path):
    """TC-BM-05: Backup file name matches koudouhyo_YYYYMMDD_HHMMSS.db format."""
    db_file = make_db_file(tmp_path)
    backup_dir = make_backup_dir(tmp_path)
    mgr = BackupManager(str(db_file), str(backup_dir))
    mgr.run_pre_master_backup()
    backups = list(backup_dir.iterdir())
    assert len(backups) == 1
    pattern = re.compile(r"koudouhyo_\d{8}_\d{6}\.db")
    assert pattern.match(backups[0].name)


def test_tc_bm_06_db_not_found(tmp_path):
    """TC-BM-06: run_pre_master_backup() raises FileNotFoundError if DB doesn't exist."""
    backup_dir = make_backup_dir(tmp_path)
    mgr = BackupManager(str(tmp_path / "nonexistent.db"), str(backup_dir))
    with pytest.raises(FileNotFoundError):
        mgr.run_pre_master_backup()
