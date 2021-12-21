import jpy

ArrayStringSet = jpy.get_type("io.deephaven.stringset.ArrayStringSet")


def map_values(value, map, default=lambda v: f"UNKNOWN(v)"):
    """ Maps one set of values to another.  A default value is used if the value is not in the map. """

    if value is None:
        return None

    try:
        return map[value]
    except KeyError:
        # TODO: log bad mapping
        return default(value)


def to_string_val(value):
    """ Converts a value to a string. """

    if value is None:
        return None

    return str(value)


def to_string_set(value):
    """ Converts an iterable to a string set. """

    if value is None:
        return None

    return ArrayStringSet(",".join([to_string_val(v) for v in value]))
