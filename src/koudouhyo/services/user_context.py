"""User context service for koudouhyo application."""
from __future__ import annotations

import os


class UserContext:
    def __init__(self) -> None:
        self.windows_user_name: str = os.environ.get("USERNAME", "unknown")
        self.pc_name: str = os.environ.get("COMPUTERNAME", "unknown")

    def is_admin(self, admin_users: list[str]) -> bool:
        """Check if the current user is in the admin users list."""
        return self.windows_user_name in admin_users
