"""Functionality for working with time in Deephaven and IB."""

from typing import Union

import jpy
import datetime
import numpy
import pandas

import deephaven.time as dtime
from deephaven.dtypes import Instant

_SimpleDateFormat = jpy.get_type("java.text.SimpleDateFormat")
_TimeZone = jpy.get_type("java.util.TimeZone")
_DateTimeUtils = jpy.get_type("io.deephaven.time.DateTimeUtils")

_ib_date_time_pattern_sec = "yyyyMMdd HH:mm:ss"
_ib_date_time_pattern_subsec = "yyyyMMdd HH:mm:ss.S"
_ib_date_time_patterns = [
    "yyyyMMdd HH:mm:ss.S",
    "yyyy-MM-dd HH:mm:ss.S",
    "yyyyMMdd HH:mm:ss",
    "yyyy-MM-dd HH:mm:ss",
]
_ib_date_time_formatter_sec = _SimpleDateFormat(_ib_date_time_pattern_sec)
_ib_date_time_formatter_sec.setTimeZone(_TimeZone.getTimeZone("US/Eastern"))
_ib_date_time_formatter_subsec = _SimpleDateFormat(_ib_date_time_pattern_subsec)
_ib_date_time_formatter_subsec.setTimeZone(_TimeZone.getTimeZone("US/Eastern"))
_ib_date_time_formatters = [_SimpleDateFormat(pattern) for pattern in _ib_date_time_patterns]

for _f in _ib_date_time_formatters:
    _f.setTimeZone(_TimeZone.getTimeZone("US/Eastern"))


def to_ib_datetime(time: Union[None, Instant, int, str, datetime.datetime, numpy.datetime64, pandas.Timestamp],
                   sub_sec: bool = True) -> str:
    """Convert a time to an IB timestamp string.

    Args:
        time (Union[None, Instant, int, str, datetime.datetime, numpy.datetime64, pandas.Timestamp]): time.  See https://deephaven.io/core/pydoc/code/deephaven.time.html#deephaven.time.to_j_instant for supported inputs.
        sub_sec (bool): true to return subsecond resolution and false otherwise.
    """

    time = dtime.to_j_instant(time)

    if time is None:
        return ""

    date = _DateTimeUtils.toDate(time)

    if sub_sec:
        return _ib_date_time_formatter_subsec.format(date) + " US/Eastern"
    else:
        return _ib_date_time_formatter_sec.format(date) + " US/Eastern"


def ib_to_j_instant(time: str) -> Instant:
    """Convert an IB timestamp to a Java Instant."""

    if time is None:
        return None

    exceptions = []

    for formatter in _ib_date_time_formatters:
        try:
            return formatter.parse(time).toInstant()
        except Exception as e:
            exceptions.append(e)
            pass

    raise Exception(f"Unable to parse time '{time}'", exceptions)


def unix_sec_to_j_instant(time: int) -> Instant:
    """Convert Unix seconds since the epoch to a Java Instant."""

    if time is None:
        return None

    return dtime.to_j_instant(int(time) * 1000000000)
