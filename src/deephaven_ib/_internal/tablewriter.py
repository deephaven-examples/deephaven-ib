"""Functionality for creating Deephaven tables."""

import logging
from typing import List, Any, Sequence, Optional, Set
import collections

from deephaven.time import dh_now
import jpy
from deephaven import DynamicTableWriter
from deephaven.table import Table
from deephaven import dtypes
from deephaven.dtypes import DType
import decimal
from decimal import Decimal

from .trace import trace_str


class TableWriter:
    """A writer for logging data to Deephaven dynamic tables.

    Empty strings are logged as None.
    """

    _dtw: DynamicTableWriter
    _string_indices: List[int]
    _receive_time: bool

    def __init__(self, names: List[str], types: List[DType], receive_time: bool = True):
        TableWriter._check_for_duplicate_names(names)
        self.names = names
        self.types = types
        self._receive_time = receive_time

        if receive_time:
            self.names.insert(0, "ReceiveTime")
            self.types.insert(0, dtypes.Instant)

        col_defs = {name: type for name, type in zip(names, types)}
        self._dtw = DynamicTableWriter(col_defs)
        self._string_indices = [i for (i, t) in enumerate(types) if t == dtypes.string]

    @staticmethod
    def _check_for_duplicate_names(names: List[str]) -> None:
        counts = collections.Counter(names)
        dups = [name for name, count in counts.items() if count > 1]

        if len(dups) > 0:
            raise Exception(f"Duplicate column names: {','.join(dups)}")

    def _check_logged_value_types(self, values: List) -> None:
        for n, t, v in zip(self.names, self.types, values):
            if v is None:
                continue

            if (t is dtypes.string and not isinstance(v, str)) or \
                    (t is dtypes.int64 and not isinstance(v, int)) or \
                    (t is dtypes.float64 and not isinstance(v, float)):
                logging.error(
                    f"TableWriter column type and value type are mismatched: column_name={n} column_type={t} value_type={type(v)} value={v}\n{trace_str()}\n-----")

    def table(self) -> Table:
        """Gets the table data is logged to."""
        return self._dtw.table

    def write_row(self, values: List) -> None:
        """Writes a row of data.  The input values may be modified."""

        if self._receive_time:
            values.insert(0, dh_now())

        for i in range(len(values)):
            if  isinstance(values[i], decimal.Decimal): 
                values[i] = float(values[i])

        self._check_logged_value_types(values)

        for i in self._string_indices:
            if values[i] == "":
                values[i] = None

        try:
            self._dtw.write_row(*values)
        except Exception as e:
            msg = f"Problem logging row:\n"

            for i, v in enumerate(values):
                msg += f"\t{i} {type(v)} {v}\n"

            logging.error(msg)

            raise e


ArrayStringSet = jpy.get_type("io.deephaven.stringset.ArrayStringSet")

_unmapped_values_already_logged:Set[str] = set()

def map_values(value, map, default=lambda v: f"UNKNOWN({v})") -> Any:
    """ Maps one set of values to another.  A default value is used if the value is not in the map. """

    if value is None:
        return None

    try:
        return map[value]
    except KeyError:
        msg = f"Unmapped value.  Please file an issue at https://github.com/deephaven-examples/deephaven-ib/issues: '{value}'\n{trace_str()}\n-----"

        if msg not in _unmapped_values_already_logged:
            _unmapped_values_already_logged.add(msg)
            logging.error(msg)

        return default(value)


def to_string_val(value) -> Optional[str]:
    """ Converts a value to a string. """

    if value is None:
        return None

    return str(value)


def to_string_set(value: Sequence) -> Optional[ArrayStringSet]:
    """ Converts an iterable to a string set. """

    if value is None:
        return None

    return ArrayStringSet(list({to_string_val(v) for v in value}))
