from typing import List, Any

import deephaven.Types as dht
from deephaven import DynamicTableWriter as DTW


class DynamicTableWriter:
    """A writer for logging data to dynamic tables.

    Empty strings are logged as None.
    """

    # TODO improve types type annotation once deephaven v2 is available
    def __init__(self, names: List[str], types: List[Any]):
        self._dtw = DTW(names, types)
        self._string_indices = [i for (i, t) in enumerate(types) if t == dht.string]

    # TODO improve types type annotation once deephaven v2 is available
    def table(self) -> Any:
        """Gets the table data is logged to."""
        return self._dtw.getTable()

    def write_row(self, values: List) -> None:
        """Writes a row of data."""

        for i in self._string_indices:
            if values[i] == "":
                values[i] = None

        self._dtw.logRow(values)
