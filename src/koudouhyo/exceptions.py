"""Custom exceptions for koudouhyo application."""


class LockError(Exception):
    """Raised when lock acquisition/release fails."""
    pass


class ConfigError(Exception):
    """Raised when configuration loading fails."""
    pass


class BackupError(Exception):
    """Raised when backup operation fails."""
    pass
