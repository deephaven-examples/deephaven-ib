import logging
import traceback
from typing import Sequence

import jpy

ArrayStringSet = jpy.get_type("io.deephaven.stringset.ArrayStringSet")


def map_values(value, map, default=lambda v: f"UNKNOWN({v})"):
    """ Maps one set of values to another.  A default value is used if the value is not in the map. """

    if value is None:
        return None

    try:
        return map[value]
    except KeyError:
        logging.debug(f"Unmapped value: {value}\n{traceback.format_exc()}\n-----")
        return default(value)


def to_string_val(value) -> str:
    """ Converts a value to a string. """

    if value is None:
        return None

    return str(value)


def to_string_set(value: Sequence) -> ArrayStringSet:
    """ Converts an iterable to a string set. """

    if value is None:
        return None

    return ArrayStringSet([to_string_val(v) for v in value])
