from threading import Lock

_lock_unique_id = Lock()
_last_unique_id = 1


def next_unique_id():
    """Gets the next sequential ID."""
    global _last_unique_id
    _lock_unique_id.acquire()
    _last_unique_id += 1
    _lock_unique_id.release()
    return _last_unique_id
