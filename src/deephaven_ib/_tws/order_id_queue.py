"""An event queue for managing order ID requests."""

from threading import Event, Thread
from time import sleep
from enum import Enum
from typing import List, Callable, TYPE_CHECKING

from .._internal.threading import LoggingLock
from .._internal.trace import trace_all_threads_str

# Type hints on IbTwsClient cause a circular dependency.
# This conditional import plus a string-based annotation avoids the problem.
if TYPE_CHECKING:
    from .tws_client import IbTwsClient


class OrderIdStrategy(Enum):
    """Strategy used to obtain order IDs."""

    def __new__(cls, retry: bool, tws_request: bool):
        obj = object.__new__(cls)
        obj.retry = retry
        obj.tws_request = tws_request
        return obj

    INCREMENT = (False, False)
    """Use the initial order ID and increment the value upon every call.  This is fast, but it may fail for multiple, concurrent sessions."""
    BASIC = (False, True)
    """Request a new order ID from TWS every time one is needed."""
    RETRY = (True, True)
    """Request a new order ID from TWS every time one is needed.  Retry if TWS does not respond quickly.  TWS seems to have a bug where it does not always respond."""


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

        time_out = 60.0
        event_happened = self._event.wait(time_out)

        if not event_happened:
            trace = trace_all_threads_str()
            msg = f"OrderIdRequest.get() timed out after {time_out} sec.  A possible deadlock or TWS bug was detected!  You may be able to avoid this problem by using a different OrderIdStrategy.  Please create an issue at https://github.com/deephaven-examples/deephaven-ib/issues containing this error message\n{trace}\n"
            raise Exception(msg)

        with self._lock:
            if self._value is None:
                self._value = self._getter()

            return self._value


class OrderIdEventQueue:
    """A thread-safe queue for requesting and getting order IDs."""

    _events: List[Event]
    _values: List[int]
    _lock: LoggingLock
    _strategy: OrderIdStrategy
    _last_value: int
    _request_thread: Thread

    def __init__(self, client: 'IbTwsClient', strategy: OrderIdStrategy):
        self._events = []
        self._values = []
        self._lock = LoggingLock("OrderIdEventQueue")
        self._client = client
        self._strategy = strategy
        self._last_value = None

        if strategy.retry:
            self._request_thread = Thread(name="OrderIdEventQueueRetry", target=self._retry, daemon=True)
            self._request_thread.start()

    def _retry(self):
        """Re-requests IDs if there is no response."""

        while True:
            for event in self._events:
                self._client.reqIds(-1)

            sleep(0.01)

    def request(self) -> OrderIdRequest:
        """Requests data from the queue."""

        event = Event()

        with self._lock:
            self._events.append(event)

        if self._strategy.tws_request:
            self._client.reqIds(-1)
        else:
            self._increment_value()

        return OrderIdRequest(event, self._get)

    def add_value(self, value: int) -> None:
        """Adds a new value to the queue."""

        with self._lock:
            # Upon startup, add_value is called, to set the initial value
            self._last_value = value

            # if is to filter out values requested by ibapi during initialization
            if self._events:
                self._values.append(value)
                event = self._events.pop(0)
                event.set()

    def _increment_value(self) -> None:
        """Increments the latest value and adds the value to the queue."""

        with self._lock:
            if self._events:
                self._values.append(self._last_value)
                self._last_value += 1
                event = self._events.pop(0)
                event.set()

    def _get(self) -> int:
        """Gets a value from the queue."""

        with self._lock:
            return self._values.pop(0)
