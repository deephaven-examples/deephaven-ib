"""Functionality for working with time in Deephaven and IB."""

import jpy
import deephaven.time as dtime
from deephaven.dtypes import DateTime

_SimpleDateFormat = jpy.get_type("java.text.SimpleDateFormat")

_ib_date_time_pattern_sec = "yyyyMMdd HH:mm:ss"
_ib_date_time_pattern_subsec = "yyyyMMdd HH:mm:ss.S"
_ib_date_time_patterns = [
    "yyyyMMdd HH:mm:ss.S",
    "yyyy-MM-dd HH:mm:ss.S",
    "yyyyMMdd HH:mm:ss",
    "yyyy-MM-dd HH:mm:ss",
]
_ib_date_time_formatter_sec = _SimpleDateFormat(_ib_date_time_pattern_sec)
_ib_date_time_formatter_subsec = _SimpleDateFormat(_ib_date_time_pattern_subsec)
_ib_date_time_formatters = [_SimpleDateFormat(pattern) for pattern in _ib_date_time_patterns]


def dh_to_ib_datetime(time: DateTime, sub_sec: bool = True) -> str:
    """Convert a DH DateTime to an IB timestamp string.

    Args:
        time (DateTime): time
        sub_sec (bool): true to return subsecond resolution and false otherwise.
    """

    if time is None:
        return ""

    if sub_sec:
        return _ib_date_time_formatter_subsec.format(time.getDate())
    else:
        return _ib_date_time_formatter_sec.format(time.getDate())


def ib_to_dh_datetime(time: str) -> DateTime:
    """Convert an IB timestamp to a DH DateTime."""

    if time is None:
        return None

    exceptions = []

    for formatter in _ib_date_time_formatters:
        try:
            return DateTime.j_type.of(formatter.parse(time).toInstant())
        except Exception as e:
            exceptions.append(e)
            pass

    raise Exception(f"Unable to parse time '{time}'", exceptions)


def unix_sec_to_dh_datetime(time: int) -> DateTime:
    """Convert Unix seconds since the epoch to a DH DateTime."""

    if time is None:
        return None

    return DateTime(int(time) * dtime.SECOND)
