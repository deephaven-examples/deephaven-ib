"""Functionality for working with stack traces."""

import traceback


def trace_str() -> str:
    """Gets a string of the current stacktrace."""
    return "".join(traceback.format_stack())
