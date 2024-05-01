from enum import Enum
from typing import Union, Dict, List, Callable, Optional
import json
import datetime
import numpy
import pandas

from deephaven.table import Table
from deephaven.constants import NULL_DOUBLE
from deephaven.dtypes import Instant
from ibapi.contract import Contract, ContractDetails
from ibapi.order import Order

from ._tws import IbTwsClient
from ._tws.order_id_queue import OrderIdStrategy
from .time import to_ib_datetime

__all__ = ["MarketDataType", "TickDataType", "BarDataType", "BarSize", "Duration", "OrderIdStrategy",
           "Request", "RegisteredContract", "IbSessionTws"]


class MarketDataType(Enum):
    """Type of market data to use."""

    REAL_TIME = 1
    """Real-time market data."""
    FROZEN = 2
    """Real-time market data during regular trading hours, and frozen prices after the close."""
    DELAYED = 3
    """Delayed market data."""


class TickDataType(Enum):
    """Tick data type."""

    LAST = "Last"
    """Most recent trade."""
    BID_ASK = "BidAsk"
    """"Most recent bid and ask."""
    MIDPOINT = "MidPoint"
    """Most recent midpoint."""

    def historical_value(self) -> str:
        if self.value == "Last":
            return "Trades"
        else:
            return self.value


