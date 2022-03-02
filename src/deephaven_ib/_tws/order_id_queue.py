"""An event queue for managing order ID requests."""

from threading import Event, Thread
from time import sleep
from typing import List, Callable, TYPE_CHECKING

from .._internal.threading import LoggingLock
from .._internal.trace import trace_all_threads_str
from ..__init__ import OrderIdStrategy

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
            #TODO: debug remove
            trace = trace_all_threads_str()
            print(trace)
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
    _strategy: OrderIdStrategy
    _last_value: int
    _request_thread: Thread

    def __init__(self, client: 'IbTwsClient', strategy:OrderIdStrategy = OrderIdStrategy.RETRY):
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
                print(f"DEBUG: rerequest: event={event}")
                self._client.reqIds(-1)

            sleep(0.01)

    def request(self) -> OrderIdRequest:
        """Requests data from the queue."""

        event = Event()

        with self._lock:
            self._events.append(event)

        print(f"DEBUG: request: event={event}")
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
            print(f"DEBUG: add_value 1: events={self._events} value={value}")
            if self._events:
                self._values.append(value)
                event = self._events.pop(0)
                print(f"DEBUG: add_value 2: event={event} value={value}")
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
