from enum import Enum
from typing import Dict, List, Any, Callable

# noinspection PyPep8Naming
from deephaven import DateTimeUtils as dtu
from ibapi.contract import Contract, ContractDetails
from ibapi.order import Order

from ._tws import IbTwsClient as IbTwsClient
from ._utils import next_unique_id
from .utils import dh_to_ib_datetime

__all__ = ["MarketDataType", "TickDataType", "BarDataType", "BarSize", "Duration", "Request", "RegisteredContract",
           "IbSessionTws"]


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

    def _historical_value(self) -> str:
        if self.value == "Last":
            return "Trades"
        else:
            return self.value


class GenericTickType(Enum):
    """Tick data types for 'Generic" data.

    See: https://interactivebrokers.github.io/tws-api/tick_types.html
    """

    NEWS = 292
    """News."""

    DIVIDENDS = 456
    """Dividends."""

    AUCTION = 225
    """Auction details."""

    MARK_PRICE = 232
    """Mark price is the current theoretical calculated value of an instrument. Since it is a calculated value, it will typically have many digits of precision."""
    MARK_PRICE_SLOW = 619
    """Slower mark price update used in system calculations."""

    TRADING_RANGE = 165
    """Multi-week price and volume trading ranges."""

    TRADE_LAST_RTH = 318
    """Last regular trading hours traded price."""
    TRADE_COUNT = 293
    """Trade count for the day."""
    TRADE_COUNT_RATE = 294
    """Trade count per minute."""
    TRADE_VOLUME = 233
    """Trade volume for the day."""
    TRADE_VOLUME_NO_UNREPORTABLE = 375
    """Trade volume for the day that excludes "Unreportable Trades"."""
    TRADE_VOLUME_RATE = 295
    """Trade volume per minute."""
    TRADE_VOLUME_SHORT_TERM = 595
    """Short-term trading volume."""

    SHORTABLE = 236
    """Describes the level of difficulty with which the contract can be sold short."""
    SHORTABLE_SHARES = 236
    """Number of shares available to short."""

    FUTURE_OPEN_INTEREST = 588
    """Total number of outstanding futures contracts."""
    FUTURE_INDEX_PREMIUM = 162
    """Number of points that the index is over the cash index."""

    OPTION_VOLATILITY_HISTORICAL = 104
    """30-day historical volatility."""
    OPTION_VOLATILITY_HISTORICAL_REAL_TIME = 411
    """Real-time historical volatility."""
    OPTION_VOLATILITY_IMPLIED = 106
    """IB 30-day at-market volatility, estimated for a maturity thirty calendar days forward of the current trading day"""
    OPTION_VOLUME = 100
    """Option volume for the trading day."""
    OPTION_VOLUME_AVERAGE = 105
    """Average option volume for a trading day."""
    OPTION_OPEN_INTEREST = 101
    """Option open interest."""

    ETF_NAV_CLOSE = 578
    """ETF's Net Asset Value (NAV) closing price."""
    ETF_NAV_PRICE = 576
    """ETF's Net Asset Value (NAV) bid / ask price."""
    ETF_NAV_LAST = 577
    """ETF's Net Asset Value (NAV) last price."""
    ETF_NAV_LAST_FROZEN = 623
    """ETF's Net Asset Value (NAV) for frozen data."""
    ETF_NAV_RANGE = 614
    """ETF's Net Asset Value (NAV) price range."""

    BOND_FACTOR_MULTIPLIER = 460
    """Bond factor multiplier is a number that indicates the ratio of the current bond principal to the original principal."""


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

    value: str

    def __init__(self, value: str):
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


class Request:
    """ IB session request. """

    request_id: int
    cancel_func: Callable

    def __init__(self, request_id: int, cancel_func: Callable = None):
        self.request_id = request_id
        self.cancel_func = cancel_func

    def is_cancellable(self) -> None:
        """Is the request cancellable?"""
        return self.cancel_func is not None

    def cancel(self):
        """Cancel the request."""

        if not self.is_cancellable():
            raise Exception("Request is not cancellable.")

        self.cancel_func(self.request_id)


class RegisteredContract:
    """ Details describing a financial instrument that has been registered in the framework.  This can be a stock, bond, option, etc."""

    contract_details: ContractDetails

    def __init__(self, contract_details: ContractDetails):
        self.contract_details = contract_details


