import logging

from ibapi.wrapper import EWrapper

logging.basicConfig(level=logging.DEBUG)


# TODO: no users need to see this
class _IbListener(EWrapper):
    """Listener for data from IB."""
    pass