class GenericTickType(Enum):
    """Tick data types for 'Generic' data.

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
    """Trade prices."""
    MIDPOINT = 2
    """Midpoint prices."""
    BID = 3
    """Bid prices."""
    ASK = 4
    """Ask prices."""
    BID_ASK = 5
    """Bid/Ask prices."""
    ADJUSTED_LAST = 6
    """Bid/Ask prices."""
    HISTORICAL_VOLATILITY = 7
    """Historical volatility."""
    OPTION_IMPLIED_VOLATILITY = 8
    """Option implied volatility."""
    REBATE_RATE = 9
    """Rebate rate."""
    FEE_RATE = 10
    """Fee rate."""
    YIELD_BID = 11
    """Bid yield."""
    YIELD_ASK = 12
    """Ask yield."""
    YIELD_BID_ASK = 13
    """Bid/Ask yield."""
    YIELD_LAST = 14
    """Last yield."""
    AGGTRADES = 15
    """Aggregate trade prices."""

class BarSize(Enum):
    """Bar data sizes."""

    SEC_1 = "1 sec"
    """1 second bar."""
    SEC_5 = "5 secs"
    """5 second bar."""
    SEC_10 = "10 secs"
    """10 second bar."""
    SEC_15 = "15 secs"
    """15 second bar."""
    SEC_30 = "30 secs"
    """30 second bar."""
    MIN_1 = "1 min"
    """1 minute bar."""
    MIN_2 = "2 mins"
    """2 minute bar."""
    MIN_3 = "3 mins"
    """3 minute bar."""
    MIN_5 = "5 mins"
    "5 minute bar."
    MIN_10 = "10 mins"
    "10 minute bar."
    MIN_15 = "15 mins"
    """15 minute bar."""
    MIN_20 = "20 mins"
    "20 minute bar."
    MIN_30 = "30 mins"
    """30 minute bar."""
    HOUR_1 = "1 hour"
    """1 hour bar."""
    HOUR_2 = "2 hour"
    """2 hour bar."""
    HOUR_3 = "3 hour"
    """3 hour bar."""
    HOUR_4 = "4 hour"
    """4 hour bar."""
    HOUR_8 = "8 hour"
    """8 hour bar."""
    DAY_1 = "1 day"
    """1 day bar."""
    WEEK_1 = "1W"
    """1 week bar."""
    MONTH_1 = "1M"
    """1 month bar."""


class Duration:
    """Time period to request data for."""

    value: str

    def __init__(self, value: str):
        self.value = value

    @staticmethod
    def seconds(value: int) -> "Duration":
        """Create a duration of a specified number of seconds.

        Args:
            value (int): number of seconds

        Returns:
            A duration.
        """
        return Duration(f"{value} S")

    @staticmethod
    def days(value: int) -> "Duration":
        """Create a duration of a specified number of days.

        Args:
            value (int): number of days

        Returns:
            A duration.
        """
        return Duration(f"{value} D")

    @staticmethod
    def weeks(value: int) -> "Duration":
        """Create a duration of a specified number of weeks.

        Args:
            value (int): number of weeks

        Returns:
            A duration.
        """
        return Duration(f"{value} W")

    @staticmethod
    def months(value: int) -> "Duration":
        """Create a duration of a specified number of months.

        Args:
            value (int): number of months

        Returns:
            A duration.
        """
        return Duration(f"{value} M")

    @staticmethod
    def years(value: int) -> "Duration":
        """Create a duration of a specified number of years.

        Args:
            value (int): number of years

        Returns:
            A duration.
        """
        return Duration(f"{value} Y")

    def __repr__(self) -> str:
        return f"Duration('{self.value}')"


class Request:
    """ IB session request. """

    request_id: int
    _cancel_func: Callable

    def __init__(self, request_id: int, cancel_func: Callable = None):
        self.request_id = request_id
        self._cancel_func = cancel_func

    def is_cancellable(self) -> bool:
        """Is the request cancellable?

        Returns:
            An indication if the request is cancellable.
        """
        return self._cancel_func is not None

    def cancel(self) -> None:
        """Cancel the request.

        Returns:
            None

        Raises:
            Exception: request is not cancellable.
        """

        if not self.is_cancellable():
            raise Exception("Request is not cancellable.")

        self._cancel_func(self.request_id)


class RegisteredContract:
    """ Details describing a financial instrument that has been registered in the framework.  This can be a stock, bond, option, etc.

    When some contracts are registered, details on multiple contracts are returned.
    """

    query_contract: Contract
    contract_details: List[ContractDetails]

    def __init__(self, query_contract: Contract, contract_details: List[ContractDetails]):
        self.query_contract = query_contract
        self.contract_details = contract_details

    def is_multi(self) -> bool:
        """Does the contract have multiple contract details?

        Returns:
            An indication if the requested contract is associated with multiple contract details.
        """
        return len(self.contract_details) > 1

    def __repr__(self) -> str:
        return f"RegistredContract({self.query_contract},[{'|'.join([str(cd.contract) for cd in self.contract_details])}])"


class IbSessionTws:
    """ IB TWS session.

    **NOTE: Some tables are data specific to the current client_id (e.g. orders_submitted).  A client_id of 0 includes
    data manually entered into the TWS session.  For example, orders entered by hand.**
    
    Args:
        host (str): The host name or IP address of the machine where TWS is running. Leave blank to connect to the local host.
            When run inside docker, you probably want ``host.docker.internal``.
        port (int): TWS port, specified in TWS on the ``Configure->API->Socket Port`` field.
            By default production trading uses port 7496 and paper trading uses port 7497.
        client_id (int): A number used to identify this client connection.
            All orders placed/modified from this client will be associated with this client identifier.

            **NOTE: Each client MUST connect with a unique clientId.**
        download_short_rates (bool): True to download a short rates table.
        order_id_strategy (OrderIdStrategy): strategy for obtaining new order ids.
        read_only (bool): True to create a read only client that can not trade; false to create a read-write client that can trade.  Default is true.
        is_fa (bool): True for financial advisor accounts; false otherwise.  Default is false.


    Tables:
        ####
        # General
        ####
        * **errors**: an error log.
        * **requests**: requests to IB.

        ####
        # Contracts
        ####
        * **contract_details**: details describing contracts of interest.  Automatically populated.
        * **contracts_matching**: contracts matching query strings provided to ``request_contracts_matching``.
        * **market_rules**: market rules indicating the price increment a contract can trade in.  Automatically populated.
        * **short_rates**: interest rates for shorting securities.  Automatically populated if ``download_short_rates=True``.


        ####
        # Accounts
        ####
        * **accounts_managed**: accounts managed by the TWS session login.  Automatically populated.
        * **accounts_family_codes**: account family.  Automatically populated.
        * **accounts_groups**: account groups.  Automatically populated.
        * **accounts_allocation_profiles**: allocation profiles for accounts.  Automatically populated.
        * **accounts_value**: account values.  Automatically populated.
        * **accounts_overview**: overview of account details.  Automatically populated.
        * **accounts_summary**: account summary.  Automatically populated.
        * **accounts_positions**: account positions.  Automatically populated.
        * **accounts_pnl**: account PNL.  Automatically populated.

        ####
        # News
        ####

        * **news_providers**: currently subscribed news sources.  Automatically populated.
        * **news_bulletins**: news bulletins.  Automatically populated.
        * **news_articles**: the content of news articles requested via ``request_news_article``.
        * **news_historical**: historical news headlines requested via ``request_news_historical``.

        ####
        # Market Data
        ####

        * **ticks_price**: real-time tick market data of price values requested via ``request_market_data``.
        * **ticks_size**: real-time tick market data of size values requested via ``request_market_data``.
        * **ticks_string**: real-time tick market data of string values requested via ``request_market_data``.
        * **ticks_efp**: real-time tick market data of exchange for physical (EFP) values requested via ``request_market_data``.
        * **ticks_generic**: real-time tick market data of generic floating point values requested via ``request_market_data``.
        * **ticks_option_computation**: real-time tick market data of option computations requested via ``request_market_data``.
        * **ticks_trade**: real-time tick market data of trade prices requested via ``request_tick_data_historical`` or ``request_tick_data_realtime``.
        * **ticks_bid_ask**: real-time tick market data of bid and ask prices requested via ``request_tick_data_historical`` or ``request_tick_data_realtime``.
        * **ticks_mid_point**: real-time tick market data of mid-point prices requested via ``request_tick_data_historical`` or ``request_tick_data_realtime``.
        * **bars_historical**: historical price bars requested via ``request_bars_historical``.  Real-time bars change as new data arrives.
        * **bars_realtime**: real-time price bars requested via ``request_bars_realtime``.

        ####
        # Order Management System (OMS)
        ####

        * **orders_submitted**: submitted orders **FOR THE THE CLIENT ID**.  A client ID of 0 contains manually entered orders.  Automatically populated.
        * **orders_status**: order statuses.  Automatically populated.
        * **orders_completed**: completed orders.  Automatically populated.
        * **orders_exec_details**: order execution details.  Automatically populated.
        * **orders_exec_commission_report**: order execution commission report.  Automatically populated.
    """

    _host: str
    _port: int
    _client_id: int
    _read_only: bool
    _client: IbTwsClient
    _tables_raw: Dict[str, Table]
    _tables: Dict[str, Table]

    def __init__(self, host: str = "", port: int = 7497, client_id: int = 0, download_short_rates: bool = True, order_id_strategy: OrderIdStrategy = OrderIdStrategy.INCREMENT, read_only: bool = True, is_fa: bool = False):
        self._host = host
        self._port = port
        self._client_id = client_id
        self._read_only = read_only
        self._client = IbTwsClient(download_short_rates=download_short_rates, order_id_strategy=order_id_strategy, read_only=read_only, is_fa=is_fa)
        self._tables_raw = {f"raw_{k}": v for k, v in self._client.tables.items()}
        self._tables = dict(sorted(IbSessionTws._make_tables(self._tables_raw).items()))

    @property
    def host(self) -> str:
        """Client host.

        Returns:
            Client host.
        """
        return self._host

    @property
    def port(self) -> int:
        """Client port.

        Returns:
            Client port.
        """
        return self._port

    @property
    def client_id(self) -> int:
        """Client ID.

        Returns:
            Client ID.
        """
        return self._client_id

    @property
    def read_only(self) -> bool:
        """Is the client read only?

        Returns:
            a boolean indicating if the client is read only.
        """

    def __repr__(self) -> str:
        return f"IbSessionTws(host={self._host}, port={self._port}, client_id={self._client_id}, read_only={self._read_only})"

    ####################################################################################################################
    ####################################################################################################################
    ## Connect / Disconnect / Subscribe
    ####################################################################################################################
    ####################################################################################################################

    def connect(self) -> None:
        """Connect to an IB TWS session.  Raises an exception if already connected.

        Returns:
              None

        Raises:
              Exception: problem executing action.
        """

        self._client.connect(self._host, self._port, self._client_id)

    def disconnect(self) -> None:
        """Disconnect from an IB TWS session.

        Returns:
            None
        """

        self._client.disconnect()

    def is_connected(self) -> bool:
        """Is there a connection with TWS?

        Returns:
            an indication if the client is connected to TWS.
        """

        return self._client.isConnected()

    def _assert_connected(self) -> None:
        """Assert that the IbSessionTws is connected."""

        if not self.is_connected():
            raise Exception("IbSessionTws is not connected.")

    def _assert_read_write(self) -> None:
        """Assert that the IbSessionTws is read-write."""

        if self._read_only:
            raise Exception("IbSessionTws is read-only.  Set 'read_only=False' to enable read-write operations, such as trading.")

    ####################################################################################################################
    ####################################################################################################################
    ## General
    ####################################################################################################################
    ####################################################################################################################

    @staticmethod
    def _make_tables(tables_raw: Dict[str, Table]) -> Dict[str, Table]:
        def annotate_ticks(t):
            requests = tables_raw["raw_requests"] \
                .drop_columns(["ReceiveTime", "RequestType", "SecId", "SecIdType", "DeltaNeutralContract", "Note"])

            requests_col_names = [ c.name for c in requests.columns ]

            rst = t.natural_join(requests, on="RequestId").move_columns_up(requests_col_names)

            if "Timestamp" in [ c.name for c in rst.columns ]:
                if "TimestampEnd" in [ c.name for c in rst.columns ]:
                    rst = rst.move_columns_up(["RequestId", "ReceiveTime", "Timestamp", "TimestampEnd"])
                else:
                    rst = rst.move_columns_up(["RequestId", "ReceiveTime", "Timestamp"])
            else:
                rst = rst.move_columns_up(["RequestId", "ReceiveTime"])

            return rst

        def deephaven_ib_float_value(s: Optional[str]) -> Optional[float]:
            if not s:
                return NULL_DOUBLE

            try:
                return float(s)
            except ValueError:
                return NULL_DOUBLE

        def deephaven_ib_parse_note(note:str, key:str) -> Optional[str]:
            dict = json.loads(note)

            if key in dict:
                return dict[key]

            return None

        return {
            "requests": tables_raw["raw_requests"] \
                .move_columns_up(["RequestId", "ReceiveTime"]),
            "errors": tables_raw["raw_errors"] \
                .natural_join(tables_raw["raw_requests"] \
                             .drop_columns("Note").rename_columns("RequestTime=ReceiveTime"), on="RequestId") \
                .move_columns_up(["RequestId", "ReceiveTime"]),
            "contracts_details": tables_raw["raw_contracts_details"] \
                .move_columns_up(["RequestId", "ReceiveTime"]),
            "accounts_family_codes": tables_raw["raw_accounts_family_codes"] \
                .drop_columns("ReceiveTime"),
            "accounts_groups": tables_raw["raw_accounts_groups"] \
                .drop_columns("ReceiveTime"),
            "accounts_allocation_profiles": tables_raw["raw_accounts_allocation_profiles"] \
                .drop_columns("ReceiveTime"),
            "accounts_aliases": tables_raw["raw_accounts_aliases"] \
                .drop_columns("ReceiveTime"),
            "accounts_managed": tables_raw["raw_accounts_managed"] \
                .select_distinct("Account"),
            "accounts_positions": tables_raw["raw_accounts_positions"] \
                .last_by(["RequestId", "Account", "ModelCode", "ContractId"]) \
                .move_columns_up(["RequestId", "ReceiveTime"]),
            "accounts_overview": tables_raw["raw_accounts_overview"] \
                .last_by(["RequestId", "Account", "Currency", "Key"]) \
                .update("DoubleValue = (double)deephaven_ib_float_value(Value)") \
                .move_columns_up(["RequestId", "ReceiveTime"]),
            "accounts_summary": tables_raw["raw_accounts_summary"] \
                .natural_join(tables_raw["raw_requests"], on="RequestId", joins="Note") \
                .update("GroupName=(String)deephaven_ib_parse_note(Note,`groupName`)") \
                .drop_columns("Note") \
                .update("DoubleValue = (double)deephaven_ib_float_value(Value)") \
                .last_by(["RequestId", "GroupName", "Account", "Tag"]) \
                .move_columns_up(["RequestId", "ReceiveTime", "GroupName"]),
            "accounts_pnl": tables_raw["raw_accounts_pnl"] \
                .natural_join(tables_raw["raw_requests"], on="RequestId", joins="Note") \
                .update([
                    "Account=(String)deephaven_ib_parse_note(Note,`account`)",
                    "ModelCode=(String)deephaven_ib_parse_note(Note,`model_code`)"]) \
                .move_columns_up(["RequestId", "ReceiveTime", "Account", "ModelCode"]) \
                .drop_columns("Note") \
                .last_by("RequestId"),
            "contracts_matching": tables_raw["raw_contracts_matching"] \
                .natural_join(tables_raw["raw_requests"], on="RequestId", joins="Pattern=Note") \
                .move_columns_up(["RequestId", "ReceiveTime", "Pattern"]) \
                .update("Pattern=(String)deephaven_ib_parse_note(Pattern,`pattern`)"),
            "market_rules": tables_raw["raw_market_rules"].select_distinct(["MarketRuleId", "LowEdge", "Increment"]),
            "news_bulletins": tables_raw["raw_news_bulletins"],
            "news_providers": tables_raw["raw_news_providers"] \
                .drop_columns("ReceiveTime"),
            "news_articles": tables_raw["raw_news_articles"] \
                .move_columns_up(["RequestId", "ReceiveTime"]),
            "news_historical": tables_raw["raw_news_historical"] \
                .natural_join(tables_raw["raw_requests"], on="RequestId", joins=["ContractId","SecType","Symbol","LocalSymbol"]) \
                .move_columns_up(["RequestId", "ReceiveTime", "Timestamp", "ContractId", "SecType", "Symbol",
                               "LocalSymbol"]),
            "orders_completed": tables_raw["raw_orders_completed"] \
                .move_columns_up(["ReceiveTime", "OrderId", "ClientId", "PermId", "ParentId"]),
            "orders_exec_commission_report": tables_raw["raw_orders_exec_commission_report"],
            "orders_exec_details": tables_raw["raw_orders_exec_details"] \
                .move_columns_up(["RequestId", "ReceiveTime", "Timestamp", "ExecId", "AcctNumber"]) \
                .rename_columns("Account=AcctNumber"),
            # The status on raw_orders_submitted is buggy, so using the status from raw_orders_status
            "orders_submitted": tables_raw["raw_orders_submitted"] \
                .last_by("PermId") \
                .drop_columns("Status") \
                .natural_join(tables_raw["raw_orders_status"].last_by("PermId"), on="PermId", joins="Status")
                .move_columns_up(["ReceiveTime", "Account", "ModelCode", "PermId", "ClientId", "OrderId", "ParentId",
                               "Status"]),
            "orders_status": tables_raw["raw_orders_status"] \
                .last_by("PermId") \
                .move_columns_up(["ReceiveTime", "PermId", "ClientId", "OrderId", "ParentId"]),
            "bars_historical": annotate_ticks(tables_raw["raw_bars_historical"]).last_by(["RequestId", "Timestamp", "ContractId"]),
            "bars_realtime": annotate_ticks(tables_raw["raw_bars_realtime"]),
            "ticks_efp": annotate_ticks(tables_raw["raw_ticks_efp"]),
            "ticks_generic": annotate_ticks(tables_raw["raw_ticks_generic"]),
            "ticks_mid_point": annotate_ticks(tables_raw["raw_ticks_mid_point"]),
            "ticks_option_computation": annotate_ticks(tables_raw["raw_ticks_option_computation"]),
            "ticks_price": annotate_ticks(tables_raw["raw_ticks_price"]),
            "ticks_size": annotate_ticks(tables_raw["raw_ticks_size"]),
            "ticks_string": annotate_ticks(tables_raw["raw_ticks_string"]),
            "ticks_trade": annotate_ticks(tables_raw["raw_ticks_trade"] \
                                          .rename_columns("TradeExchange=Exchange")),
            "ticks_bid_ask": annotate_ticks(tables_raw["raw_ticks_bid_ask"]),
        }


    @property
    def tables(self) -> Dict[str, Table]:
        """Gets a dictionary of all data tables.

        Returns:
            Dictionary of all data tables.
        """
        return self._tables

    @property
    def tables_raw(self) -> Dict[str, Table]:
        """Gets a dictionary of all raw data tables.  Raw tables are just as the data comes from IB.

        Returns:
            Dictionary of all raw data tables.
        """
        return self._tables_raw

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
            A contract that has been registered with deephaven-ib.

        Raises:
              Exception: problem executing action.
        """

        self._assert_connected()

        try:
            cd = self._client.contract_registry.request_contract_details_blocking(contract)
            return RegisteredContract(query_contract=contract, contract_details=cd)
        except Exception as e:
            raise Exception(f"Error getting registered contract: contract={contract} {e}")

    def request_contracts_matching(self, pattern: str) -> Request:
        """Request contracts matching a pattern.  Results are returned in the ``contracts_matching`` table.

        Args:
            pattern (str): pattern to search for.  Can include part of a ticker or part of the company name.

        Returns:
            A Request.

        Raises:
              Exception: problem executing action.
        """

        self._assert_connected()
        req_id = self._client.request_id_manager.next_id()
        self._client.log_request(req_id, "MatchingSymbols", None, {"pattern": pattern})
        self._client.reqMatchingSymbols(reqId=req_id, pattern=pattern)
        return Request(request_id=req_id)

    ####################################################################################################################
    ####################################################################################################################
    ## Accounts
    ####################################################################################################################
    ####################################################################################################################

    def request_account_pnl(self, account: str = "All", model_code: str = "") -> Request:
        """Request PNL updates.  Results are returned in the ``accounts_pnl`` table.

        Args:
            account (str): Account to request PNL for.  "All" requests for all accounts.
            model_code (str): Model portfolio code to request PNL for.

        Returns:
            A Request.

        Raises:
              Exception: problem executing action.
        """

        self._assert_connected()
        req_id = self._client.request_account_pnl(account, model_code)
        return Request(request_id=req_id)

    def request_account_overview(self, account: str, model_code: str = "") -> Request:
        """Request portfolio overview updates.  Results are returned in the ``accounts_overview`` table.

        Args:
            account (str): Account to request an overview for.  "All" requests for all accounts.
            model_code (str): Model portfolio code to request an overview for.

        Returns:
            A Request.

        Raises:
              Exception: problem executing action.
        """
        self._assert_connected()
        req_id = self._client.request_account_overview(account, model_code)
        return Request(request_id=req_id)

    def request_account_positions(self, account: str, model_code: str = "") -> Request:
        """Request portfolio position updates.  Results are returned in the ``accounts_positions`` table.

        Args:
            account (str): Account to request positions for.  "All" requests for all accounts.
            model_code (str): Model portfolio code to request positions for.

        Returns:
            A Request.

        Raises:
              Exception: problem executing action.
        """
        self._assert_connected()
        req_id = self._client.request_account_positions(account, model_code)
        return Request(request_id=req_id)


    ####################################################################################################################
    ####################################################################################################################
    ## News
    ####################################################################################################################
    ####################################################################################################################

    def request_news_historical(self, contract: RegisteredContract,
                                start: Union[None, Instant, int, str, datetime.datetime, numpy.datetime64, pandas.Timestamp],
                                end: Union[None, Instant, int, str, datetime.datetime, numpy.datetime64, pandas.Timestamp],
                                provider_codes: List[str] = None, total_results: int = 100) -> List[Request]:
        """ Request historical news for a contract.  Results are returned in the ``news_historical`` table.

        Registered contracts that are associated with multiple contract details produce multiple requests.

        Args:
            contract (RegisteredContract): contract data is requested for
            provider_codes (List[str]): a list of provider codes.  By default, all subscribed codes are used.
            start (Union[None, Instant, int, str, datetime.datetime, numpy.datetime64, pandas.Timestamp]): marks the (exclusive) start of the date range.  See https://deephaven.io/core/pydoc/code/deephaven.time.html#deephaven.time.to_j_instant for supported inputs.
            end (Union[None, Instant, int, str, datetime.datetime, numpy.datetime64, pandas.Timestamp]): marks the (inclusive) end of the date range.  See https://deephaven.io/core/pydoc/code/deephaven.time.html#deephaven.time.to_j_instant for supported inputs.
            total_results (int): the maximum number of headlines to fetch (1 - 300)

        Returns:
            All of the requests created by the action.

        Raises:
              Exception: problem executing action.
        """

        self._assert_connected()

        if not provider_codes:
            provider_codes = self._client.news_providers

        pc = "+".join(provider_codes)
        requests = []

        for cd in contract.contract_details:
            req_id = self._client.request_id_manager.next_id()
            self._client.log_request(req_id, "HistoricalNews", cd.contract,
                                     {"provider_codes": provider_codes, "start": start, "end": end,
                                      "total_results": total_results})
            self._client.reqHistoricalNews(reqId=req_id, conId=cd.contract.conId, providerCodes=pc,
                                           startDateTime=to_ib_datetime(start, sub_sec=False),
                                           endDateTime=to_ib_datetime(end, sub_sec=False),
                                           totalResults=total_results, historicalNewsOptions=[])
            requests.append(Request(request_id=req_id))

        return requests

    def request_news_article(self, provider_code: str, article_id: str) -> Request:
        """ Request the text of a news article.  Results are returned in the ``news_articles`` table.

        Args:
            provider_code (str): short code indicating news provider, e.g. FLY
            article_id (str): id of the specific article

        Returns:
            A Request.

        Raises:
              Exception: problem executing action.
        """

        self._assert_connected()
        req_id = self._client.request_id_manager.next_id()
        self._client.log_request(req_id, "NewsArticle", None,
                                 {f"provider_code": provider_code, "article_id": article_id})
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

        Returns:
            None

        Raises:
              Exception: problem executing action.
        """

        self._assert_connected()
        self._client.reqMarketDataType(marketDataType=market_data_type.value)

    # noinspection PyDefaultArgument
    def request_market_data(self, contract: RegisteredContract, generic_tick_types: List[GenericTickType] = [],
                            snapshot: bool = False, regulatory_snapshot: bool = False) -> List[Request]:
        """ Request market data for a contract.  Results are returned in the ``ticks_price``, ``ticks_size``,
        ``ticks_string``, ``ticks_efp``, ``ticks_generic``, and ``ticks_option_computation`` tables.

        Registered contracts that are associated with multiple contract details produce multiple requests.


        Args:
            contract (RegisteredContract): contract data is requested for
            generic_tick_types (List[GenericTickType]): generic tick types being requested
            snapshot (bool): True to return a single snapshot of Market data and have the market data subscription cancel.
                Do not enter any genericTicklist values if you use snapshots.
            regulatory_snapshot (bool): True to get a regulatory snapshot.  Requires the US Value Snapshot Bundle for stocks.

        Returns:
            A Request.

        Raises:
              Exception: problem executing action.
        """

        self._assert_connected()
        generic_tick_list = ",".join([str(x.value) for x in generic_tick_types])
        requests = []

        for cd in contract.contract_details:
            req_id = self._client.request_id_manager.next_id()
            self._client.log_request(req_id, "MarketData", cd.contract,
                                     {"generic_tick_types": generic_tick_types, "snapshot": snapshot,
                                      "regulatory_snapshot": regulatory_snapshot})
            self._client.reqMktData(reqId=req_id, contract=cd.contract,
                                    genericTickList=generic_tick_list, snapshot=snapshot,
                                    regulatorySnapshot=regulatory_snapshot, mktDataOptions=[])
            requests.append(Request(request_id=req_id, cancel_func=self._cancel_market_data))

        return requests

    def _cancel_market_data(self, req_id: int) -> None:
        """Cancel a market data request.

        Args:
            req_id (int): request id

        Returns:
            None

        Raises:
              Exception: problem executing action.
        """

        self._assert_connected()
        self._client.cancelMktData(reqId=req_id)

    def request_bars_historical(self, contract: RegisteredContract,
                                duration: Duration, bar_size: BarSize, bar_type: BarDataType,
                                end: Union[None, Instant, int, str, datetime.datetime, numpy.datetime64, pandas.Timestamp] = None,
                                market_data_type: MarketDataType = MarketDataType.FROZEN,
                                keep_up_to_date: bool = True) -> List[Request]:
        """Requests historical bars for a contract.  Results are returned in the ``bars_historical`` table.

        Registered contracts that are associated with multiple contract details produce multiple requests.

        Args:
            contract (RegisteredContract): contract data is requested for
            end (Union[None, Instant, int, str, datetime.datetime, numpy.datetime64, pandas.Timestamp]): Ending timestamp of the requested data.  See https://deephaven.io/core/pydoc/code/deephaven.time.html#deephaven.time.to_j_instant for supported inputs.
            duration (Duration): Duration of data being requested by the query.
            bar_size (BarSize): Size of the bars that will be returned.
            bar_type (BarDataType): Type of bars that will be returned.
            market_data_type (MarketDataType): Type of market data to return after the close.
            keep_up_to_date (bool): True to continuously update bars

        Returns:
            All of the requests created by this action.

        Raises:
              Exception: problem executing action.
        """

        self._assert_connected()
        requests = []

        for cd in contract.contract_details:
            req_id = self._client.request_id_manager.next_id()
            self._client.log_request(req_id, "HistoricalData", cd.contract,
                                     {
                                         "end": end,
                                         "duration": duration,
                                         "bar_size": bar_size,
                                         "bar_type": bar_type,
                                         "market_data_type": market_data_type,
                                         "keep_up_to_date": keep_up_to_date,
                                     })
            self._client.reqHistoricalData(reqId=req_id, contract=cd.contract,
                                           endDateTime=to_ib_datetime(end, sub_sec=False),
                                           durationStr=duration.value, barSizeSetting=bar_size.value,
                                           whatToShow=bar_type.name, useRTH=(market_data_type == MarketDataType.FROZEN),
                                           formatDate=2, keepUpToDate=keep_up_to_date, chartOptions=[])
            requests.append(Request(request_id=req_id))

        return requests

    def request_bars_realtime(self, contract: RegisteredContract, bar_type: BarDataType, bar_size: int = 5,
                              market_data_type: MarketDataType = MarketDataType.FROZEN) -> List[Request]:
        """Requests real time bars for a contract.  Results are returned in the ``bars_realtime`` table.

        Registered contracts that are associated with multiple contract details produce multiple requests.

        Args:
            contract (RegisteredContract): contract data is requested for
            bar_type (BarDataType): Type of bars that will be returned.
            bar_size (int): Bar size in seconds.
            market_data_type (MarketDataType): Type of market data to return after the close.

        Returns:
            All of the requests created by this action.

        Raises:
              Exception: problem executing action.
        """

        self._assert_connected()
        requests = []

        if bar_type not in [BarDataType.TRADES, BarDataType.AGGTRADES, BarDataType.MIDPOINT, BarDataType.BID, BarDataType.ASK]:
            raise Exception(f"Unsupported bar type: {bar_type}")

        for cd in contract.contract_details:
            req_id = self._client.request_id_manager.next_id()
            self._client.log_request(req_id, "RealTimeBars", cd.contract,
                                     {"bar_type": bar_type, "bar_size": bar_size, "market_data_type": market_data_type})
            self._client.reqRealTimeBars(reqId=req_id, contract=cd.contract, barSize=bar_size,
                                         whatToShow=bar_type.name, useRTH=(market_data_type == MarketDataType.FROZEN),
                                         realTimeBarsOptions=[])
            requests.append(Request(request_id=req_id, cancel_func=self._cancel_bars_realtime))

        return requests

    def _cancel_bars_realtime(self, req_id: int) -> None:
        """Cancel a real-time bar request.

        Args:
            req_id (int): request id

        Returns:
            None

        Raises:
              Exception: problem executing action.
        """

        self._assert_connected()
        self._client.cancelRealTimeBars(reqId=req_id)

    def request_tick_data_realtime(self, contract: RegisteredContract, tick_type: TickDataType,
                                   number_of_ticks: int = 0, ignore_size: bool = False) -> List[Request]:
        """Requests real-time tick-by-tick data.  Results are returned in the ``ticks_trade``, ``ticks_bid_ask``,
        and ``ticks_mid_point`` tables.

        Registered contracts that are associated with multiple contract details produce multiple requests.

        Args:
            contract (RegisteredContract): contract data is requested for
            tick_type (TickDataType): Type of market data to return.
            number_of_ticks (int): Number of historical ticks to request.
            ignore_size (bool): should size values be ignored.

        Returns:
            All of the requests created by this action.

        Raises:
              Exception: problem executing action.
        """

        self._assert_connected()
        requests = []

        for cd in contract.contract_details:
            req_id = self._client.request_id_manager.next_id()
            self._client.log_request(req_id, "TickByTickData", cd.contract,
                                     {"tick_type": tick_type, "number_of_ticks": number_of_ticks,
                                      "ignore_size": ignore_size})
            self._client.reqTickByTickData(reqId=req_id, contract=cd.contract,
                                           tickType=tick_type.value,
                                           numberOfTicks=number_of_ticks, ignoreSize=ignore_size)
            requests.append(Request(request_id=req_id, cancel_func=self._cancel_tick_data_realtime))

        return requests

    def _cancel_tick_data_realtime(self, req_id: int) -> None:
        """Cancel a real-time tick-by-tick data request.

        Args:
            req_id (int): request id

        Returns:
            None

        Raises:
              Exception: problem executing action.
        """

        self._assert_connected()
        self._client.cancelTickByTickData(reqId=req_id)

    def request_tick_data_historical(self, contract: RegisteredContract,
                                     tick_type: TickDataType, number_of_ticks: int,
                                     start: Union[None, Instant, int, str, datetime.datetime, numpy.datetime64, pandas.Timestamp] = None,
                                     end: Union[None, Instant, int, str, datetime.datetime, numpy.datetime64, pandas.Timestamp] = None,
                                     market_data_type: MarketDataType = MarketDataType.FROZEN,
                                     ignore_size: bool = False) -> List[Request]:
        """Requests historical tick-by-tick data. Results are returned in the ``ticks_trade``, ``ticks_bid_ask``,
        and ``ticks_mid_point`` tables.

        Registered contracts that are associated with multiple contract details produce multiple requests.

        Args:
            contract (RegisteredContract): contract data is requested for
            start (Union[None, Instant, int, str, datetime.datetime, numpy.datetime64, pandas.Timestamp]): marks the (exclusive) start of the date range.  See https://deephaven.io/core/pydoc/code/deephaven.time.html#deephaven.time.to_j_instant for supported inputs.
            end (Union[None, Instant, int, str, datetime.datetime, numpy.datetime64, pandas.Timestamp]): marks the (inclusive) end of the date range.  See https://deephaven.io/core/pydoc/code/deephaven.time.html#deephaven.time.to_j_instant for supported inputs.
            tick_type (TickDataType): Type of market data to return.
            number_of_ticks (int): Number of historical ticks to request.
            market_data_type (MarketDataType): Type of market data to return after the close.
            ignore_size (bool): should size values be ignored.

        Returns:
            All of the requests created by this action.

        Raises:
              Exception: problem executing action.
        """

        self._assert_connected()
        what_to_show = tick_type.historical_value()
        requests = []

        if tick_type not in [TickDataType.MIDPOINT, TickDataType.LAST]:
            raise Exception(f"Unsupported tick data type: {tick_type}")

        for cd in contract.contract_details:
            req_id = self._client.request_id_manager.next_id()
            self._client.log_request(req_id, "HistoricalTicks", cd.contract,
                                     {"start": start,
                                      "end": end,
                                      "tick_type": tick_type,
                                      "number_of_ticks": number_of_ticks,
                                      "market_data_type": market_data_type,
                                      "ignore_size": ignore_size,
                                      })
            self._client.reqHistoricalTicks(reqId=req_id, contract=cd.contract,
                                            startDateTime=to_ib_datetime(start, sub_sec=False),
                                            endDateTime=to_ib_datetime(end, sub_sec=False),
                                            numberOfTicks=number_of_ticks, whatToShow=what_to_show,
                                            useRth=market_data_type.value,
                                            ignoreSize=ignore_size, miscOptions=[])
            requests.append(Request(request_id=req_id))

        return requests

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

        Returns:
            A Request.

        Raises:
              Exception: problem executing action.
        """
        self._assert_connected()
        self._assert_read_write()

        if contract.is_multi():
            raise Exception(
                f"RegisteredContracts with multiple contract details are not supported for orders: {contract}")

        req_id = self._client.next_order_id()
        cd = contract.contract_details[0]
        self._client.log_request(req_id, "PlaceOrder", cd.contract, {"order": f"Order({order})"})
        self._client.placeOrder(req_id, cd.contract, order)
        return Request(request_id=req_id, cancel_func=self.order_cancel)

    def order_cancel(self, order_id: int) -> None:
        """Cancels an order.

        Args:
            order_id (int): order ID

        Returns:
            None

        Raises:
              Exception: problem executing action.
        """

        self._assert_connected()
        self._assert_read_write()
        self._client.cancelOrder(orderId=order_id, manualCancelOrderTime="")

    def order_cancel_all(self) -> None:
        """Cancel all open orders.

        Returns:
            None

        Raises:
              Exception: problem executing action.
        """

        self._assert_connected()
        self._assert_read_write()
        self._client.reqGlobalCancel()

