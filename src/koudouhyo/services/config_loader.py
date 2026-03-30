"""Configuration loader for koudouhyo application.

Two-stage loading:
1. Local config.json  : contains only shared_root (minimum to reach server)
2. Server config.json : contains admin_users and other shared settings
                        Located at {shared_root}\\config.json
                        Managed by admin; shared across all clients.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

from koudouhyo.models import AppSettings


def _default_config_path() -> str:
    """Return local config.json path for both exe and script mode."""
    if getattr(sys, "frozen", False):
        # Running as PyInstaller exe: look next to the exe
        return str(Path(sys.executable).parent / "config.json")
    else:
        # Running as script: project root
        return str(Path(__file__).parent.parent.parent.parent / "config.json")


def _read_json(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


class ConfigLoader:
    def __init__(self, config_path: Optional[str] = None) -> None:
        self._config_path = config_path if config_path is not None else _default_config_path()

    def load(self) -> AppSettings:
        """Load configuration via two-stage reading.

        Stage 1 – Local config.json (required):
            { "shared_root": "\\\\server\\share\\koudouhyo" }

        Stage 2 – Server config.json at {shared_root}\\config.json (optional):
            { "admin_users": ["yamada", "suzuki"] }
            If unreachable, admin_users defaults to [].

        Raises:
            FileNotFoundError: Local config.json not found.
            json.JSONDecodeError: Local config.json is invalid JSON.
            KeyError: shared_root key is missing.
        """
        # --- Stage 1: local config ---
        local_data = _read_json(self._config_path)
        if "shared_root" not in local_data:
            raise KeyError("'shared_root' is required in config.json")
        shared_root = local_data["shared_root"]

        # --- Stage 2: server config (best-effort) ---
        server_config_path = str(Path(shared_root) / "config.json")
        server_data: dict = {}
        try:
            server_data = _read_json(server_config_path)
        except (FileNotFoundError, json.JSONDecodeError):
            pass  # Server not reachable or config not yet created → use defaults

        admin_users = server_data.get("admin_users", [])

        return AppSettings(shared_root=shared_root, admin_users=admin_users)
