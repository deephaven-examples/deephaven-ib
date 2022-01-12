"""An event queue for managing order ID requests."""

from threading import Event
from typing import List, Callable

from .._internal.threading import LoggingLock


class OrderIdRequest:
    """An order ID request."""

    _event: Event
    _getter: Callable[[], int]
    _value: int
    _lock: LoggingLock

    def __init__(self, event: Event, getter: Callable[[], int]):
        self._event = event
        self._getter = getter
        self._value = None
        self._lock = LoggingLock("OrderIdRequest")

    def get(self) -> int:
        """A blocking call to get the order ID."""

        self._event.wait()

        with self._lock:
            if not self._value:
                self._value = self._getter()

            return self._value


class OrderIdEventQueue:
    """A thread-safe queue for requesting and getting order IDs."""

    _events: List[Event]
    _values: List[int]
    _lock: LoggingLock

    def __init__(self):
        self._events = []
        self._values = []
        self._lock = LoggingLock("OrderIdEventQueue")

    def request(self) -> OrderIdRequest:
        """Requests data from the queue."""

        event = Event()

        with self._lock:
            self._events.append(event)

        return OrderIdRequest(event, self._get)

    def add_value(self, value: int) -> None:
        """Adds a new value to the queue."""

        with self._lock:
            self._values.append(value)
            event = self._events.pop(0)
            event.set()

    def _get(self) -> int:
        """Gets a value from the queue."""

        with self._lock:
            return self._values.pop(0)
