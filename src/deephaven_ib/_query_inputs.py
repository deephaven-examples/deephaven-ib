"""Inputs to queries.

Currently Deephaven has an open ticket for using variables in queries from within python modules.
This module is to house nasty workaround code until the problem has been resolved.

https://github.com/deephaven/deephaven-core/issues/1072
"""

# TODO: When ticket #1072 is resolved, the following code should be replaced with something cleaner (https://github.com/deephaven-examples/deephaven-ib/issues/11)
# To work around the problem, variables have to be fed into QueryScope.
# Since python objects can't be inserted into QueryScope, PythonFunctions were created, which are Java objects.
# PythonFunctions only take a single argument, so the python functions had to be changed to take only one arument.

import json
from typing import Union

import jpy
from deephaven.jcompat import j_function
from deephaven.constants import NULL_DOUBLE
import deephaven.dtypes

_QueryScope = jpy.get_type("io.deephaven.engine.table.lang.QueryScope")


def __deephaven_ib_float_value(s: str) -> Union[float, None]:
    if not s:
        return NULL_DOUBLE

    try:
        return float(s)
    except ValueError:
        return NULL_DOUBLE


_QueryScope.addParam("__deephaven_ib_float_value", j_function(__deephaven_ib_float_value, deephaven.dtypes.double))


# def __deephaven_ib_parse_note(note:str, key:str) -> Union[str,None]:
#     dict = json.loads(note)
#
#     if key in dict:
#         return dict[key]
#
#     return None

def __deephaven_ib_parse_note(inputs) -> Union[str, None]:
    note = inputs[0]
    key = inputs[1]

    json_dict = json.loads(note)

    if key in json_dict:
        return json_dict[key]

    return None


_QueryScope.addParam("__deephaven_ib_parse_note", j_function(__deephaven_ib_parse_note, deephaven.dtypes.string))