# TODO review API
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
        short_rates: interest rates for shorting securities


        ####
        # Accounts
        ####
        accounts_managed: accounts managed by the TWS session login.  Automatically populated.
        accounts_family_codes: account family.  Automatically populated.
        accounts_value: account values.  Automatically populated.
        accounts_portfolio: account holdings.  Automatically populated.
        accounts_summary: account summary.  Automatically populated.
        accounts_positions: account positions.  Automatically populated.
        accounts_pnl: account PNL requested via 'request_account_pnl'.

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

    _client: IbTwsClient

    def __init__(self):
        self._client = IbTwsClient()

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

    def _assert_connected(self):
        """Assert that the IbSessionTws is connected."""

        if not self.is_connected():
            raise Exception("IbSessionTws is not connected.")

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

    def get_registered_contract(self, contract: Contract) -> RegisteredContract:
        """Gets a contract that has been registered in the framework.  The registered contract is confirmed to
        exist in the IB system and contains a complete description of the contract.

        Args:
            contract (Contract): contract to search for

        Returns:
            RegisteredContract

        Raises:
              Exception
        """

        self._assert_connected()
        cd = self._client.contract_registry.request_contract_details_blocking(contract)
        return RegisteredContract(contract_details=cd)

    def request_contracts_matching(self, pattern: str) -> Request:
        """Request contracts matching a pattern.  Results are returned in the `contracts_matching` table.

        Args:
            pattern (str): pattern to search for.  Can include part of a ticker or part of the company name.

        Returns:
            Request

        Raises:
              Exception
        """

        self._assert_connected()
        req_id = next_unique_id()
        self._client.reqMatchingSymbols(reqId=req_id, pattern=pattern)
        return Request(request_id=req_id)

    ####################################################################################################################
    ####################################################################################################################
    ## Accounts
    ####################################################################################################################
    ####################################################################################################################

    # TODO request by default when pull accounts?
    def request_account_pnl(self, account: str = "All", model_code: str = "") -> Request:
        """Request PNL updates.  Results are returned in the `accounts_pnl` table.

        Args:
            account (str): Account to request PNL for.  "All" requests PNL for all accounts.
            model_code (str): Model used to evaluate PNL.

        Returns:
            Request

        Raises:
              Exception
        """

        self._assert_connected()
        req_id = next_unique_id()
        self._client.reqPnL(reqId=req_id, account=account, modelCode=model_code)
        return Request(request_id=req_id)

    ####################################################################################################################
    ####################################################################################################################
    ## News
    ####################################################################################################################
    ####################################################################################################################

    def request_news_historical(self, contract: RegisteredContract, provider_codes: str, start: dtu.DateTime,
                                end: dtu.DateTime,
                                total_results: int = 100) -> Request:
        """ Request historical news for a contract.  Results are returned in the `news_historical` table.

        Args:
            contract (RegisteredContract): contract data is requested for
            provider_codes (str): a '+'-separated list of provider codes
            start (DateTime): marks the (exclusive) start of the date range.
            end (DateTime): marks the (inclusive) end of the date range.
            total_results (int): the maximum number of headlines to fetch (1 - 300)

        Returns:
            Request

        Raises:
              Exception
        """

        self._assert_connected()
        req_id = next_unique_id()
        self._client.reqHistoricalNews(reqId=req_id, conId=contract.contract_details.contract.conId,
                                       providerCodes=provider_codes,
                                       startDateTime=dh_to_ib_datetime(start), endDateTime=dh_to_ib_datetime(end),
                                       totalResults=total_results, historicalNewsOptions=[])
        return Request(request_id=req_id)

    def request_news_article(self, provider_code: str, article_id: str) -> Request:
        """ Request the text of a news article.  Results are returned in the `news_articles` table.

        Args:
            provider_code (str): short code indicating news provider, e.g. FLY
            article_id (str): id of the specific article

        Returns:
            Request

        Raises:
              Exception
        """

        self._assert_connected()
        req_id = next_unique_id()
        self._client.reqNewsArticle(reqId=req_id, providerCode=provider_code, articleId=article_id,
                                    newsArticleOptions=[])
        return Request(request_id=req_id)

    ####################################################################################################################
    ####################################################################################################################
    ## Market Data
    ####################################################################################################################
    ####################################################################################################################

    def set_market_data_type(self, market_data_type: MarketDataType) -> None:
        """Sets the default type of market data.

        Args:
            market_data_type (MarketDataType): market data type

        Raises:
              Exception
        """

        self._assert_connected()
        self._client.reqMarketDataType(marketDataType=market_data_type.value)

    # noinspection PyDefaultArgument
    def request_market_data(self, contract: RegisteredContract, generic_tick_types: List[GenericTickType] = [],
                            snapshot: bool = False,
                            regulatory_snapshot: bool = False) -> Request:
        """ Request market data for a contract.  Results are returned in the `ticks_price`, `ticks_size`,
        `ticks_string`, `ticks_efp`, `ticks_generic`, and `ticks_option_computation` tables.


        Args:
            contract (RegisteredContract): contract data is requested for
            generic_tick_types (List[GenericTickType]): generic tick types being requested
            snapshot (bool): True to return a single snapshot of Market data and have the market data subscription cancel.
                Do not enter any genericTicklist values if you use snapshots.
            regulatory_snapshot (bool): True to get a regulatory snapshot.  Requires the US Value Snapshot Bundle for stocks.

        Returns:
            Request

        Raises:
              Exception
        """

        self._assert_connected()
        generic_tick_list = ",".join([x.value for x in generic_tick_types])
        req_id = next_unique_id()
        self._client.reqMktData(reqId=req_id, contract=contract.contract_details.contract,
                                genericTickList=generic_tick_list, snapshot=snapshot,
                                regulatorySnapshot=regulatory_snapshot, mktDataOptions=[])
        return Request(request_id=req_id, cancel_func=self._cancel_market_data)

    def _cancel_market_data(self, req_id: int):
        """Cancel a market data request.

        Args:
            req_id (int): request id

        Raises:
              Exception
        """

        self._assert_connected()
        self._client.cancelMktData(reqId=req_id)

    def request_bars_historical(self, contract: RegisteredContract, end: dtu.DateTime,
                                duration: Duration, bar_size: BarSize, bar_type: BarDataType,
                                market_data_type: MarketDataType = MarketDataType.FROZEN,
                                keep_up_to_date: bool = True) -> Request:
        """Requests historical bars for a contract.  Results are returned in the `bars_historical` table.

        Args:
            contract (RegisteredContract): contract data is requested for
            end (DateTime): Ending timestamp of the requested data.
            duration (Duration): Duration of data being requested by the query.
            bar_size (BarSize): Size of the bars that will be returned.
            bar_type (BarDataType): Type of bars that will be returned.
            market_data_type (MarketDataType): Type of market data to return after the close.
            keep_up_to_date (bool): True to continuously update bars

        Returns:
            Request

        Raises:
              Exception
        """

        self._assert_connected()
        req_id = next_unique_id()
        self._client.reqHistoricalData(reqId=req_id, contract=contract.contract_details.contract,
                                       endDateTime=dh_to_ib_datetime(end),
                                       durationStr=duration.value, barSizeSetting=bar_size.value,
                                       whatToShow=bar_type.name, useRTH=(market_data_type == MarketDataType.FROZEN),
                                       formatDate=2,
                                       keepUpToDate=keep_up_to_date, chartOptions=[])
        return Request(request_id=req_id)

    def request_bars_realtime(self, contract: RegisteredContract, bar_type: BarDataType, bar_size: int = 5,
                              market_data_type: MarketDataType = MarketDataType.FROZEN) -> Request:
        """Requests real time bars for a contract.  Results are returned in the `bars_realtime` table.

        Args:
            contract (RegisteredContract): contract data is requested for
            bar_type (BarDataType): Type of bars that will be returned.
            bar_size (int): Bar size in seconds.
            market_data_type (MarketDataType): Type of market data to return after the close.

        Returns:
            Request

        Raises:
              Exception
        """

        self._assert_connected()
        req_id = next_unique_id()
        self._client.reqRealTimeBars(reqId=req_id, contract=contract.contract_details.contract, barSize=bar_size,
                                     whatToShow=bar_type.name, useRTH=(market_data_type == MarketDataType.FROZEN),
                                     realTimeBarsOptions=[])
        return Request(request_id=req_id, cancel_func=self._cancel_bars_realtime)

    def _cancel_bars_realtime(self, req_id: int):
        """Cancel a real-time bar request.

        Args:
            req_id (int): request id


        Raises:
              Exception
        """

        self._assert_connected()
        self._client.cancelRealTimeBars(reqId=req_id)

    def request_tick_data_realtime(self, contract: RegisteredContract, tick_type: TickDataType,
                                   number_of_ticks: int = 0, ignore_size: bool = False) -> Request:
        """Requests real-time tick-by-tick data.  Results are returned in the ticks_trade`, `ticks_bid_ask`,
        and `ticks_mid_point` tables.

        Args:
            contract (RegisteredContract): contract data is requested for
            tick_type (TickDataType): Type of market data to return.
            number_of_ticks (int): Number of historical ticks to request.
            ignore_size (bool): should size values be ignored.

        Returns:
            Request

        Raises:
              Exception
        """

        self._assert_connected()
        req_id = next_unique_id()
        self._client.reqTickByTickData(reqId=req_id, contract=contract.contract_details.contract,
                                       tickType=tick_type.value,
                                       numberOfTicks=number_of_ticks, ignoreSize=ignore_size)
        return Request(request_id=req_id, cancel_func=self._cancel_tick_data_realtime)

    def _cancel_tick_data_realtime(self, req_id: int):
        """Cancel a real-time tick-by-tick data request.

        Args:
            req_id (int): request id


        Raises:
              Exception
        """

        self._assert_connected()
        self._client.cancelTickByTickData(reqId=req_id)

    def request_tick_data_historical(self, contract: RegisteredContract, start: dtu.DateTime, end: dtu.DateTime,
                                     tick_type: TickDataType, number_of_ticks: int,
                                     market_data_type: MarketDataType = MarketDataType.FROZEN,
                                     ignore_size: bool = False) -> Request:
        """Requests historical tick-by-tick data. Results are returned in the ticks_trade`, `ticks_bid_ask`,
        and `ticks_mid_point` tables.


        Args:
            contract (RegisteredContract): contract data is requested for
            start (DateTime): marks the (exclusive) start of the date range.
            end (DateTime): marks the (inclusive) end of the date range.
            tick_type (TickDataType): Type of market data to return.
            number_of_ticks (int): Number of historical ticks to request.
            market_data_type (MarketDataType): Type of market data to return after the close.
            ignore_size (bool): should size values be ignored.

        Returns:
            Request

        Raises:
              Exception
        """

        self._assert_connected()
        req_id = next_unique_id()
        what_to_show = tick_type._historical_value()
        self._client.reqHistoricalTicks(reqId=req_id, contract=contract.contract_details.contract,
                                        startDateTime=dh_to_ib_datetime(start),
                                        endDateTime=dh_to_ib_datetime(end),
                                        numberOfTicks=number_of_ticks, whatToShow=what_to_show,
                                        useRth=market_data_type.value,
                                        ignoreSize=ignore_size, miscOptions=[])
        return Request(request_id=req_id)

    ####################################################################################################################
    ####################################################################################################################
    ## Order Management System (OMS)
    ####################################################################################################################
    ####################################################################################################################

    def order_place(self, contract: RegisteredContract, order: Order) -> Request:
        """Places an order.

        Args:
            contract (RegisteredContract): contract to place an order on
            order (Order): order to place
        """
        self._assert_connected()
        req_id = next_unique_id()
        self._client.placeOrder(req_id, contract.contract_details.contract, order)
        return Request(request_id=req_id, cancel_func=self.order_cancel)

    def order_cancel(self, order_id: int) -> None:
        """Cancels an order.

        Args:
            order_id (int): order ID
        """

        self._assert_connected()
        self._client.cancelOrder(orderId=order_id)

    def order_cancel_all(self) -> None:
        """Cancel all open orders.

        Raises:
              Exception
        """

        self._assert_connected()
        self._client.reqGlobalCancel()

    # TODO:     self._client.reqIds() --> get next valid id for placing orders
    # TODO: (don't do)     self._client.reqPositionsMulti() --> req positions by account and model (needed only if >50 sub accounts because reqPositions will not work)
    # TODO: (don't do)     self._client.reqOpenOrders() --> reqAllOpenOrders gets orders that were not submitted by this session (needed?)