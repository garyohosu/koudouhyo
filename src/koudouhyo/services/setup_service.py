"""Initial setup service: create shared folder structure and deploy exe."""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

from koudouhyo.models import AppSettings

# Required subdirectories under shared_root
REQUIRED_DIRS = ["data", "backup", "lock", "update", "app/current", "app/releases"]


def ensure_shared_dirs(app_settings: AppSettings) -> None:
    """Create required directories under shared_root if they don't exist."""
    root = Path(app_settings.shared_root)
    for d in REQUIRED_DIRS:
        (root / d).mkdir(parents=True, exist_ok=True)


def is_running_from_current(app_settings: AppSettings) -> bool:
    """Return True if this exe is already running from app\\current\\."""
    if not getattr(sys, "frozen", False):
        return True  # Running as script, skip deployment check
    exe_path = Path(sys.executable).resolve()
    current_path = (Path(app_settings.shared_root) / "app" / "current").resolve()
    return exe_path.parent == current_path


def deploy_to_current(app_settings: AppSettings) -> None:
    """Copy exe and config.json to shared_root\\app\\current\\."""
    if not getattr(sys, "frozen", False):
        return  # Nothing to deploy in script mode

    src_exe = Path(sys.executable)
    src_cfg = src_exe.parent / "config.json"
    dst_dir = Path(app_settings.shared_root) / "app" / "current"
    dst_dir.mkdir(parents=True, exist_ok=True)

    shutil.copy2(src_exe, dst_dir / src_exe.name)
    if src_cfg.exists():
        shutil.copy2(src_cfg, dst_dir / "config.json")
