import jpy
from deephaven import DateTimeUtils as dtu

_DateTimeFormatter = jpy.get_type("java.time.format.DateTimeFormatter")
_ZoneId = jpy.get_type("java.time.ZoneId")

_ib_date_time_pattern = "yyyy-MM-dd HH:mm:ss.S"
_SimpleDateFormat = jpy.get_type("java.text.SimpleDateFormat")
_ib_date_time_formatter = _SimpleDateFormat(_ib_date_time_pattern)

_last_unique_id = 1


# TODO: needs to be thread safe
# TODO: move to private location
def next_unique_id():
    """Gets the next sequential ID."""
    global _last_unique_id
    _last_unique_id += 1
    return _last_unique_id


def dh_to_ib_datetime(time: dtu.DateTime) -> str:
    """Convert a DH DateTime to an IB timestamp.

    The IB format is yyyy-MM-dd HH:mm:ss.0"""

    if time is None:
        return ""

    return _ib_date_time_formatter.format(time.getDate())


def ib_to_dh_datetime(time: str) -> dtu.DateTime:
    """Convert an IB timestamp to a DH DateTime."""

    if time is None:
        return None

    return dtu.DateTime.of(_ib_date_time_formatter.parse(time).toInstant())


def unix_sec_to_dh_datetime(time: int) -> dtu.DateTime:
    """Convert Unix seconds since the epoch to a DH DateTime."""

    if time is None:
        return None

    return dtu.DateTime(int(time) * dtu.SECOND)
