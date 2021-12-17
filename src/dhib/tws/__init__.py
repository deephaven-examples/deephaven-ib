from enum import Enum

from deephaven import DateTimeUtils as dtu
from ibapi.contract import Contract

from ._client import _IbClient
from ._listener import _IbListener
from ..utils import next_unique_id, dh_to_ib_datetime

__all__ = ["MarketDataType", "IbSessionTws"]


# TODO: automatically set request ids
# TODO: raise exception if no connection and certain methods are called

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

    def request_news_article(self, provider_code: str, article_id: str) -> int:
        """ Request the text of a news article.

        Args:
            provider_code (str): short code indicating news provider, e.g. FLY
            article_id (str): id of the specific article

        Returns:
            Request ID
        """
        req_id = next_unique_id()
        self._client.reqNewsArticle(reqId=req_id, providerCode=provider_code, articleId=article_id,
                                    newsArticleOptions=[])
        return req_id

    # TODO: how to handle contract?
    # TODO: fill in generic_tick_list with ContractSamples?
    def request_market_data(self, contract: Contract, generic_tick_list: str, snapshot: bool = False,
                            regulatory_snapshot: bool = False) -> int:
        """ Request market data for a contract.

        Args:
            contract (Contract): contract data is requested for
            generic_tick_list (str): A commma delimited list of generic tick types.
                Tick types can be found in the Generic Tick Types page.
                Prefixing w/ 'mdoff' indicates that top mkt data shouldn't tick.
                You can specify the news source by postfixing w/ ':<source>.
                Example: "mdoff,292:FLY+BRF"
                See: https://interactivebrokers.github.io/tws-api/tick_types.html
            snapshot (bool): True to return a single snapshot of Market data and have the market data subscription cancel.
                Do not enter any genericTicklist values if you use snapshots.
            regulatory_snapshot (bool): True to get a regulatory snapshot.  Requires the US Value Snapshot Bundle for stocks.
        """

        req_id = next_unique_id()
        self._client.reqMktData(reqId=req_id, contract=contract, genericTickList=generic_tick_list, snapshot=snapshot,
                                regulatorySnapshot=regulatory_snapshot, mktDataOptions=[])
        return req_id

    def cancelMktData(self, reqId: int):
        """Cancel a market data request.

        Args:
            req_id (int): request id
        """
        self._client.cancelMktData(reqId=reqId)


    #     self._client.reqContractDetails() -> for a particular contract

    #     self._client.reqTickByTickData() -> get tick data.  Limits on subscriptions so need to remove
    #     self._client.reqHistoricalTicks()
    #     self._client.reqHistoricalData()
    #     self._client.reqRealTimeBars()

    #     self._client.reqIds() --> get next valid id for placing orders

    ### Don't Do vvvvvvv

    #     self._client.reqMatchingSymbols() -> search for partial matches for tickers (?)
    #     self._client.reqFamilyCodes() --> doesn't look important
    #     self._client.reqMarketRule() --> request min ticks (needed?)
    #     self._client.reqOpenOrders() --> reqAllOpenOrders gets orders that were not submitted by this session (needed?)
    #     self._client.reqPnL() --> daily pnl by account and model code (needed?)
    #     self._client.reqPositionsMulti() --> req positions by account and model (needed?)
    #     self._client.reqFundamentalData() (deprecated)
