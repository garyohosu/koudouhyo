"""Migration manager for koudouhyo application."""
from __future__ import annotations

from typing import Optional

from koudouhyo.database import DatabaseManager
from koudouhyo.repositories import AppConfigRepository

CURRENT_SCHEMA_VERSION = "1.0.0"


def _version_tuple(v: str):
    return tuple(map(int, v.split(".")))


class MigrationManager:
    def __init__(self, db: DatabaseManager, config_repo: AppConfigRepository) -> None:
        self._db = db
        self._config_repo = config_repo

    def run_if_needed(self) -> None:
        """Run migrations if schema version is outdated or None."""
        current = self._config_repo.get_schema_version()
        if current is None or _version_tuple(current) < _version_tuple(CURRENT_SCHEMA_VERSION):
            self._apply_migrations(current)
            self._config_repo.set_schema_version(CURRENT_SCHEMA_VERSION)

    def _apply_migrations(self, from_version: Optional[str]) -> None:
        """Apply pending migrations.

        For version None (fresh install): insert initial data if needed.
        """
        if from_version is None:
            # Initial migration: tables are already created by DatabaseManager.connect()
            # Nothing else needed for the initial version
            pass
