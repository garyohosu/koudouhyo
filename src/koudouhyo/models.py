"""Data models and enums for koudouhyo application."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional


class AttendanceStatus(str, Enum):
    IN_OFFICE = "出社中"
    LEFT = "退社済み"


class LocationStatus(str, Enum):
    AT_DESK = "在席"
    OUT = "外出"
    BUSINESS_TRIP = "出張"
    VACATION = "休暇"
    MEETING = "会議"
    DIRECT_START = "直行"
    DIRECT_HOME = "直帰"
    OTHER = "その他"


@dataclass
class EmployeeMaster:
    employee_name: str = ""
    extension_number: str = ""
    display_order: int = 0
    id: Optional[int] = None
    department: str = ""
    is_active: int = 1
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class CurrentStatus:
    employee_id: int = 0
    attendance_status: AttendanceStatus = AttendanceStatus.IN_OFFICE
    location_status: LocationStatus = LocationStatus.AT_DESK
    updated_by: str = ""
    updated_at: str = ""
    id: Optional[int] = None
    destination: str = ""
    note: str = ""


@dataclass
class StatusHistory:
    employee_id: int = 0
    new_attendance_status: str = ""
    new_location_status: str = ""
    updated_by: str = ""
    updated_at: str = ""
    id: Optional[int] = None
    old_attendance_status: Optional[str] = None
    old_location_status: Optional[str] = None
    old_destination: str = ""
    new_destination: str = ""
    old_note: str = ""
    new_note: str = ""


@dataclass
class AppConfig:
    config_key: str = ""
    config_value: str = ""
    id: Optional[int] = None
    updated_at: Optional[str] = None


@dataclass
class LockInfo:
    lock_id: str = ""
    user_name: str = ""
    pc_name: str = ""
    started_at: str = ""
    app_version: str = "1.0.0"


@dataclass
class VersionInfo:
    version: str = ""
    path: str = ""
    notes: str = ""


@dataclass
class AppSettings:
    shared_root: str = ""
    admin_users: list = field(default_factory=list)

    @property
    def db_path(self) -> str:
        return str(Path(self.shared_root) / "koudouhyo.db")

    @property
    def backup_dir(self) -> str:
        return str(Path(self.shared_root) / "backup")

    @property
    def lock_path(self) -> str:
        return str(Path(self.shared_root) / "koudouhyo.lock")

    @property
    def update_json_path(self) -> str:
        return str(Path(self.shared_root) / "latest.json")

    @property
    def server_config_path(self) -> str:
        """Master config on the shared server (admin_users etc.)."""
        return str(Path(self.shared_root) / "config.json")

    @property
    def app_current_path(self) -> str:
        return str(Path(self.shared_root) / "app" / "current")
