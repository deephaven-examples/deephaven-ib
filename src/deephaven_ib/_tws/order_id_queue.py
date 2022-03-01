"""An event queue for managing order ID requests."""

from threading import Event
from typing import List, Callable
from typing import TYPE_CHECKING

from .._internal.threading import LoggingLock

# Type hints on IbTwsClient cause a circular dependency.
# This conditional import plus a string-based annotation avoids the problem.
if TYPE_CHECKING:
    from .tws_client import IbTwsClient



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

        time_out = 2 * 60.0
        print(f"DEBUG: get: event={self._event}")
        event_happened = self._event.wait(time_out)

        if not event_happened:
            raise Exception(f"OrderIdRequest.get() timed out after {time_out} sec.")

        with self._lock:
            if self._value is None:
                self._value = self._getter()

            return self._value


class OrderIdEventQueue:
    """A thread-safe queue for requesting and getting order IDs."""

    _events: List[Event]
    _values: List[int]
    _lock: LoggingLock

    def __init__(self, client: 'IbTwsClient'):
        self._events = []
        self._values = []
        self._lock = LoggingLock("OrderIdEventQueue")
        self._client = client

    def request(self) -> OrderIdRequest:
        """Requests data from the queue."""

        event = Event()

        with self._lock:
            self._events.append(event)

        print(f"DEBUG: request: event={event}")
        self._client.reqIds(-1)

        return OrderIdRequest(event, self._get)

    def add_value(self, value: int) -> None:
        """Adds a new value to the queue."""

        with self._lock:
            # if is to filter out values requested by ibapi during initialization
            print(f"DEBUG: add_value: events={self._events}")
            if self._events:
                self._values.append(value)
                event = self._events.pop(0)
                print(f"DEBUG: add_value: event={event} value={value}")
                event.set()

    def _get(self) -> int:
        """Gets a value from the queue."""

        with self._lock:
            return self._values.pop(0)
