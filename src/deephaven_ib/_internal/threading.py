import inspect
import logging
import threading


class LoggingLock(object):
    """A threading lock that logs lock acquisition and release."""

    def __init__(self, name, lock=threading.Lock(), log=logging):
        self.name = str(name)
        self.log = log
        self.lock = lock
        self.log.debug(f"{inspect.stack()[1][3]} created {self.name}")

    def acquire(self, blocking=True):
        self.log.debug(f"{inspect.stack()[1][3]} trying to acquire {self.name}")
        ret = self.lock.acquire(blocking)

        if ret:
            self.log.debug(f"{inspect.stack()[1][3]} acquired {self.name}")
        else:
            self.log.debug(f"{inspect.stack()[1][3]} non-blocking acquire of {self.name} lock failed")

        return ret

    def release(self):
        self.log.debug(f"{inspect.stack()[1][3]} releasing {self.name}")
        self.lock.release()

    def __enter__(self):
        self.acquire()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
        return False  # True causes exceptions to be swallowed.  False causes exceptions to be handled.
