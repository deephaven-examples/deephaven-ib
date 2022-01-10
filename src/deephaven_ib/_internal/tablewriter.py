"""Functionality for creating Deephaven tables."""

import logging
import traceback
from typing import List, Any, Sequence, Union

# noinspection PyPep8Naming
import deephaven.Types as dht
import jpy
from deephaven import DynamicTableWriter


class TableWriter:
    """A writer for logging data to Deephaven dynamic tables.

    Empty strings are logged as None.
    """

    _dtw: DynamicTableWriter
    _string_indices: List[int]

    # TODO improve types type annotation once deephaven v2 is available
    def __init__(self, names: List[str], types: List[Any]):
        self._dtw = DynamicTableWriter(names, types)
        self._string_indices = [i for (i, t) in enumerate(types) if t == dht.string]

    # TODO improve types type annotation once deephaven v2 is available
    def table(self) -> Any:
        """Gets the table data is logged to."""
        return self._dtw.getTable()

    def write_row(self, values: List) -> None:
        """Writes a row of data.  The input values may be modified."""

        for i in self._string_indices:
            if values[i] == "":
                values[i] = None

        self._dtw.logRow(values)


ArrayStringSet = jpy.get_type("io.deephaven.stringset.ArrayStringSet")


def map_values(value, map, default=lambda v: f"UNKNOWN({v})") -> Any:
    """ Maps one set of values to another.  A default value is used if the value is not in the map. """

    if value is None:
        return None

    try:
        return map[value]
    except KeyError:
        # TODO: what logging level?
        logging.debug(f"Unmapped value: {value}\n{traceback.format_exc()}\n-----")
        return default(value)


def to_string_val(value) -> Union[str, None]:
    """ Converts a value to a string. """

    if value is None:
        return None

    return str(value)


def to_string_set(value: Sequence) -> Union[ArrayStringSet, None]:
    """ Converts an iterable to a string set. """

    if value is None:
        return None

    return ArrayStringSet([to_string_val(v) for v in value])
