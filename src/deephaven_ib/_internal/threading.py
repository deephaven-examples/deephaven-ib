"""Functionality for working multi-threaded code."""

import inspect
import logging
import threading

from .._internal.trace import trace_str


class LoggingLock(object):
    """A threading lock that logs lock acquisition and release."""

    def __init__(self, name, lock=None, log=logging, log_stack=False):
        if lock is None:
            lock = threading.Lock()

        self.name = str(name)
        self.log = log
        self.lock = lock
        self.log_stack = log_stack
        self._log(f"{inspect.stack()[1][3]} created {self.name}")

    def _log(self, msg: str) -> None:
        if self.log_stack:
            msg = f"{msg}\n{trace_str()}"

        self.log.debug(msg)
        # TODO: remove print
        # print(msg)

    def acquire(self, blocking=True):
        self._log(f"{inspect.stack()[1][3]} trying to acquire {self.name}")
        ret = self.lock.acquire(blocking)

        if ret:
            self._log(f"{inspect.stack()[1][3]} acquired {self.name}")
        else:
            self._log(f"{inspect.stack()[1][3]} non-blocking acquire of {self.name} lock failed")

        return ret

    def release(self):
        self._log(f"{inspect.stack()[1][3]} releasing {self.name}")
        self.lock.release()

    def __enter__(self):
        self.acquire()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
        return False  # True causes exceptions to be swallowed.  False causes exceptions to be handled.
