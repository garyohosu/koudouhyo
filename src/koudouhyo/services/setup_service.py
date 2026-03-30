"""Initial setup service: create shared folder structure and deploy exe."""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

from koudouhyo.models import AppSettings

# Required subdirectories under shared_root
REQUIRED_DIRS = ["data", "backup", "lock", "update", "app/current", "app/releases"]

NEW_EXE_SUFFIX = "_new.exe"
UPDATE_BAT_NAME = "_update.bat"
VERSION_FILE_NAME = "version.txt"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _parse_version(v: str) -> tuple:
    """Convert "1.2.3" to (1, 2, 3) for comparison."""
    return tuple(map(int, v.strip().split(".")))


def _get_deployed_version(app_settings: AppSettings) -> Optional[str]:
    """Read version from app\\current\\version.txt on the shared folder."""
    version_file = (
        Path(app_settings.shared_root) / "app" / "current" / VERSION_FILE_NAME
    )
    if not version_file.exists():
        return None
    return version_file.read_text(encoding="utf-8").strip()


def _write_deployed_version(app_settings: AppSettings, version: str) -> None:
    version_file = (
        Path(app_settings.shared_root) / "app" / "current" / VERSION_FILE_NAME
    )
    version_file.write_text(version, encoding="utf-8")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

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


def needs_deploy(app_settings: AppSettings, local_version: str) -> bool:
    """Return True if this exe should be deployed to app\\current\\.

    Conditions:
    - Koudouhyo.exe does not exist in app\\current\\  (initial setup)
    - OR local version is newer than the deployed version
    """
    if not getattr(sys, "frozen", False):
        return False

    exe_name = Path(sys.executable).name
    current_exe = Path(app_settings.shared_root) / "app" / "current" / exe_name

    if not current_exe.exists():
        return True  # Initial deploy

    deployed = _get_deployed_version(app_settings)
    if deployed is None:
        return True  # version.txt missing → treat as outdated

    try:
        return _parse_version(local_version) > _parse_version(deployed)
    except (ValueError, TypeError):
        return True  # Unparseable version → re-deploy to be safe


def deploy_to_current(app_settings: AppSettings, local_version: str) -> None:
    """Copy exe and config.json to shared_root\\app\\current\\ and write version.txt."""
    if not getattr(sys, "frozen", False):
        return

    src_exe = Path(sys.executable)
    src_cfg = src_exe.parent / "config.json"
    dst_dir = Path(app_settings.shared_root) / "app" / "current"
    dst_dir.mkdir(parents=True, exist_ok=True)

    shutil.copy2(src_exe, dst_dir / src_exe.name)
    if src_cfg.exists():
        shutil.copy2(src_cfg, dst_dir / "config.json")

    _write_deployed_version(app_settings, local_version)


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
