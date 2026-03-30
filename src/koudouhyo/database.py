"""Database manager for koudouhyo application."""
from __future__ import annotations

import sqlite3
from typing import Optional


CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS employee_master (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_name TEXT NOT NULL,
    department TEXT DEFAULT '',
    extension_number TEXT NOT NULL DEFAULT '',
    display_order INTEGER NOT NULL DEFAULT 0,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS current_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL UNIQUE,
    attendance_status TEXT NOT NULL,
    location_status TEXT NOT NULL,
    destination TEXT DEFAULT '',
    note TEXT DEFAULT '',
    updated_by TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (employee_id) REFERENCES employee_master(id)
);

CREATE TABLE IF NOT EXISTS status_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL,
    old_attendance_status TEXT,
    new_attendance_status TEXT NOT NULL,
    old_location_status TEXT,
    new_location_status TEXT NOT NULL,
    old_destination TEXT DEFAULT '',
    new_destination TEXT DEFAULT '',
    old_note TEXT DEFAULT '',
    new_note TEXT DEFAULT '',
    updated_by TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (employee_id) REFERENCES employee_master(id)
);

CREATE TABLE IF NOT EXISTS app_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    config_key TEXT NOT NULL UNIQUE,
    config_value TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""


class DatabaseManager:
    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None

    def connect(self) -> None:
        """Connect to SQLite database and initialize schema."""
        self._conn = sqlite3.connect(self._db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.execute("PRAGMA journal_mode = DELETE")
        self._conn.commit()
        # Create tables
        self._conn.executescript(CREATE_TABLES_SQL)
        self._conn.commit()

    def close(self) -> None:
        """Close the database connection."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def get_connection(self) -> sqlite3.Connection:
        """Return the current database connection."""
        if self._conn is None:
            raise RuntimeError("Database is not connected. Call connect() first.")
        return self._conn

    def __enter__(self) -> "DatabaseManager":
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
