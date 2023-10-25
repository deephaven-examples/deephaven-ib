"""An IB TWS client that produces Deephaven tables."""

import html
import json
import logging
import time
import types
# noinspection PyPep8Naming
import xml.etree.ElementTree as ET
from functools import wraps
from threading import Thread
from typing import Set, Optional

import decimal
from decimal import Decimal

from deephaven.table import Table
from deephaven import dtypes

from ibapi import news
from ibapi.client import EClient
from ibapi.commission_report import CommissionReport
from ibapi.common import *
from ibapi.contract import Contract, ContractDetails
from ibapi.execution import Execution, ExecutionFilter
from ibapi.order import Order
from ibapi.order_state import OrderState
from ibapi.ticktype import TickType, TickTypeEnum
from ibapi.wrapper import EWrapper
from ratelimit import limits, sleep_and_retry

from .contract_registry import ContractRegistry
from .ib_type_logger import *
from .order_id_queue import OrderIdEventQueue, OrderIdStrategy
from .requests import RequestIdManager
from .._internal.error_codes import load_error_codes
from .._internal.short_rates import load_short_rates
from .._internal.tablewriter import TableWriter
from ..time import unix_sec_to_j_instant

_error_code_message_map, _error_code_note_map = load_error_codes()
_news_msgtype_map: Dict[int, str] = {news.NEWS_MSG: "NEWS", news.EXCHANGE_AVAIL_MSG: "EXCHANGE_AVAILABLE",
                                     news.EXCHANGE_UNAVAIL_MSG: "EXCHANGE_UNAVAILABLE"}


# Rate limit is 50 per second.  Limiting to 45 per second.
@sleep_and_retry
@limits(calls=45, period=1)
def _check_rate_limit():
    """Empty function to limit the rate of calls to API."""
    pass


