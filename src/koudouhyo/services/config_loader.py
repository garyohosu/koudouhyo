"""Configuration loader for koudouhyo application."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

from koudouhyo.models import AppSettings


def _default_config_path() -> str:
    """Return config.json path that works both as script and PyInstaller exe."""
    if getattr(sys, "frozen", False):
        # Running as PyInstaller bundle: look next to the exe
        return str(Path(sys.executable).parent / "config.json")
    else:
        # Running as script: project root (4 levels up from this file)
        return str(Path(__file__).parent.parent.parent.parent / "config.json")


class ConfigLoader:
    CURRENT_DIR_CONFIG = "config.json"

    def __init__(self, config_path: Optional[str] = None) -> None:
        if config_path is not None:
            self._config_path = config_path
        else:
            self._config_path = _default_config_path()

    def load(self) -> AppSettings:
        """Load configuration from JSON file and return AppSettings.

        Raises:
            FileNotFoundError: If config file does not exist.
            JSONDecodeError: If config file contains invalid JSON.
            KeyError: If required keys are missing.
        """
        path = Path(self._config_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {self._config_path}")

        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        if "shared_root" not in data:
            raise KeyError("'shared_root' is required in config.json")

        shared_root = data["shared_root"]
        admin_users = data.get("admin_users", [])

        return AppSettings(shared_root=shared_root, admin_users=admin_users)
