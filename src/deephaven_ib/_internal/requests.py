"""Functionality for working with requests."""

from .threading import LoggingLock

_lock_unique_id: LoggingLock = LoggingLock(name="next_unique_id")
_last_unique_id: int = 1


def next_unique_id():
    """Gets the next sequential ID."""
    global _lock_unique_id, _last_unique_id
    with _lock_unique_id:
        _last_unique_id += 1
        return _last_unique_id
