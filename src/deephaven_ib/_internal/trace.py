"""Functionality for working with stack traces."""

import traceback
import threading
import sys

def trace_str() -> str:
    """Gets a string of the current stacktrace."""
    return "".join(traceback.format_stack())


def trace_thread_str(thread:threading.Thread) -> str:
    """Gets a string of the stacktrace of a thread."""
    try:
        return "".join(traceback.format_stack(sys._current_frames()[thread.ident]))
    except KeyError:
        return f"Thread stack not found: thread={thread.ident}"


def trace_all_threads_str() -> str:
    """Get the stacktraces for all threads as a string."""

    rst = "Stack Traces:\n"

    for th in threading.enumerate():
        rst += str(th)
        rst += trace_thread_str(th)
        rst += "\n"

    return rst