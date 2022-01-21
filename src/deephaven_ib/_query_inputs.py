"""Inputs to queries.

Currently Deephaven has an open ticket for using variables in queries from within python modules.
This module is to house nasty workaround code until the problem has been resolved.

https://github.com/deephaven/deephaven-core/issues/1072
"""

# TODO: When ticket #1072 is resolved, the following code should be replaced with something cleaner
# To work around the problem, variables have to be fed into QueryScope.
# Since python objects can't be inserted into QueryScope, PythonFunctions were created, which are Java objects.
# PythonFunctions only take a single argument, so the python functions had to be changed to take only one arument.

from typing import Union

import jpy
from deephaven import PythonFunction
from deephaven.conversion_utils import NULL_DOUBLE

_QueryScope = jpy.get_type("io.deephaven.engine.table.lang.QueryScope")


def __deephaven_ib_float_value(s: str) -> Union[float, None]:
    if not s:
        return NULL_DOUBLE

    try:
        return float(s)
    except ValueError:
        return NULL_DOUBLE


_QueryScope.addParam("__deephaven_ib_float_value", PythonFunction(__deephaven_ib_float_value, "double"))


# def __deephaven_ib_parse_note(note:str, key:str) -> Union[str,None]:
#     for item in note.split():
#         if item.startswith(f"{key}="):
#             v = item.split("=")[1]
#             v = v[1:-1]
#             if v:
#                 return v
#     return None

def __deephaven_ib_parse_note(inputs) -> Union[str, None]:
    note = inputs[0]
    key = inputs[1]

    for item in note.split():
        if item.startswith(f"{key}="):
            v = item.split("=")[1]
            v = v[1:-1]
            if v:
                return v
    return None


_QueryScope.addParam("__deephaven_ib_parse_note", PythonFunction(__deephaven_ib_parse_note, "java.lang.String"))
