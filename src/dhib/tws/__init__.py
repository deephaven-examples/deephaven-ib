from ._client import _IbClient
from ._listener import _IbListener

__all__ = ["IbSessionTws"]


class IbSessionTws:
    """ IB TWS session."""

    def __init__(self):
        self._listener = _IbListener()
        self._client = _IbClient(self._listener)

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

        self._client.connect(host, port, clientId)
        self._listener.connect(self._client)

    def disconnect(self) -> None:
        """Disconnect from an IB TWS session.

        Returns:
            None
        """

        self._client.disconnect()
        self._listener.disconnect()

    def is_connected(self):
        """Is there a connection with TWS?"""

        return self._client.isConnected()

    # #TODO: move this to the listener
    # def _subscribe(self):
    #
    #     self._client.reqAllOpenOrders()
    #     self._client.reqContractDetails()
    #     self._client.reqHistoricalData()
    #     self._client.reqHistoricalNews()
    #     self._client.reqHistoricalTicks()
    #     self._client.reqIds()
    #     self._client.reqMarketDataType()
    #     self._client.reqMarketRule()
    #     self._client.reqMatchingSymbols()
    #     self._client.reqNewsArticle()
    #     self._client.reqNewsBulletins()
    #     self._client.reqNewsProviders()
    #     self._client.reqFundamentalData()
    #     self._client.reqOpenOrders()
    #     self._client.reqAutoOpenOrders()
    #     self._client.reqCompletedOrders()
    #     self._client.reqExecutions()
    #     self._client.reqFamilyCodes()
    #     self._client.reqGlobalCancel()
    #     self._client.reqMktData()
    #     self._client.reqContractDetails()
    #     self._client.reqPnL()
    #     self._client.reqPositions()
    #     self._client.reqPositionsMulti()
    #     self._client.reqRealTimeBars()
    #     self._client.reqTickByTickData()
