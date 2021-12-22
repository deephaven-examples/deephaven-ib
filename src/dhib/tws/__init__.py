from enum import Enum
from typing import Dict, Any

from deephaven import DateTimeUtils as dtu
from ibapi.contract import Contract

from ._twsclient import IbTwsClient as _IbTwsClient
from ..utils import next_unique_id, dh_to_ib_datetime

__all__ = ["MarketDataType", "TickDataType", "BarDataType", "BarSize", "Duration", "IbSessionTws"]


# TODO: make a request ID type?

class MarketDataType(Enum):
    """Type of market data to use."""

    REAL_TIME = 1
    """Real-time market data."""
    FROZEN = 2
    """Real-time market data during regular trading hours, and frozen prices after the close."""


class TickDataType(Enum):
    """Tick data type."""

    LAST = "Last"
    "Most recent trade."
    BID_ASK = "BidAsk"
    "Most recent bid and ask."
    MIDPOINT = "MidPoint"
    "Most recent midpoint."


class BarDataType(Enum):
    """Bar data type."""

    TRADES = 1
    MIDPOINT = 2
    BID = 3
    ASK = 4
    BID_ASK = 5
    HISTORICAL_VOLATILITY = 6
    OPTION_IMPLIED_VOLATILITY = 7
    FEE_RATE = 8
    REBATE_RATE = 9

class BarSize(Enum):
    """Bar data sizes."""

    SEC_1 = "1 sec"
    SEC_5 = "5 secs"
    SEC_15 = "15 secs"
    SEC_30 = "30 secs"
    MIN_1 = "1 min"
    MIN_2 = "2 mins"
    MIN_3 = "3 mins"
    MIN_5 = "5 mins"
    MIN_15 = "15 mins"
    MIN_30 = "30 mins"
    HOUR_1 = "1 hour"
    DAY_1 = "1 day"


class Duration:
    """Time period to request data for."""

    def __init__(self, value):
        self.value = value

    @staticmethod
    def seconds(value: int):
        return Duration(f"{value} S")

    @staticmethod
    def days(value: int):
        return Duration(f"{value} D")

    @staticmethod
    def weeks(value: int):
        return Duration(f"{value} W")

    @staticmethod
    def months(value: int):
        return Duration(f"{value} M")

    @staticmethod
    def years(value: int):
        return Duration(f"{value} Y")


