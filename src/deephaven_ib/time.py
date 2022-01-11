"""Functionality for working with time in Deephaven and IB."""

import jpy
# noinspection PyPep8Naming
from deephaven import DateTimeUtils as dtu

_SimpleDateFormat = jpy.get_type("java.text.SimpleDateFormat")

_ib_date_time_pattern = "yyyyMMdd HH:mm:ss.S"
_ib_date_time_patterns = [
    "yyyyMMdd HH:mm:ss.S",
    "yyyy-MM-dd HH:mm:ss.S",
    "yyyyMMdd HH:mm:ss",
    "yyyy-MM-dd HH:mm:ss",
]
_ib_date_time_formatter = _SimpleDateFormat(_ib_date_time_pattern)
_ib_date_time_formatters = [_SimpleDateFormat(pattern) for pattern in _ib_date_time_patterns]


def dh_to_ib_datetime(time: dtu.DateTime) -> str:
    """Convert a DH DateTime to an IB timestamp string."""

    if time is None:
        return ""

    return _ib_date_time_formatter.format(time.getDate())


def ib_to_dh_datetime(time: str) -> dtu.DateTime:
    """Convert an IB timestamp to a DH DateTime."""

    if time is None:
        return None

    for formatter in _ib_date_time_formatters:
        try:
            return dtu.DateTime.of(formatter.parse(time).toInstant())
        except:
            pass

    raise Exception(f"Unable to parse time '{time}'")


def unix_sec_to_dh_datetime(time: int) -> dtu.DateTime:
    """Convert Unix seconds since the epoch to a DH DateTime."""

    if time is None:
        return None

    return dtu.DateTime(int(time) * dtu.SECOND)
