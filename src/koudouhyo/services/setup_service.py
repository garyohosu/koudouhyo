"""Initial setup service: create shared folder structure and deploy exe."""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from koudouhyo.models import AppSettings

# Required subdirectories under shared_root
REQUIRED_DIRS = ["data", "backup", "lock", "update", "app/current", "app/releases"]

NEW_EXE_SUFFIX = "_new.exe"
UPDATE_BAT_NAME = "_update.bat"


def ensure_shared_dirs(app_settings: AppSettings) -> None:
    """Create required directories under shared_root if they don't exist."""
    root = Path(app_settings.shared_root)
    for d in REQUIRED_DIRS:
        (root / d).mkdir(parents=True, exist_ok=True)


def is_running_from_unc() -> bool:
    """Return True if this exe is running from a UNC path (\\\\server\\...)."""
    if not getattr(sys, "frozen", False):
        return False
    return Path(sys.executable).drive == ""  # UNC paths have no drive letter


def is_running_from_current(app_settings: AppSettings) -> bool:
    """Return True if this exe is running from app\\current\\ on the shared folder."""
    if not getattr(sys, "frozen", False):
        return False
    exe_path = Path(sys.executable).resolve()
    current_path = (Path(app_settings.shared_root) / "app" / "current").resolve()
    try:
        exe_path.relative_to(current_path)
        return True
    except ValueError:
        return False


def deploy_to_current(app_settings: AppSettings) -> None:
    """Copy exe and config.json to shared_root\\app\\current\\ (distribution point)."""
    if not getattr(sys, "frozen", False):
        return

    src_exe = Path(sys.executable)
    src_cfg = src_exe.parent / "config.json"
    dst_dir = Path(app_settings.shared_root) / "app" / "current"
    dst_dir.mkdir(parents=True, exist_ok=True)

    shutil.copy2(src_exe, dst_dir / src_exe.name)
    if src_cfg.exists():
        shutil.copy2(src_cfg, dst_dir / "config.json")


def apply_pending_update() -> None:
    """If Koudouhyo_new.exe exists next to this exe, swap it in via bat and exit.

    Called at the very start of main() before anything else.
    Since the old exe has already exited by the time the bat runs,
    Windows allows the rename.
    """
    if not getattr(sys, "frozen", False):
        return

    exe_path = Path(sys.executable)
    exe_dir = exe_path.parent
    new_exe = exe_dir / (exe_path.stem + NEW_EXE_SUFFIX)

    if not new_exe.exists():
        return

    bat_path = exe_dir / UPDATE_BAT_NAME
    bat_content = (
        "@echo off\n"
        "timeout /t 2 /nobreak >nul\n"
        f'move /y "{new_exe}" "{exe_path}"\n'
        f'start "" "{exe_path}"\n'
        f'del "%~f0"\n'
    )
    bat_path.write_text(bat_content, encoding="cp932")

    subprocess.Popen(
        ["cmd", "/c", str(bat_path)],
        creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
        close_fds=True,
    )
    sys.exit(0)


def stage_update(releases_exe_path: str) -> None:
    """Copy new exe from releases to local folder as Koudouhyo_new.exe.

    The actual swap happens on the next launch via apply_pending_update().
    """
    if not getattr(sys, "frozen", False):
        return

    src = Path(releases_exe_path)
    exe_dir = Path(sys.executable).parent
    new_exe = exe_dir / (Path(sys.executable).stem + NEW_EXE_SUFFIX)
    shutil.copy2(src, new_exe)
