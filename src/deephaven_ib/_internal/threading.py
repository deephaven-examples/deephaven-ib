"""Functionality for working multi-threaded code."""

import inspect
import logging
import threading
import time
from typing import Dict, Tuple

from .._internal.trace import trace_str


class DeadlockMonitor:
    """A monitor for deadlocked LoggingLocks."""

    timeout_sec: float
    sleep_sec: float
    locks: Dict[int, Tuple[float, int, str, str]]
    _lock: threading.Lock
    _thread: threading.Thread

    def __init__(self, timeout_sec: float, sleep_sec: float):
        self.timeout_sec = timeout_sec
        self.sleep_sec = sleep_sec
        self.locks = {}
        self._lock = threading.Lock()

        self._thread = threading.Thread(name="DeadlockMonitor", target=self._run, daemon=True)
        self._thread.start()
        setattr(self, "deadlock_monitor_thread", self._thread)

    def _run(self):
        while True:
            self._check_for_deadlocks()
            time.sleep(self.sleep_sec)

    def _check_for_deadlocks(self):
        with self._lock:
            t = time.time()

            for k, v in self.locks.items():
                if t - v[0] > self.timeout_sec:
                    self._log_deadlock()
                    return

    def _log_deadlock(self):
        t = time.time()
        msg = "A likely deadlock was detected!  Please create an issue at https://github.com/deephaven-examples/deephaven-ib/issues containing this error message\nOpen locks:\n"

        for k, v in self.locks.items():
            msg += f"age_sec={t-v[0]} lock_id={v[1]} name={v[2]}\n"

        msg += "\n\nStacks:\n\n"

        for k, v in self.locks.items():
            msg += f"age_sec={t-v[0]} lock_id={v[1]} name={v[2]}\n{v[3]}\n"

        logging.error(msg)

    def acquire(self, lock_id: int, name: str, stack: str) -> None:
        with self._lock:
            self.locks[lock_id] = (time.time(), lock_id, name, stack)

    def release(self, lock_id: int):
        with self._lock:
            # pop is used here instead of del, because there are instances where the locks are released multiple times
            self.locks.pop(lock_id, None)


_lock_id: int = 0
_lock: threading.Lock = threading.Lock()
_deadlock_monitor: DeadlockMonitor = DeadlockMonitor(3 * 60.0, 10.0)


def _next_lock_id() -> int:
    global _lock_id

    with _lock:
        _lock_id += 1
        return _lock_id


class LoggingLock(object):
    """A threading lock that logs lock acquisition and release."""

    name: str
    log_stack: bool

    def __init__(self, name: str, lock=None, log_level=logging.DEBUG, log_stack: bool = False):
        if lock is None:
            lock = threading.Lock()

        self.name = str(name)
        self.log_level = log_level
        self.lock = lock
        self.log_stack = log_stack
        self.id = _next_lock_id()
        self._log(f"{inspect.stack()[1][3]} created {self.name}")

    def _log(self, msg: str) -> None:
        if self.log_stack:
            msg = f"{msg}: lock_id={self.id} thread_id={threading.get_ident()}\n{trace_str()}"
        else:
            msg = f"{msg}: lock_id={self.id} thread_id={threading.get_ident()}"

        logging.log(self.log_level, msg)

    def acquire(self, blocking=True):
        self._log(f"{inspect.stack()[1][3]} trying to acquire {self.name}")

        if _deadlock_monitor:
            _deadlock_monitor.acquire(self.id, self.name, trace_str())

        ret = self.lock.acquire(blocking)

        if ret:
            self._log(f"{inspect.stack()[1][3]} acquired {self.name}")
        else:
            self._log(f"{inspect.stack()[1][3]} non-blocking acquire of {self.name} lock failed")

        return ret

    def release(self):
        self._log(f"{inspect.stack()[1][3]} releasing {self.name}")

        if _deadlock_monitor:
            _deadlock_monitor.release(self.id)

        self.lock.release()

    def __enter__(self):
        self.acquire()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
        return False  # True causes exceptions to be swallowed.  False causes exceptions to be handled.
