from threading import Thread

from ibapi.client import EClient

from ._listener import _IbListener


class IbClient(EClient):
    """Client for connecting to IB TWS.  Can be used to request data, send orders, etc."""

    def __init__(self, listener: _IbListener):
        EClient.__init__(self, listener)
        self.thread = None

    def connect(self, host: str = "", port: int = 7497, clientId: int = 0) -> None:
        """Connect to an IB TWS session.  Raises an exception if already connected.

        Args:
            host (str): The host name or IP address of the machine where TWS is running. Leave blank to connect to the local host.
            port (int): TWS port, specified in TWS on the Configure>API>Socket Port field.
                By default production trading uses port 7496 and paper trading uses port 7497.
            clientId (int): A number used to identify this client connection.
                All orders placed/modified from this client will be associated with this client identifier.

                Note: Each client MUST connect with a unique clientId.

        Returns:
              None

        Raises:
              Exception
        """

        if self.isConnected():
            raise Exception("IbClient is already connected.")

        EClient.connect(self, host, port, clientId)

        self.thread = Thread(target=self.run)
        self.thread.start()
        setattr(self, "_thread", self.thread)  # TODO: ???

    def disconnect(self) -> None:
        """Disconnect from an IB TWS session.

        Returns:
            None
        """

        EClient.disconnect(self)
        self.thread = None

