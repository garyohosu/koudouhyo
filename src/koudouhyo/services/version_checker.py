"""Version checker for koudouhyo application."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from koudouhyo.models import VersionInfo


@dataclass
class VersionCheckResult:
    has_update: bool
    latest: Optional[VersionInfo] = None


class VersionChecker:
    def __init__(self, update_json_path: str, current_version: str) -> None:
        self._update_json_path = Path(update_json_path)
        self._current_version = current_version

    def check(self) -> VersionCheckResult:
        """Check if an update is available.

        Returns VersionCheckResult with has_update=False if file doesn't exist.
        Raises JSONDecodeError if file contains invalid JSON.
        """
        if not self._update_json_path.exists():
            return VersionCheckResult(has_update=False)

        data = json.loads(self._update_json_path.read_text(encoding="utf-8"))

        latest_version = data.get("version", "")
        path = data.get("path", "")
        notes = data.get("notes", "")

        latest_info = VersionInfo(version=latest_version, path=path, notes=notes)

        has_update = self._compare_versions(latest_version, self._current_version)

        return VersionCheckResult(has_update=has_update, latest=latest_info)

    @staticmethod
    def _compare_versions(latest: str, current: str) -> bool:
        """Return True if latest > current."""
        try:
            latest_tuple = tuple(map(int, latest.split(".")))
            current_tuple = tuple(map(int, current.split(".")))
            return latest_tuple > current_tuple
        except (ValueError, AttributeError):
            return False
