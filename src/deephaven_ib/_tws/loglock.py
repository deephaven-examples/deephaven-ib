import inspect
import logging
import threading


class LogLock(object):
    """Wrap a lock and log the locking and unlocking."""

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
        return False  # Do not swallow exceptions