def _rate_limit_wrapper(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        _check_rate_limit()
        return func(*args, **kwargs)

    return wrapped


# noinspection PyPep8Naming
class IbTwsClient(EWrapper, EClient):
    """A client for communicating with IB TWS.

    Almost all of the methods in this class are listeners for EWrapper and should not be called directly by users of the class.
    """

    _table_writers: Dict[str, TableWriter]
    tables: Dict[str, Table]
    _thread: Thread
    contract_registry: ContractRegistry
    request_id_manager: RequestIdManager
    order_id_queue: OrderIdEventQueue
    _registered_market_rules: Set[str]
    _realtime_bar_sizes: Dict[TickerId, int]
    news_providers: List[str]
    _accounts_managed: Set[str]
    _order_id_strategy: OrderIdStrategy
    _read_only: bool
    _is_fa: bool

    def __init__(self, download_short_rates: bool, order_id_strategy: OrderIdStrategy, read_only: bool, is_fa: bool):
        EWrapper.__init__(self)
        EClient.__init__(self, wrapper=self)
        self._table_writers = IbTwsClient._build_table_writers()
        self._thread = None
        self.contract_registry = None
        self.request_id_manager = RequestIdManager()
        self.order_id_queue = None
        self._registered_market_rules = None
        self._realtime_bar_sizes = None
        self.news_providers = None
        self._accounts_managed = None
        self._order_id_strategy = order_id_strategy
        self._read_only = read_only
        self._is_fa = is_fa

        tables = {name: tw.table() for (name, tw) in self._table_writers.items()}

        if download_short_rates:
            tables["short_rates"] = load_short_rates()

        self.tables = dict(sorted(tables.items()))

    # wrap all method names starting with "req" with a rate limiter.
    def __getattribute__(self, name):
        attr = EClient.__getattribute__(self, name)
        if type(attr) == types.MethodType and name.startswith("req"):
            attr = _rate_limit_wrapper(attr)
            return attr
        else:
            return attr

    @staticmethod
    def _build_table_writers() -> Dict[str, TableWriter]:
        # noinspection PyDictCreation
        table_writers = {}

        ####
        # General
        ####

        table_writers["requests"] = TableWriter(["RequestId", "RequestType", *logger_contract.names(), "Note"],
                                                [dtypes.int64, dtypes.string, *logger_contract.types(), dtypes.string])

        table_writers["errors"] = TableWriter(
            ["RequestId", "ErrorCode", "ErrorDescription", "Error", "Note"],
            [dtypes.int64, dtypes.int64, dtypes.string, dtypes.string, dtypes.string])

        ####
        # Contracts
        ####

        table_writers["contracts_details"] = TableWriter(
            ["RequestId", *logger_contract_details.names()],
            [dtypes.int64, *logger_contract_details.types()])

        table_writers["contracts_matching"] = TableWriter(
            ["RequestId", *logger_contract.names(), "DerivativeSecTypes"],
            [dtypes.int64, *logger_contract.types(), dtypes.StringSet])

        table_writers["market_rules"] = TableWriter(
            ["MarketRuleId", *logger_price_increment.names()],
            [dtypes.string, *logger_price_increment.types()])

        ####
        # Accounts
        ####

        table_writers["accounts_managed"] = TableWriter(["Account"], [dtypes.string])

        table_writers["accounts_family_codes"] = TableWriter(
            [*logger_family_code.names()],
            [*logger_family_code.types()])

        table_writers["accounts_groups"] = TableWriter(
            ["GroupName", "DefaultMethod", "Account"],
            [dtypes.string, dtypes.string, dtypes.string])

        table_writers["accounts_allocation_profiles"] = TableWriter(
            ["AllocationProfileName", "Type", "Account", "Amount"],
            [dtypes.string, dtypes.string, dtypes.string, dtypes.float64])

        table_writers["accounts_aliases"] = TableWriter(
            ["Account", "Alias"],
            [dtypes.string, dtypes.string])

        table_writers["accounts_overview"] = TableWriter(
            ["RequestId", "Account", "ModelCode", "Currency", "Key", "Value"],
            [dtypes.int64, dtypes.string, dtypes.string, dtypes.string, dtypes.string, dtypes.string])

        table_writers["accounts_summary"] = TableWriter(
            ["RequestId", "Account", "Tag", "Value", "Currency"],
            [dtypes.int64, dtypes.string, dtypes.string, dtypes.string, dtypes.string])

        table_writers["accounts_positions"] = TableWriter(
            ["RequestId", "Account", "ModelCode", *logger_contract.names(), "Position", "AvgCost"],
            [dtypes.int64, dtypes.string, dtypes.string, *logger_contract.types(), dtypes.float64, dtypes.float64])

        table_writers["accounts_pnl"] = TableWriter(
            ["RequestId", "DailyPnl", "UnrealizedPnl", "RealizedPnl"],
            [dtypes.int64, dtypes.float64, dtypes.float64, dtypes.float64])

        ####
        # News
        ####

        table_writers["news_providers"] = TableWriter(logger_news_provider.names(), logger_news_provider.types())

        table_writers["news_bulletins"] = TableWriter(
            ["MsgId", "MsgType", "Message", "OriginExch"],
            [dtypes.int64, dtypes.string, dtypes.string, dtypes.string])

        table_writers["news_articles"] = TableWriter(
            ["RequestId", "ArticleType", "ArticleText"],
            [dtypes.int64, dtypes.string, dtypes.string])

        table_writers["news_historical"] = TableWriter(
            ["RequestId", "Timestamp", "ProviderCode", "ArticleId", "Headline"],
            [dtypes.int64, dtypes.Instant, dtypes.string, dtypes.string, dtypes.string])

        ####
        # Market Data
        ####

        table_writers["ticks_price"] = TableWriter(
            ["RequestId", "TickType", "Price", *logger_tick_attrib.names()],
            [dtypes.int64, dtypes.string, dtypes.float64, *logger_tick_attrib.types()])

        table_writers["ticks_size"] = TableWriter(
            ["RequestId", "TickType", "Size"],
            [dtypes.int64, dtypes.string, dtypes.float64])

        table_writers["ticks_string"] = TableWriter(
            ["RequestId", "TickType", "Value"],
            [dtypes.int64, dtypes.string, dtypes.string])

        # exchange for physical
        table_writers["ticks_efp"] = TableWriter(
            ["RequestId", "TickType", "BasisPoints", "FormattedBasisPoints", "TotalDividends", "HoldDays",
             "FutureLastTradeDate", "DividendImpact", "DividendsToLastTradeDate"],
            [dtypes.int64, dtypes.string, dtypes.float64, dtypes.string, dtypes.float64, dtypes.int64,
             dtypes.string, dtypes.float64, dtypes.float64])

        table_writers["ticks_generic"] = TableWriter(
            ["RequestId", "TickType", "Value"],
            [dtypes.int64, dtypes.string, dtypes.float64])

        table_writers["ticks_option_computation"] = TableWriter(
            ["RequestId", "TickType", "TickAttrib", "ImpliedVol", "Delta", "OptPrice", "PvDividend", "Gamma",
             "Vega", "Theta", "UndPrice"],
            [dtypes.int64, dtypes.string, dtypes.string, dtypes.float64, dtypes.float64, dtypes.float64, dtypes.float64, dtypes.float64,
             dtypes.float64, dtypes.float64, dtypes.float64])

        table_writers["ticks_trade"] = TableWriter(
            ["RequestId", *logger_hist_tick_last.names()],
            [dtypes.int64, *logger_hist_tick_last.types()])

        table_writers["ticks_bid_ask"] = TableWriter(
            ["RequestId", *logger_hist_tick_bid_ask.names()],
            [dtypes.int64, *logger_hist_tick_bid_ask.types()])

        table_writers["ticks_mid_point"] = TableWriter(
            ["RequestId", "Timestamp", "MidPoint"],
            [dtypes.int64, dtypes.Instant, dtypes.float64])

        table_writers["bars_historical"] = TableWriter(
            ["RequestId", *logger_bar_data.names()],
            [dtypes.int64, *logger_bar_data.types()])

        table_writers["bars_realtime"] = TableWriter(
            ["RequestId", *logger_real_time_bar_data.names()],
            [dtypes.int64, *logger_real_time_bar_data.types()])

        ####
        # Order Management System (OMS)
        ####

        table_writers["orders_submitted"] = TableWriter(
            [*logger_contract.names(), *logger_order.names(), *logger_order_state.names()],
            [*logger_contract.types(), *logger_order.types(), *logger_order_state.types()])

        table_writers["orders_status"] = TableWriter(
            ["OrderId", "Status", "Filled", "Remaining", "AvgFillPrice", "PermId", "ParentId", "LastFillPrice",
             "ClientId", "WhyHeld", "MktCapPrice"],
            [dtypes.int64, dtypes.string, dtypes.float64, dtypes.float64, dtypes.float64, dtypes.int64, dtypes.int64, dtypes.float64,
             dtypes.int64, dtypes.string, dtypes.float64])

        table_writers["orders_completed"] = TableWriter(
            [*logger_contract.names(), *logger_order.names(), *logger_order_state.names()],
            [*logger_contract.types(), *logger_order.types(), *logger_order_state.types()])

        table_writers["orders_exec_details"] = TableWriter(
            ["RequestId", *logger_contract.names(renames={"Exchange": "ContractExchange"}),
             *logger_execution.names(renames={"Exchange": "ExecutionExchange"})],
            [dtypes.int64, *logger_contract.types(), *logger_execution.types()])

        table_writers["orders_exec_commission_report"] = TableWriter(
            [*logger_commission_report.names()],
            [*logger_commission_report.types()])

        ####
        # End
        ####

        return table_writers

    ####################################################################################################################
    ####################################################################################################################
    ## Connect / Disconnect / Subscribe
    ####################################################################################################################
    ####################################################################################################################

    def connect(self, host: str, port: int, client_id: int) -> None:
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

        if self.isConnected():
            raise Exception("IbTwsClient is already connected.")

        self.contract_registry = ContractRegistry(self)
        self.order_id_queue = OrderIdEventQueue(self, strategy=self._order_id_strategy)
        self._registered_market_rules = set()
        self._realtime_bar_sizes = {}
        self.news_providers = []
        self._accounts_managed = set()

        EClient.connect(self, host, port, client_id)

        # wait for the client to connect to avoid a race condition (https://github.com/deephaven-examples/deephaven-ib/issues/12)
        time.sleep(1)

        self._thread = Thread(name="IbTwsClient", target=self.run)
        self._thread.start()
        setattr(self, "ib_thread", self._thread)

        # wait for the client to connect to avoid a race condition (https://github.com/deephaven-examples/deephaven-ib/issues/12)
        time.sleep(1)

        self._subscribe()

        # wait for the client to connect to avoid a race condition (https://github.com/deephaven-examples/deephaven-ib/issues/12)
        time.sleep(1)

    def disconnect(self) -> None:
        """Disconnect from an IB TWS session.

        Returns:
            None
        """

        EClient.disconnect(self)
        self._thread = None
        self.contract_registry = None
        self.order_id_queue = None
        self._registered_market_rules = None
        self._realtime_bar_sizes = None
        self.news_providers = None
        self._accounts_managed = None

    def __del__(self):
        self.disconnect()

    def _subscribe(self) -> None:
        """Subscribe to IB data."""

        self.reqFamilyCodes()

        if self._is_fa:
            self.requestFA(1)  # request GROUPS.  See FaDataTypeEnum.
            #TODO: see https://github.com/deephaven-examples/deephaven-ib/issues/32
            #TODO: see https://github.com/deephaven-examples/deephaven-ib/issues/5
            # self.requestFA(2)  # request PROFILE.  See FaDataTypeEnum.
            self.requestFA(3)  # request ACCOUNT ALIASES.  See FaDataTypeEnum.

            self.request_account_pnl("All")

        self.request_account_summary("All")
        self.request_account_overview("All")
        self.request_account_positions("All")
        self.reqManagedAccts()
        self.reqNewsBulletins(allMsgs=True)
        self.request_executions()
        self.reqNewsProviders()

        if not self._read_only:
            self.reqCompletedOrders(apiOnly=False)
            # Just subscribe to orders from the current client id.
            # When subscribing to all clients, data from other clients does not update.
            self.reqOpenOrders()

    ####################################################################################################################
    ####################################################################################################################
    ## General
    ####################################################################################################################
    ####################################################################################################################

    def log_request(self, req_id: int, request_type: str, contract: Optional[Contract],
                    notes: Optional[Dict[str, Any]]):
        """Log a data request."""

        if notes is None:
            note_string = None
        else:
            note_string = json.dumps(dict({k: str(v) for (k, v) in notes.items()}.items()))

        self._table_writers["requests"].write_row([req_id, request_type, *logger_contract.vals(contract), note_string])

    ####
    # Always present
    ####

    def error(self, reqId: TickerId, errorCode: int, errorString: str, advancedOrderRejectJson: str = ""):
        EWrapper.error(self, reqId, errorCode, errorString, advancedOrderRejectJson)

        if reqId == 2147483647:
            reqId = None

        if errorCode not in _error_code_message_map:
            msg = f"Unmapped error code.  Please file an issue at https://github.com/deephaven-examples/deephaven-ib/issues:\n\terrorCode='{errorCode}'\n\terrorString='{errorString}'\n\tThis only impacts the error message you see and will not impact the execution of your program."
            logging.error(msg)
            _error_code_message_map[errorCode] = errorString
            _error_code_note_map[errorCode] = ""

        self._table_writers["errors"].write_row(
            [reqId, errorCode, map_values(errorCode, _error_code_message_map), errorString,
             map_values(errorCode, _error_code_note_map)])

        # error may get called after disconnect, so need to avoid cases where contract_registry is None
        if self.isConnected():
            self.contract_registry.add_error_data(req_id=reqId, error_string=errorString)

    ####################################################################################################################
    ####################################################################################################################
    ## Contracts
    ####################################################################################################################
    ####################################################################################################################

    def request_market_rules(self, contractDetails: ContractDetails):
        """Request price increment market quoting rules, if they have not yet been retrieved."""

        for market_rule in contractDetails.marketRuleIds.split(","):
            if market_rule not in self._registered_market_rules:
                self.reqMarketRule(marketRuleId=int(market_rule))

    ####
    # reqContractDetails
    ####

    def contractDetails(self, reqId: int, contractDetails: ContractDetails):
        EWrapper.contractDetails(self, reqId, contractDetails)
        self._table_writers["contracts_details"].write_row([reqId, *logger_contract_details.vals(contractDetails)])
        self.contract_registry.add_contract_data(reqId, contractDetails)
        self.request_market_rules(contractDetails)

    def bondContractDetails(self, reqId: int, contractDetails: ContractDetails):
        EWrapper.bondContractDetails(self, reqId, contractDetails)
        self._table_writers["contracts_details"].write_row([reqId, *logger_contract_details.vals(contractDetails)])
        self.contract_registry.add_contract_data(reqId, contractDetails)
        self.request_market_rules(contractDetails)

    def contractDetailsEnd(self, reqId: int):
        EWrapper.contractDetailsEnd(self, reqId)
        self.contract_registry.request_end(reqId)

    ####
    # reqMatchingSymbols
    ####

    def symbolSamples(self, reqId: int, contractDescriptions: ListOfContractDescription):
        EWrapper.symbolSamples(self, reqId, contractDescriptions)

        for cd in contractDescriptions:
            self._table_writers["contracts_matching"].write_row([reqId, *logger_contract.vals(cd.contract),
                                                                 to_string_set(cd.derivativeSecTypes)])

            # Negative contract IDs seem to be for malformed contracts that yield errors when requesting details
            if cd.contract.conId >= 0:
                self.contract_registry.request_contract_details_nonblocking(cd.contract)

    ####
    # reqMarketRule
    ####

    def marketRule(self, marketRuleId: int, priceIncrements: ListOfPriceIncrements):
        EWrapper.marketRule(self, marketRuleId, priceIncrements)

        for pi in priceIncrements:
            self._table_writers["market_rules"].write_row([str(marketRuleId), *logger_price_increment.vals(pi)])

        self._registered_market_rules.add(str(marketRuleId))

    ####################################################################################################################
    ####################################################################################################################
    ## Accounts
    ####################################################################################################################
    ####################################################################################################################

    def request_account_summary(self, group_name: str) -> None:
        """Request account summary data for an account group."""

        account_summary_tags = [
            "accountountType",
            "NetLiquidation",
            "TotalCashValue",
            "SettledCash",
            "TotalCashValue",
            "AccruedCash",
            "BuyingPower",
            "EquityWithLoanValue",
            "PreviousDayEquityWithLoanValue",
            "GrossPositionValue",
            "RegTEquity",
            "RegTMargin",
            "SMA",
            "InitMarginReq",
            "MaintMarginReq",
            "AvailableFunds",
            "ExcessLiquidity",
            "Cushion",
            "FullInitMarginReq",
            "FullMaintMarginReq",
            "FullAvailableFunds",
            "FullExcessLiquidity",
            "LookAheadNextChange",
            "LookAheadInitMarginReq",
            "LookAheadMaintMarginReq",
            "LookAheadAvailableFunds",
            "LookAheadExcessLiquidity",
            "HighestSeverity",
            "DayTradesRemaining",
            "Leverage",
            "$LEDGER",
        ]

        req_id = self.request_id_manager.next_id()
        tags = ",".join(account_summary_tags)
        self.log_request(req_id, "AccountSummary", None, {"groupName": group_name, "tags": tags})
        self.reqAccountSummary(reqId=req_id, groupName=group_name, tags=tags)

    def request_account_pnl(self, account: str, model_code: str = "") -> int:
        """Request PNL updates.  Results are returned in the `accounts_pnl` table.

        Args:
            account (str): Account to request PNL for.  "All" requests for all accounts.
            model_code (str): Model portfolio code to request PNL for.

        Returns:
            Request ID

        Raises:
              Exception
        """

        req_id = self.request_id_manager.next_id()
        self.log_request(req_id, "Pnl", None, {"account": account, "model_code": model_code})
        self.reqPnL(reqId=req_id, account=account, modelCode=model_code)
        return req_id

    def request_account_overview(self, account: str, model_code: str = "") -> int:
        """Request portfolio overview updates.  Results are returned in the `accounts_overview` table.

        Args:
            account (str): Account to request an overview for.  "All" requests for all accounts.
            model_code (str): Model portfolio code to request an overview for.

        Returns:
            Request ID

        Raises:
              Exception
        """
        req_id = self.request_id_manager.next_id()
        self.log_request(req_id, "AccountOverview", None, {"account": account, "model_code": model_code})
        self.reqAccountUpdatesMulti(reqId=req_id, account=account, modelCode=model_code, ledgerAndNLV=False)
        return req_id

    def request_account_positions(self, account: str, model_code: str = "") -> int:
        """Request portfolio position updates.  Results are returned in the `accounts_positions` table.

        Args:
            account (str): Account to request positions for.  "All" requests for all accounts.
            model_code (str): Model portfolio code to request positions for.

        Returns:
            Request ID

        Raises:
              Exception
        """
        req_id = self.request_id_manager.next_id()
        self.log_request(req_id, "AccountPositions", None, {"account": account, "model_code": model_code})
        self.reqPositionsMulti(reqId=req_id, account=account, modelCode=model_code)
        return req_id


    ####
    # reqManagedAccts
    ####

    def managedAccounts(self, accountsList: str):
        EWrapper.managedAccounts(self, accountsList)

        for account in accountsList.split(","):
            if account and account not in self._accounts_managed:
                self._accounts_managed.add(account)
                self._table_writers["accounts_managed"].write_row([account])
                self.request_account_pnl(account)
                self.request_account_overview(account)
                self.request_account_positions(account)

    ####
    # reqFamilyCodes
    ####

    def familyCodes(self, familyCodes: ListOfFamilyCode):
        EWrapper.familyCodes(self, familyCodes)

        for fc in familyCodes:
            self._table_writers["accounts_family_codes"].write_row(logger_family_code.vals(fc))

    ####
    # requestFA
    ####

    def receiveFA(self, faData: FaDataType, cxml: str):
        EWrapper.receiveFA(self, faData, cxml)

        fa_data_type = FaDataTypeEnum.to_str(faData)
        logging.debug(f"RECEIVEFA XML: {faData} {fa_data_type} {cxml}")

        xml_tree = ET.fromstring(cxml)

        if fa_data_type == "GROUPS":
            if xml_tree.tag != "ListOfGroups":
                raise Exception(f"Unexpected XML tag: {xml_tree.tag} != ListOfGroups")

            for group in xml_tree.findall("Group"):
                name = group.find("name").text
                accounts = group.find("ListOfAccts")
                default_method = group.find("defaultMethod").text

                for account in accounts.findall("Account"):
                    account = account.find("acct").text
                    self._table_writers["accounts_groups"].write_row([name, default_method, account])

                self.request_account_summary(name)

        elif fa_data_type == "PROFILES":
            if xml_tree.tag != "ListOfAllocationProfiles":
                raise Exception(f"Unexpected XML tag: {xml_tree.tag} != ListOfAllocationProfiles")

            for profile in xml_tree.findall("AllocationProfile"):
                name = profile.find("name").text
                ap_type = profile.find("type").text
                allocations = profile["ListOfAllocations"]

                for allocation in allocations.findall("Allocation"):
                    acct = allocation.find("acct").text
                    amount = allocation.find("amount").text
                    type_names = {1: "Percentages", 2: "Financial Ratios", 3: "Shares"}
                    self._table_writers["accounts_allocation_profiles"].write_row(
                        [name, map_values(ap_type, type_names), acct, float(amount)])

        elif fa_data_type == "ALIASES":
            if xml_tree.tag != "ListOfAccountAliases":
                raise Exception(f"Unexpected XML tag: {xml_tree.tag} != ListOfAccountAliases")

            for alias in xml_tree.findall("AccountAlias"):
                account = alias.find("account").text
                account_alias = alias.find("alias").text
                self._table_writers["accounts_aliases"].write_row([account, account_alias])

        else:
            logging.error(f"RECEIVEFA unknown data type: {faData} {fa_data_type} {cxml}")

    ####
    # reqAccountUpdates
    ####

    # NOT NEEDED. reqAccountUpdatesMulti is used instead.

    ####
    # reqAccountUpdatesMulti
    ####

    def accountUpdateMulti(self, reqId: int, account: str, modelCode: str, key: str, value: str, currency: str):
        EWrapper.accountUpdateMulti(self, reqId, account, modelCode, key, value, currency)
        self._table_writers["accounts_overview"].write_row([reqId, account, modelCode, currency, key, value])

    def accountUpdateMultiEnd(self, reqId: int):
        # do not need to implement
        EWrapper.accountUpdateMultiEnd(self, reqId)

    ####
    # reqAccountSummary
    ####

    def accountSummary(self, reqId: int, account: str, tag: str, value: str, currency: str):
        EWrapper.accountSummary(self, reqId, account, tag, value, currency)
        self._table_writers["accounts_summary"].write_row([reqId, account, tag, value, currency])

    ####
    # reqPositions
    ####

    # NOT NEEDED. reqAccountUpdatesMulti is used instead.

    ####
    # reqPositionsMulti
    ####

    def positionMulti(self, reqId: int, account: str, modelCode: str, contract: Contract, pos: decimal.Decimal, avgCost: float):
        EWrapper.positionMulti(self, reqId, account, modelCode, contract, pos, avgCost)

        # The returned contract seems to be inconsistent with IB's API to request contract details.
        # This hack is to work around the problem.
        # See https://github.com/deephaven-examples/deephaven-ib/issues/33
        
        if contract.secType == "STK":
            contract.exchange = "SMART"

        self._table_writers["accounts_positions"].write_row(
            [reqId, account, modelCode, *logger_contract.vals(contract), pos, avgCost])

        self.contract_registry.request_contract_details_nonblocking(contract)

    def positionMultiEnd(self, reqId: int):
        # do not need to implement
        EWrapper.positionMultiEnd(self, reqId)

    ####
    # reqPnL
    ####

    def pnl(self, reqId: int, dailyPnL: float, unrealizedPnL: float, realizedPnL: float):
        EWrapper.pnl(self, reqId, dailyPnL, unrealizedPnL, realizedPnL)
        self._table_writers["accounts_pnl"].write_row([reqId, dailyPnL, unrealizedPnL, realizedPnL])

    ####################################################################################################################
    ####################################################################################################################
    ## News
    ####################################################################################################################
    ####################################################################################################################

    ####
    # reqNewsProviders
    ####

    def newsProviders(self, newsProviders: ListOfNewsProviders):
        EWrapper.newsProviders(self, newsProviders)

        for provider in newsProviders:
            self._table_writers["news_providers"].write_row(logger_news_provider.vals(provider))
            self.news_providers.append(provider.code)

    ####
    # reqNewsBulletins
    ####

    def updateNewsBulletin(self, msgId: int, msgType: int, newsMessage: str, originExch: str):
        EWrapper.updateNewsBulletin(self, msgId, msgType, newsMessage, originExch)
        self._table_writers["news_bulletins"].write_row([msgId, map_values(msgType, _news_msgtype_map), newsMessage,
                                                         originExch])

    ####
    # reqNewsArticle
    ####

    def newsArticle(self, requestId: int, articleType: int, articleText: str):
        EWrapper.newsArticle(self, requestId, articleType, articleText)
        at = map_values(articleType, {0: "PlainTextOrHtml", 1: "BinaryDataOrPdf"})
        self._table_writers["news_articles"].write_row([requestId, at, html.unescape(articleText)])

    ####
    # reqHistoricalNews
    ####

    def historicalNews(self, requestId: int, timestamp: str, providerCode: str, articleId: str, headline: str):
        EWrapper.historicalNews(self, requestId, timestamp, providerCode, articleId, headline)

        h = headline.split("}", 1)

        if len(h) == 1:
            headline_clean = h[0]
        else:
            headline_clean = h[1]

        self._table_writers["news_historical"].write_row(
            [requestId, ib_to_j_instant(timestamp), providerCode, articleId,
             headline_clean])

    def historicalNewsEnd(self, requestId: int, hasMore: bool):
        # do not need to implement
        EWrapper.historicalNewsEnd(self, requestId, hasMore)

    ####################################################################################################################
    ####################################################################################################################
    ## Market Data
    ####################################################################################################################
    ####################################################################################################################

    ####
    # reqMktData
    ####

    def tickPrice(self, reqId: TickerId, tickType: TickType, price: float, attrib: TickAttrib):
        EWrapper.tickPrice(self, reqId, tickType, price, attrib)

        if price == 0.0:
            price = None

        self._table_writers["ticks_price"].write_row([reqId, TickTypeEnum.to_str(tickType), price,
                                                      *logger_tick_attrib.vals(attrib)])

    def tickSize(self, reqId: TickerId, tickType: TickType, size: decimal.Decimal):
        EWrapper.tickSize(self, reqId, tickType, size)
        self._table_writers["ticks_size"].write_row([reqId, TickTypeEnum.to_str(tickType), size])

    def tickString(self, reqId: TickerId, tickType: TickType, value: str):
        EWrapper.tickString(self, reqId, tickType, value)
        self._table_writers["ticks_string"].write_row([reqId, TickTypeEnum.to_str(tickType), value])

    def tickEFP(self, reqId: TickerId, tickType: TickType, basisPoints: float,
                formattedBasisPoints: str, totalDividends: float,
                holdDays: int, futureLastTradeDate: str, dividendImpact: float,
                dividendsToLastTradeDate: float):
        EWrapper.tickEFP(self, reqId, tickType, basisPoints, formattedBasisPoints, totalDividends, holdDays,
                         futureLastTradeDate, dividendImpact, dividendsToLastTradeDate)
        self._table_writers["ticks_efp"].write_row(
            [reqId, TickTypeEnum.to_str(tickType), basisPoints, formattedBasisPoints,
             totalDividends, holdDays, futureLastTradeDate, dividendImpact,
             dividendsToLastTradeDate])

    def tickGeneric(self, reqId: TickerId, tickType: TickType, value: float):
        EWrapper.tickGeneric(self, reqId, tickType, value)
        self._table_writers["ticks_generic"].write_row([reqId, TickTypeEnum.to_str(tickType), value])

    def tickOptionComputation(self, reqId: TickerId, tickType: TickType, tickAttrib: int,
                              impliedVol: float, delta: float, optPrice: float, pvDividend: float,
                              gamma: float, vega: float, theta: float, undPrice: float):
        EWrapper.tickOptionComputation(self, reqId, tickType, tickAttrib, impliedVol, delta, optPrice, pvDividend,
                                       gamma, vega, theta, undPrice)
        ta = map_values(tickAttrib, {0: "Return-based", 1: "Price-based"})
        self._table_writers["ticks_option_computation"].write_row([reqId, TickTypeEnum.to_str(tickType), ta, impliedVol,
                                                                   delta,
                                                                   optPrice, pvDividend, gamma, vega, theta, undPrice])

    def tickSnapshotEnd(self, reqId: int):
        # do not ned to implement
        EWrapper.tickSnapshotEnd(self, reqId)

    ####
    # reqTickByTickData and reqHistoricalTicks
    ####

    def tickByTickAllLast(self, reqId: int, tickType: int, timestamp: int, price: float,
                          size: decimal.Decimal, tickAttribLast: TickAttribLast, exchange: str,
                          specialConditions: str):
        EWrapper.tickByTickAllLast(self, reqId, tickType, timestamp, price, size, tickAttribLast, exchange,
                                   specialConditions)

        t = HistoricalTickLast()
        t.time = timestamp
        t.tickAttribLast = tickAttribLast
        t.price = price
        t.size = size
        t.exchange = exchange
        t.specialConditions = specialConditions

        self._table_writers["ticks_trade"].write_row([reqId, *logger_hist_tick_last.vals(t)])

    # noinspection PyUnusedLocal
    def historicalTicksLast(self, reqId: int, ticks: ListOfHistoricalTickLast, done: bool):
        EWrapper.historicalTicksLast(self, reqId, ticks, done)

        for t in ticks:
            self._table_writers["ticks_trade"].write_row([reqId, *logger_hist_tick_last.vals(t)])

    def tickByTickBidAsk(self, reqId: int, timestamp: int, bidPrice: float, askPrice: float,
                         bidSize: decimal.Decimal, askSize: decimal.Decimal, tickAttribBidAsk: TickAttribBidAsk):
        EWrapper.tickByTickBidAsk(self, reqId, timestamp, bidPrice, askPrice, bidSize, askSize, tickAttribBidAsk)

        t = HistoricalTickBidAsk()
        t.time = timestamp
        t.tickAttribBidAsk = tickAttribBidAsk
        t.priceBid = bidPrice
        t.priceAsk = askPrice
        t.sizeBid = bidSize
        t.sizeAsk = askSize

        self._table_writers["ticks_bid_ask"].write_row([reqId, *logger_hist_tick_bid_ask.vals(t)])

    def historicalTicksBidAsk(self, reqId: int, ticks: ListOfHistoricalTickBidAsk, done: bool):

        for t in ticks:
            self._table_writers["ticks_bid_ask"].write_row([reqId, *logger_hist_tick_bid_ask.vals(t)])

    def tickByTickMidPoint(self, reqId: int, timestamp: int, midPoint: float):
        EWrapper.tickByTickMidPoint(self, reqId, timestamp, midPoint)
        self._table_writers["ticks_mid_point"].write_row([reqId, unix_sec_to_j_instant(timestamp), midPoint])

    def historicalTicks(self, reqId: int, ticks: ListOfHistoricalTick, done: bool):
        EWrapper.historicalTicks(self, reqId, ticks, done)

        for t in ticks:
            self._table_writers["ticks_mid_point"].write_row([reqId, unix_sec_to_j_instant(t.time), t.price])

    ####
    # reqHistoricalData
    ####

    def historicalData(self, reqId: int, bar: BarData):
        EWrapper.historicalData(self, reqId, bar)
        self._table_writers["bars_historical"].write_row([reqId, *logger_bar_data.vals(bar)])

    def historicalDataEnd(self, reqId: int, start: str, end: str):
        # do not ned to implement
        EWrapper.historicalDataEnd(self, reqId, start, end)

    def historicalDataUpdate(self, reqId: int, bar: BarData):
        EWrapper.historicalDataUpdate(self, reqId, bar)
        self._table_writers["bars_historical"].write_row([reqId, *logger_bar_data.vals(bar)])

    ####
    # reqRealTimeBars
    ####

    def reqRealTimeBars(self, reqId: TickerId, contract: Contract, barSize: int,
                        whatToShow: str, useRTH: bool,
                        realTimeBarsOptions: TagValueList):
        self._realtime_bar_sizes[reqId] = barSize
        EClient.reqRealTimeBars(self, reqId, contract, barSize, whatToShow, useRTH, realTimeBarsOptions)

    def realtimeBar(self, reqId: TickerId, timestamp: int, open_: float, high: float, low: float, close: float,
                    volume: decimal.Decimal, wap: decimal.Decimal, count: int):
        EWrapper.realtimeBar(self, reqId, timestamp, open_, high, low, close, volume, wap, count)
        bar_size = self._realtime_bar_sizes[reqId]
        bar = RealTimeBar(time=timestamp, endTime=timestamp + bar_size, open_=open_, high=high, low=low, close=close,
                          volume=volume,
                          wap=wap, count=count)
        self._table_writers["bars_realtime"].write_row([reqId, *logger_real_time_bar_data.vals(bar)])

    ####################################################################################################################
    ####################################################################################################################
    ## Order Management System (OMS)
    ####################################################################################################################
    ####################################################################################################################

    def next_order_id(self) -> int:
        """Gets the next valid order ID."""
        return self.request_id_manager.next_order_id(self.order_id_queue)

    def request_executions(self) -> None:
        """Requests executions."""
        req_id = self.request_id_manager.next_id()
        self.log_request(req_id, "Executions", None, None)
        self.reqExecutions(reqId=req_id, execFilter=ExecutionFilter())


    ####
    # reqIds
    ####

    def nextValidId(self, orderId: int):
        EWrapper.nextValidId(self, orderId)
        self.order_id_queue.add_value(orderId)

    ####
    # reqAllOpenOrders / reqOpenOrders
    ####

    def openOrder(self, orderId: OrderId, contract: Contract, order: Order, orderState: OrderState):
        EWrapper.openOrder(self, orderId, contract, order, orderState)

        if orderId != order.orderId:
            raise Exception("Order IDs do not match")

        self._table_writers["orders_submitted"].write_row(
            [*logger_contract.vals(contract), *logger_order.vals(order), *logger_order_state.vals(orderState)])
        self.contract_registry.request_contract_details_nonblocking(contract)

    def orderStatus(self, orderId: OrderId, status: str, filled: decimal.Decimal,
                    remaining: decimal.Decimal, avgFillPrice: float, permId: int,
                    parentId: int, lastFillPrice: float, clientId: int,
                    whyHeld: str, mktCapPrice: float):
        EWrapper.orderStatus(self, orderId, status, filled, remaining, avgFillPrice, permId, parentId, lastFillPrice,
                             clientId, whyHeld, mktCapPrice)
        self._table_writers["orders_status"].write_row(
            [orderId, status, filled, remaining, avgFillPrice, permId, parentId,
             lastFillPrice, clientId, whyHeld, mktCapPrice])

    def openOrderEnd(self):
        # do not ned to implement
        EWrapper.openOrderEnd(self)

    ####
    # reqCompletedOrders
    ####

    def completedOrder(self, contract: Contract, order: Order, orderState: OrderState):
        EWrapper.completedOrder(self, contract, order, orderState)
        self._table_writers["orders_completed"].write_row([*logger_contract.vals(contract), *logger_order.vals(order),
                                                           *logger_order_state.vals(orderState)])
        self.contract_registry.request_contract_details_nonblocking(contract)

    def completedOrdersEnd(self):
        # do not ned to implement
        EWrapper.completedOrdersEnd(self)

    ####
    # reqExecutions
    ####

    def execDetails(self, reqId: int, contract: Contract, execution: Execution):
        EWrapper.execDetails(self, reqId, contract, execution)
        self._table_writers["orders_exec_details"].write_row([reqId, *logger_contract.vals(contract),
                                                              *logger_execution.vals(execution)])
        self.contract_registry.request_contract_details_nonblocking(contract)

    def execDetailsEnd(self, reqId: int):
        # do not need to implement
        EWrapper.execDetailsEnd(self, reqId)

    def commissionReport(self, commissionReport: CommissionReport):
        EWrapper.commissionReport(self, commissionReport)
        self._table_writers["orders_exec_commission_report"].write_row(logger_commission_report.vals(commissionReport))

    ####################################################################################################################
    ####################################################################################################################
    ## End
    ####################################################################################################################
    ####################################################################################################################