class IbSessionTws:
    """ IB TWS session.
    
    Tables:
        ####
        # General
        ####
        errors: an error log

        ####
        # Contracts
        ####
        contract_details: details describing contracts of interest.  Automatically populated.
        contracts_matching: contracts matching query strings provided to `request_contracts_matching`.
        market_rules: market rules indicating the price increment a contract can trade in.  Automatically populated.


        ####
        # Accounts
        ####
        accounts_managed: accounts managed by the TWS session login.  Automatically populated.
        accounts_family_codes: account family.  Automatically populated.
        accounts_value: account values.  Automatically populated.
        accounts_portfolio: account holdings.  Automatically populated.
        accounts_summary: account summary.  Automatically populated.
        accounts_positions: account positions.  Automatically populated.
        accounts_pnl: account PNL requested via 'request_pnl'.

        ####
        # News
        ####

        news_providers: currently subscribed news sources.  Automatically populated.
        news_bulletins: news bulletins.  Automatically populated.
        news_articles: the content of news articles requested via 'request_news_article'
        news_historical: historical news headlines requested via 'request_news_historical'

        ####
        # Market Data
        ####

        ticks_price: real-time tick market data of price values requested via 'request_market_data'.
        ticks_size: real-time tick market data of size values requested via 'request_market_data'.
        ticks_string: real-time tick market data of string values requested via 'request_market_data'.
        ticks_efp: real-time tick market data of exchange for physical (EFP) values requested via 'request_market_data'.
        ticks_generic: real-time tick market data of generic values requested via 'request_market_data'.
        ticks_option_computation: real-time tick market data of option computations requested via 'request_market_data'.
        ticks_trade: real-time tick market data of trade prices requested via 'request_tick_data_historical' or 'request_tick_data_realtime'.
        ticks_bid_ask: real-time tick market data of bid and ask prices requested via 'request_tick_data_historical' or 'request_tick_data_realtime'.
        ticks_mid_point: real-time tick market data of mid-point prices requested via 'request_tick_data_historical' or 'request_tick_data_realtime'.
        bars_historical: historical price bars requested via 'request_bars_historical'
        bars_realtime: real-time price bars requested via 'request_bars_realtime'

        ####
        # Order Management System (OMS)
        ####

        orders_open: open orders.  Automatically populated.
        orders_status: order statuses.  Automatically populated.
        orders_completed: completed orders.  Automatically populated.
        orders_exec_details: order execution details.  Automatically populated.
        orders_exec_commission_report: order execution commission report.  Automatically populated.
    """

    def __init__(self):
        self._client = _IbTwsClient()

    ####################################################################################################################
    ####################################################################################################################
    ## Connect / Disconnect / Subscribe
    ####################################################################################################################
    ####################################################################################################################

    def connect(self, host: str = "", port: int = 7497, client_id: int = 0) -> None:
        """Connect to an IB TWS session.  Raises an exception if already connected.

        Args:
            host (str): The host name or IP address of the machine where TWS is running. Leave blank to connect to the local host.
            port (int): TWS port, specified in TWS on the Configure>API>Socket Port field.
                By default production trading uses port 7496 and paper trading uses port 7497.
            client_id (int): A number used to identify this client connection.
                All orders placed/modified from this client will be associated with this client identifier.

                Note: Each client MUST connect with a unique clientId.

        Returns:
              None

        Raises:
              Exception
        """

        self._client.connect(host, port, client_id)

    def disconnect(self) -> None:
        """Disconnect from an IB TWS session.

        Returns:
            None
        """

        self._client.disconnect()

    def is_connected(self) -> bool:
        """Is there a connection with TWS?"""

        return self._client.isConnected()

    ####################################################################################################################
    ####################################################################################################################
    ## General
    ####################################################################################################################
    ####################################################################################################################

    @property
    def tables(self) -> Dict[str, Any]:
        """Gets a dictionary of all data tables."""
        return self._client.tables

    ####################################################################################################################
    ####################################################################################################################
    ## Contracts
    ####################################################################################################################
    ####################################################################################################################

    def request_contracts_matching(self, pattern: str) -> int:
        """Request contracts matching a pattern.  Results are returned in the `contracts_matching` table.

        Args:
            pattern (str): pattern to search for.  Can include part of a ticker or part of the company name.

        Returns:
            Request ID

        Raises:
              Exception
        """

        if not self.is_connected():
            raise Exception("IbSessionTws is not connected.")

        req_id = next_unique_id()
        self._client.reqMatchingSymbols(reqId=req_id, pattern=pattern)
        return req_id

    ####################################################################################################################
    ####################################################################################################################
    ## Accounts
    ####################################################################################################################
    ####################################################################################################################

    ####################################################################################################################
    ####################################################################################################################
    ## News
    ####################################################################################################################
    ####################################################################################################################

    # TODO: how to handle conId?
    def request_news_historical(self, conId: int, provider_codes: str, start: dtu.DateTime, end: dtu.DateTime,
                                total_results: int = 100) -> int:
        """ Request historical news for a contract.  Results are returned in the `news_historical` table.

        Args:
            conId (int): contract id of ticker
            provider_codes (str): a '+'-separated list of provider codes
            start (DateTime): marks the (exclusive) start of the date range.
            end (DateTime): marks the (inclusive) end of the date range.
            total_results (int): the maximum number of headlines to fetch (1 - 300)

        Returns:
            Request ID

        Raises:
              Exception
        """

        if not self.is_connected():
            raise Exception("IbSessionTws is not connected.")

        req_id = next_unique_id()
        self._client.reqHistoricalNews(reqId=req_id, conId=conId, providerCodes=provider_codes,
                                       startDateTime=dh_to_ib_datetime(start), endDateTime=dh_to_ib_datetime(end),
                                       totalResults=total_results, historicalNewsOptions=[])
        return req_id

    def request_news_article(self, provider_code: str, article_id: str) -> int:
        """ Request the text of a news article.  Results are returned in the `news_articles` table.

        Args:
            provider_code (str): short code indicating news provider, e.g. FLY
            article_id (str): id of the specific article

        Returns:
            Request ID

        Raises:
              Exception
        """

        if not self.is_connected():
            raise Exception("IbSessionTws is not connected.")

        req_id = next_unique_id()
        self._client.reqNewsArticle(reqId=req_id, providerCode=provider_code, articleId=article_id,
                                    newsArticleOptions=[])
        return req_id

    ####################################################################################################################
    ####################################################################################################################
    ## Market Data
    ####################################################################################################################
    ####################################################################################################################

    def set_market_data_type(self, type: MarketDataType) -> None:
        """Sets the default type of market data.

        Args:
            type (MarketDataType): market data type

        Raises:
              Exception
        """

        if not self.is_connected():
            raise Exception("IbSessionTws is not connected.")

        self._client.reqMarketDataType(marketDataType=type.value)

    # TODO: how to handle contract?
    # TODO: fill in generic_tick_list with ContractSamples?
    def request_market_data(self, contract: Contract, generic_tick_list: str, snapshot: bool = False,
                            regulatory_snapshot: bool = False) -> int:
        """ Request market data for a contract.  Results are returned in the `ticks_price`, `ticks_size`,
        `ticks_string`, `ticks_efp`, `ticks_generic`, and `ticks_option_computation` tables.


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

        Raises:
              Exception
        """

        if not self.is_connected():
            raise Exception("IbSessionTws is not connected.")

        req_id = next_unique_id()
        self._client.reqMktData(reqId=req_id, contract=contract, genericTickList=generic_tick_list, snapshot=snapshot,
                                regulatorySnapshot=regulatory_snapshot, mktDataOptions=[])
        return req_id

    def cancel_market_data(self, reqId: int):
        """Cancel a market data request.

        Args:
            req_id (int): request id

        Raises:
              Exception
        """
        self._client.cancelMktData(reqId=reqId)

    # TODO: how to handle contract?
    def request_bars_historical(self, contract: Contract, end: dtu.DateTime,
                                duration: Duration, barSize: BarSize, barType: BarDataType,
                                type: MarketDataType = MarketDataType.FROZEN, keepUpToDate: bool = True) -> int:
        """Requests historical bars for a contract.  Results are returned in the `bars_historical` table.

        Args:
            contract (Contract): contract data is requested for
            end (DateTime): Ending timestamp of the requested data.
            duration (Duration): Duration of data being requested by the query.
            barSize (BarSize): Size of the bars that will be returned.
            barType (BarDataType): Type of bars that will be returned.
            type (MarketDataType): Type of market data to return after the close.
            keepUpToDate (bool): True to continuously update bars

        Returns:
            Request ID

        Raises:
              Exception
        """

        if not self.is_connected():
            raise Exception("IbSessionTws is not connected.")

        req_id = next_unique_id()
        self._client.reqHistoricalData(reqId=req_id, contract=contract, endDateTime=dh_to_ib_datetime(end),
                                       durationStr=duration.value, barSizeSetting=barSize.value,
                                       whatToShow=barType.name, useRTH=(type == MarketDataType.FROZEN), formatDate=2,
                                       keepUpToDate=keepUpToDate, chartOptions=[])
        return req_id

    # TODO: how to handle contract?
    def request_bars_realtime(self, contract: Contract, barType: BarDataType, barSize: int = 5,
                              type: MarketDataType = MarketDataType.FROZEN) -> int:
        """Requests real time bars for a contract.  Results are returned in the `bars_realtime` table.

        Args:
            contract (Contract): contract data is requested for
            barType (BarDataType): Type of bars that will be returned.
            barSize (int): Bar size in seconds.
            type (MarketDataType): Type of market data to return after the close.


        Returns:
            Request ID

        Raises:
              Exception
        """

        if not self.is_connected():
            raise Exception("IbSessionTws is not connected.")

        req_id = next_unique_id()
        self._client.reqRealTimeBars(reqId=req_id, contract=contract, barSize=barSize,
                                     whatToShow=barType.name, useRTH=(type == MarketDataType.FROZEN),
                                     realTimeBarsOptions=[])
        return req_id

    def cancel_bars_realtime(self, req_id: int):
        """Cancel a real-time bar request.

        Args:
            req_id (int): request id


        Raises:
              Exception
        """

        if not self.is_connected():
            raise Exception("IbSessionTws is not connected.")

        self._client.cancelRealTimeBars(reqId=req_id)

    # TODO: how to handle contract?
    def request_tick_data_realtime(self, contract: Contract, tickType: TickDataType,
                                   numberOfTicks: int = 0, ignoreSize: bool = False) -> int:
        """Requests real-time tick-by-tick data.  Results are returned in the ticks_trade`, `ticks_bid_ask`,
        and `ticks_mid_point` tables.

        Args:
            contract (Contract): Contract data is requested for
            tickType (TickDataType): Type of market data to return.
            numberOfTicks (int): Number of historical ticks to request.
            ignoreSize (bool): should size values be ignored.

        Returns:
            Request ID

        Raises:
              Exception
        """

        if not self.is_connected():
            raise Exception("IbSessionTws is not connected.")

        req_id = next_unique_id()
        self._client.reqTickByTickData(reqId=req_id, contract=contract, tickType=tickType.value,
                                       numberOfTicks=numberOfTicks, ignoreSize=ignoreSize)
        return req_id

    def cancel_tick_data_realtime(self, req_id: int):
        """Cancel a real-time tick-by-tick data request.

        Args:
            req_id (int): request id


        Raises:
              Exception
        """

        if not self.is_connected():
            raise Exception("IbSessionTws is not connected.")

        self._client.cancelTickByTickData(reqId=req_id)

    # TODO: how to handle contract?
    def request_tick_data_historical(self, contract: Contract, start: dtu.DateTime, end: dtu.DateTime,
                                     tickType: TickDataType, numberOfTicks: int,
                                     type: MarketDataType = MarketDataType.FROZEN,
                                     ignoreSize: bool = False) -> int:
        """Requests historical tick-by-tick data. Results are returned in the ticks_trade`, `ticks_bid_ask`,
        and `ticks_mid_point` tables.


        Args:
            contract (Contract): Contract data is requested for
            start (DateTime): marks the (exclusive) start of the date range.
            end (DateTime): marks the (inclusive) end of the date range.
            tickType (TickDataType): Type of market data to return.
            numberOfTicks (int): Number of historical ticks to request.
            type (MarketDataType): Type of market data to return after the close.
            ignoreSize (bool): should size values be ignored.

        Returns:
            Request ID

        Raises:
              Exception
        """

        if not self.is_connected():
            raise Exception("IbSessionTws is not connected.")

        req_id = next_unique_id()
        whatToShow = tickType.value

        if whatToShow == "Last":
            whatToShow = "Trades"

        self._client.reqHistoricalTicks(reqId=req_id, contract=contract, startDateTime=dh_to_ib_datetime(start),
                                        endDateTime=dh_to_ib_datetime(end),
                                        numberOfTicks=numberOfTicks, whatToShow=whatToShow, useRth=type.value,
                                        ignoreSize=ignoreSize, miscOptions=[])
        return req_id

    ####################################################################################################################
    ####################################################################################################################
    ## Order Management System (OMS)
    ####################################################################################################################
    ####################################################################################################################

    # TODO: rename?
    def cancel_all_orders(self) -> None:
        """Cancel all open orders.

        Raises:
              Exception
        """

        if not self.is_connected():
            raise Exception("IbSessionTws is not connected.")

        self._client.reqGlobalCancel()

    ## ???????

    # TODO: rename
    # TODO request by default when pull accounts?
    def request_pnl(self, account: str = "All", model_code: str = "") -> int:
        """Request PNL updates.  Results are returned in the `accounts_pnl` table.

        Args:
            account (str): Account to request PNL for.  "All" requests PNL for all accounts.
            model_code (str): Model used to evaluate PNL.

        Raises:
              Exception
        """

        if not self.is_connected():
            raise Exception("IbSessionTws is not connected.")

        req_id = next_unique_id()
        self._client.reqPnL(reqId=req_id, account=account, modelCode=model_code)
        return req_id

    # TODO: *** add contract details requests in this file ***

    #TODO: placeOrder, cancelOrder, reqGlobalCancel

    #### To do ######

    #     self._client.reqIds() --> get next valid id for placing orders

    ### Don't Do vvvvvvv

    #     self._client.reqPositionsMulti() --> req positions by account and model (needed only if >50 sub accounts because reqPositions will not work)


    #     self._client.reqOpenOrders() --> reqAllOpenOrders gets orders that were not submitted by this session (needed?)
