"""Functionality for working with requests."""

from .order_id_queue import OrderIdEventQueue
from .._internal.threading import LoggingLock


class RequestIdManager:
    """A manager for getting unique request IDs that are well behaved."""

    _lock: LoggingLock
    _id: int

    def __init__(self):
        self._lock = LoggingLock("RequestManager")
        self._id = 0

    def next_id(self) -> int:
        """Gets the next sequential ID for a generic request."""
        with self._lock:
            self._id += 1
            return self._id

    def next_order_id(self, order_id_queue: OrderIdEventQueue) -> int:
        """Gets the next sequential ID for an order request."""
        with self._lock:
            request = order_id_queue.request()
            oid = request.get()
            max_id = max(oid, self._id + 1)
            self._id = max_id
            return max_id
