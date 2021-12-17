from enum import Enum

from deephaven import DateTimeUtils as dtu

from ._client import _IbClient
from ._listener import _IbListener
from ..utils import next_unique_id, dh_to_ib_datetime

__all__ = ["MarketDataType", "IbSessionTws"]


# TODO: automatically set request ids

class MarketDataType(Enum):
    """Type of market data to use after the close."""

    REAL_TIME = 1
    """Real time market data."""
    FROZEN = 2
    """Market data frozen at the close."""


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

    def is_connected(self) -> bool:
        """Is there a connection with TWS?"""

        return self._client.isConnected()

    def cancel_all_orders(self) -> None:
        """Cancel all open orders."""
        self._client.reqGlobalCancel()

    def market_data_type(self, type: MarketDataType) -> None:
        """Sets the type of market data to use after the close."""
        self._client.reqMarketDataType(marketDataType=type.value)

    # TODO: how to handle conId?
    def request_historical_news(self, conId: int, provider_codes: str, start: dtu.DateTime, end: dtu.DateTime,
                                total_results: int = 100) -> int:
        """ Request historical news for a contract.

        Args:
            conId (int): contract id of ticker
            provider_codes (str): a '+'-separated list of provider codes
            start (DateTime): marks the (exclusive) start of the date range.
            end (DateTime): marks the (inclusive) end of the date range.
            total_results (int): the maximum number of headlines to fetch (1 - 300)

        Returns:
            Request ID
        """
        req_id = next_unique_id()
        self._client.reqHistoricalNews(reqId=req_id, conId=conId, providerCodes=provider_codes,
                                       startDateTime=dh_to_ib_datetime(start), endDateTime=dh_to_ib_datetime(end),
                                       totalResults=total_results, historicalNewsOptions=[])
        return req_id

    def request_news_article(self, providerCode: str, article_id: str) -> int:
        """ Request the text of a news article.

        Args:
            provider_code (str): short code indicating news provider, e.g. FLY
            article_id (str): id of the specific article

        Returns:
            Request ID
        """
        req_id = next_unique_id()
        self._client.reqNewsArticle(reqId=req_id, providerCode=providerCode, articleId=article_id,
                                    newsArticleOptions=[])
        return req_id


    #     self._client.reqContractDetails() -> for a particular contract

    #     self._client.reqTickByTickData() -> get tick data.  Limits on subscriptions so need to remove
    #     self._client.reqHistoricalData()
    #     self._client.reqMktData()
    #     self._client.reqRealTimeBars()
    #     self._client.reqHistoricalTicks()

    #     self._client.reqIds() --> get next valid id for placing orders

    ### Don't Do vvvvvvv

    #     self._client.reqMatchingSymbols() -> search for partial matches for tickers (?)
    #     self._client.reqFamilyCodes() --> doesn't look important
    #     self._client.reqMarketRule() --> request min ticks (needed?)
    #     self._client.reqOpenOrders() --> reqAllOpenOrders gets orders that were not submitted by this session (needed?)
    #     self._client.reqPnL() --> daily pnl by account and model code (needed?)
    #     self._client.reqPositionsMulti() --> req positions by account and model (needed?)
    #     self._client.reqFundamentalData() (deprecated)
