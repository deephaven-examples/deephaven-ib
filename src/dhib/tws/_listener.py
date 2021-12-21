import logging
from typing import Dict

# noinspection PyPep8Naming
from deephaven import DynamicTableWriter, Types as dht
from ibapi import errors
from ibapi import news
from ibapi.commission_report import CommissionReport
from ibapi.common import ListOfNewsProviders, OrderId, TickerId, TickAttrib, BarData, TickAttribLast, \
    ListOfHistoricalTickLast, TickAttribBidAsk, ListOfHistoricalTickBidAsk, ListOfHistoricalTick, HistoricalTickBidAsk, \
    HistoricalTickLast, ListOfFamilyCode, ListOfContractDescription, ListOfPriceIncrements
from ibapi.contract import Contract, ContractDetails
from ibapi.execution import Execution, ExecutionFilter
from ibapi.order import Order
from ibapi.order_state import OrderState
from ibapi.ticktype import TickType, TickTypeEnum
from ibapi.wrapper import EWrapper

from ._client import IbClient
from ._ibtypelogger import *
from ..utils import next_unique_id, unix_sec_to_dh_datetime

logging.basicConfig(level=logging.DEBUG)

_error_code_map = {e.code(): e.msg() for e in dir(errors) if isinstance(e, errors.CodeMsgPair)}


# TODO: map string "" to None
# TODO: parse time strings

# TODO: no users need to see this
# noinspection PyPep8Naming
class _IbListener(EWrapper):
    """Listener for data from IB."""

    def __init__(self):
        EWrapper.__init__(self)
        self._client = None
        self._registered_contracts = None
        self._table_writers = _IbListener._build_table_writers()

    @staticmethod
    def _build_table_writers() -> Dict[str,Any]:
        table_writers = {}

        # General

        table_writers["error"] = DynamicTableWriter(
            ["RequestId", "ErrorCode", "ErrorDescription", "Error"],
            [dht.int64, dht.int64, dht.string, dht.string])

        # Contracts

        table_writers["contract_details"] = DynamicTableWriter(
            ["RequestId", *logger_contract_details.names()],
            [dht.int64, *logger_contract_details.types()])

        #TODO: rename
        table_writers["matching_symbols"] = DynamicTableWriter(
            ["RequestId", *logger_contract.names(), "DerivativeSecTypes"],
            [dht.int64, *logger_contract.types(), dht.string])

        table_writers["price_increment"] = DynamicTableWriter(
            ["MarketRuleId", *logger_price_increment.names()],
            [dht.int64, *logger_price_increment.types()])

        # Accounts

        table_writers["managed_accounts"] = DynamicTableWriter(["Account"], [dht.string])

        table_writers["family_codes"] = DynamicTableWriter(
            [*logger_family_code.names()],
            [*logger_family_code.types()])

        table_writers["account_value"] = DynamicTableWriter(["Account", "Currency", "Key", "Value"],
                                                [dht.string, dht.string, dht.string, dht.string])

        table_writers["portfolio"] = DynamicTableWriter(
            ["Account", *logger_contract.names(), "Position", "MarketPrice", "MarketValue", "AvgCost",
             "UnrealizedPnl", "RealizedPnl"],
            [dht.string, *logger_contract.types(), dht.float64, dht.float64, dht.float64, dht.float64,
             dht.float64, dht.float64])

        table_writers["account_summary"] = DynamicTableWriter(["ReqId", "Account", "Tag", "Value", "Currency"],
                                                  [dht.int64, dht.string, dht.string, dht.string, dht.string])

        table_writers["positions"] = DynamicTableWriter(["Account", *logger_contract.names(), "Position", "AvgCost"],
                                            [dht.string, *logger_contract.types(), dht.float64, dht.float64])

        table_writers["pnl"] = DynamicTableWriter(
            ["RequestId", "DailyPnl", "UnrealizedPnl", "RealizedPnl"],
            [dht.int64, dht.float64, dht.float64, "RealizedPnl"])

        # News

        table_writers["news_providers"] = DynamicTableWriter(["Provider"], [dht.string])


        table_writers["news_bulletins"] = DynamicTableWriter(["MsgId", "MsgType", "Message", "OriginExch"],
                                                 [dht.int64, dht.string, dht.string, dht.string])

        table_writers["news_article"] = DynamicTableWriter(
            ["RequestId", "ArticleType", "ArticleText"],
            [dht.int64, dht.string, dht.string])

        table_writers["news_historical"] = DynamicTableWriter(
            ["RequestId", "Time", "ProviderCode", "ArticleId", "Headline"],
            [dht.int64, dht.string, dht.string, dht.string, dht.string])

        # Market Data

        #?????






        self.exec_details = DynamicTableWriter(["ReqId", "Time", "Account", *logger_contract.names(),
                                                "Exchange", "Side", "Shares", "Price",
                                                "CumQty", "AvgPrice", "Liquidation",
                                                "EvRule", "EvMultiplier", "ModelCode", "LastLiquidity"
                                                                                       "ExecId", "PermId", "ClientId",
                                                "OrderId", "OrderRef"],
                                               [dht.int64, dht.string, dht.string, *logger_contract.types(),
                                                dht.string, dht.string, dht.float64, dht.float64,
                                                dht.float64, dht.float64, dht.int64,
                                                dht.string, dht.float64, dht.string, dht.int64,
                                                dht.string, dht.int64, dht.int64, dht.int64, dht.string])

        self.commission_report = DynamicTableWriter(
            ["ExecId", "Currency", "Commission", "RealizedPnl", "Yield", "YieldRedemptionDate"],
            [dht.string, dht.string, dht.float64, dht.float64, dht.float64, dht.int64])


        self.orders_completed = DynamicTableWriter(
            [*logger_contract.names(), *logger_order.names(), *logger_order_state.names()],
            [*logger_contract.types(), *logger_order.types(), *logger_order_state.types()])

        self.orders_status = DynamicTableWriter(
            ["OrderId", "Status", "Filled", "Remaining", "AvgFillPrice", "PermId", "ParentId", "LastFillPrice",
             "ClientId", "WhyHeld", "MktCapPrice"],
            [dht.int64, dht.string, dht.float64, dht.float64, dht.float64, dht.int64, dht.int64, dht.float64, dht.int64,
             dht.string, dht.float64])

        self.orders_open = DynamicTableWriter(
            ["OrderId", *logger_contract.names(), *logger_order.names(), *logger_order_state.names()],
            [dht.int64, *logger_contract.types(), *logger_order.types(), *logger_order_state.types()])


        self.tick_price = DynamicTableWriter(
            ["RequestId", "TickType", "Price", *logger_tick_attrib.names()],
            [dht.int64, dht.string, dht.float64, *logger_tick_attrib.types()])

        self.tick_size = DynamicTableWriter(
            ["RequestId", "TickType", "Size"],
            [dht.int64, dht.string, dht.int64])

        self.tick_string = DynamicTableWriter(
            ["RequestId", "TickType", "Value"],
            [dht.int64, dht.string, dht.string])

        # exchange for physical
        self.tick_efp = DynamicTableWriter(
            ["RequestId", "TickType", "BasisPoints", "FormattedBasisPoints", "TotalDividends", "HoldDays",
             "FutureLastTradeDate", "DividendImpact", "DividendsToLastTradeDate"],
            [dht.int64, dht.string, dht.float64, dht.string, dht.float64, dht.int64, dht.string, dht.float64,
             dht.float64])

        self.tick_generic = DynamicTableWriter(
            ["RequestId", "TickType", "Value"],
            [dht.int64, dht.string, dht.float64])

        self.tick_option_computation = DynamicTableWriter(
            ["RequestId", "TickType", "TickAttrib", "ImpliedVol", "Delta", "OptPrice", "PvDividend", "Gamma", "Vega",
             "Theta", "UndPrice"],
            [dht.int64, dht.string, dht.string, dht.float64, dht.float64, dht.float64, dht.float64, dht.float64,
             dht.float64, dht.float64, dht.float64])

        self.historical_data = DynamicTableWriter(
            ["RequestId", *logger_bar_data.names()],
            [dht.int64, *logger_bar_data.types()])

        self.realtime_bar = DynamicTableWriter(
            ["RequestId", "Timestamp", "Open", "High", "Low", "Close", "Volume", "WAP", "Count"],
            [dht.int64, dht.datetime, dht.float64, dht.float64, dht.float64, dht.float64, dht.int64, dht.float64,
             dht.int64])

        self.tick_last = DynamicTableWriter(
            ["RequestId", *logger_hist_tick_last.names()],
            [dht.int64, *logger_hist_tick_last.types()])

        self.tick_bid_ask = DynamicTableWriter(
            ["RequestId", *logger_hist_tick_bid_ask.names()],
            [dht.int64, *logger_hist_tick_bid_ask.types()])

        self.tick_mid_point = DynamicTableWriter(
            ["RequestId", "Timestamp", "MidPoint"],
            [dht.int64, dht.datetime, dht.float64])





        return table_writers


    def connect(self, client: IbClient):
        self._client = client
        self._registered_contracts = set()

        client.reqManagedAccts()

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

        client.reqAccountSummary(reqId=next_unique_id(), groupName="All", tags=",".join(account_summary_tags))
        client.reqPositions()
        client.reqNewsBulletins(allMsgs=True)
        client.reqExecutions(reqId=next_unique_id(), execFilter=ExecutionFilter())
        client.reqCompletedOrders(apiOnly=False)
        client.reqNewsProviders()
        client.reqAllOpenOrders()
        client.reqFamilyCodes()


    def disconnect(self):
        self._client = None

    def request_contract_details(self, contract: Contract):
        # TODO: Is checking to see if a contract is in the set sufficient to see if it has been registered?

        if contract not in self._registered_contracts:
            req_id = next_unique_id()
            self._client.reqContractDetails(reqId=req_id, contract=contract)

    ####################################################################################################################
    ####################################################################################################################
    ## General
    ####################################################################################################################
    ####################################################################################################################


    ####
    # Always present
    ####

    def error(self, reqId: TickerId, errorCode: int, errorString: str):
        EWrapper.error(self, reqId, errorCode, errorString)
        self._table_writers["error"].logRow(reqId, errorCode, map_values(errorCode, _error_code_map), errorString)

    ####################################################################################################################
    ####################################################################################################################
    ## Contracts
    ####################################################################################################################
    ####################################################################################################################

    ####
    # reqContractDetails
    ####

    def contractDetails(self, reqId: int, contractDetails: ContractDetails):
        EWrapper.contractDetails(self, reqId, contractDetails)
        self._table_writers["contract_details"].logRow(reqId, *logger_contract_details.vals(contractDetails))
        self._registered_contracts.add(contractDetails.contract)

    def bondContractDetails(self, reqId: int, contractDetails: ContractDetails):
        EWrapper.bondContractDetails(self, reqId, contractDetails)
        self._table_writers["contract_details"].logRow(reqId, *logger_contract_details.vals(contractDetails))
        self._registered_contracts.add(contractDetails.contract)

    def contractDetailsEnd(self, reqId: int):
        # do not ned to implement
        EWrapper.contractDetailsEnd(self, reqId)

    ####
    # reqMatchingSymbols
    ####

    def symbolSamples(self, reqId: int, contractDescriptions: ListOfContractDescription):
        EWrapper.symbolSamples(self, reqId, contractDescriptions)

        for cd in contractDescriptions:
            self._table_writers["matching_symbols"].logRow(reqId, *logger_contract.vals(cd.contract), to_string_set(cd.derivativeSecTypes))
            self.request_contract_details(cd.contract)

    ####
    # reqMarketRule
    ####

    def marketRule(self, marketRuleId: int, priceIncrements: ListOfPriceIncrements):
        EWrapper.marketRule(self, marketRuleId, priceIncrements)

        for pi in priceIncrements:
            self._table_writers["price_increment"].logRow(marketRuleId, *logger_price_increment.vals(pi))


    ####################################################################################################################
    ####################################################################################################################
    ## Accounts
    ####################################################################################################################
    ####################################################################################################################

    ####
    # reqManagedAccts
    ####

    def managedAccounts(self, accountsList: str):
        EWrapper.managedAccounts(self, accountsList)

        for account in accountsList.split(","):
            self._table_writers["managed_accounts"].logRow(account)
            self._client.reqAccountUpdates(subscribe=True, acctCode=account)

    ####
    # reqFamilyCodes
    ####

    def familyCodes(self, familyCodes: ListOfFamilyCode):
        EWrapper.familyCodes(self, familyCodes)

        for fc in familyCodes:
            self._table_writers["family_codes"].logRow(*logger_family_code.vals(fc))

    ####
    # reqAccountUpdates
    ####

    def updateAccountValue(self, key: str, val: str, currency: str, accountName: str):
        EWrapper.updateAccountValue(self, key, val, currency, accountName)
        self._table_writers["account_value"].logRow(accountName, currency, key, val)

    def updatePortfolio(self, contract: Contract, position: float,
                        marketPrice: float, marketValue: float,
                        averageCost: float, unrealizedPNL: float,
                        realizedPNL: float, accountName: str):
        EWrapper.updatePortfolio(self, contract, position, marketPrice, marketValue, averageCost, unrealizedPNL,
                                 realizedPNL, accountName)
        self._table_writers["portfolio"].logRow(accountName, *logger_contract.vals(contract), position, marketPrice, marketValue,
                              averageCost, unrealizedPNL, realizedPNL)
        self.request_contract_details(contract)

    ####
    # reqAccountSummary
    ####

    def accountSummary(self, reqId: int, account: str, tag: str, value: str, currency: str):
        EWrapper.accountSummary(self, reqId, account, tag, value, currency)
        self._table_writers["account_summary"].logRow(reqId, account, tag, value, currency)

    ####
    # reqPositions
    ####

    def position(self, account: str, contract: Contract, position: float, avgCost: float):
        EWrapper.position(self, account, contract, position, avgCost)
        self._table_writers["positions"].logRow(account, *logger_contract.vals(contract), position, avgCost)
        self.request_contract_details(contract)


    ####
    # reqPnL
    ####

    def pnl(self, reqId: int, dailyPnL: float, unrealizedPnL: float, realizedPnL: float):
        EWrapper.pnl(self, reqId, dailyPnL, unrealizedPnL, realizedPnL)
        self._table_writers["pnl"].logRow(reqId, dailyPnL, unrealizedPnL, realizedPnL)
        # TODO: need to be able to associate an account with the request id and data.

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
            self._table_writers["news_providers"].logRow(provider)


    ####
    # reqNewsBulletins
    ####

    def updateNewsBulletin(self, msgId: int, msgType: int, newsMessage: str, originExch: str):
        EWrapper.updateNewsBulletin(self, msgId, msgType, newsMessage, originExch)

        # TODO: Clean up with better mapping
        if msgType == news.NEWS_MSG:
            mtype = "NEWS"
        elif msgType == news.EXCHANGE_AVAIL_MSG:
            mtype = "EXCHANGE_AVAILABLE"
        elif msgType == news.EXCHANGE_UNAVAIL_MSG:
            mtype = "EXCHANGE_UNAVAILABLE"
        else:
            mtype = f"UNKNOWN({msgType})"

        self._table_writers["news_bulletins"].logRow(msgId, mtype, newsMessage, originExch)

    ####
    # reqNewsArticle
    ####

    def newsArticle(self, requestId: int, articleType: int, articleText: str):
        EWrapper.newsArticle(self, requestId, articleType, articleText)
        at = map_values(articleType, {0: "PlainTextOrHtml", 1: "BinaryDataOrPdf"})
        self._table_writers["news_article"].logRow(requestId, at, articleText)

    ####
    # reqHistoricalNews
    ####

    def historicalNews(self, requestId: int, time: str, providerCode: str, articleId: str, headline: str):
        EWrapper.historicalNews(self, requestId, time, providerCode, articleId, headline)
        self._table_writers["news_historical"].logRow(requestId, time, providerCode, articleId, headline)

    def historicalNewsEnd(self, requestId: int, hasMore: bool):
        # do not need to implement
        self.historicalNewsEnd(requestId, hasMore)


    ####################################################################################################################
    ####################################################################################################################
    ## Market Data
    ####################################################################################################################
    ####################################################################################################################

    


    #????







    ####
    # reqExecutions
    ####

    def execDetails(self, reqId: int, contract: Contract, execution: Execution):
        EWrapper.execDetails(self, reqId, contract, execution)
        self.exec_details.logRow(reqId, execution.time, execution.acctNumber, *logger_contract.vals(contract),
                                 execution.exchange, execution.side, execution.shares, execution.price,
                                 execution.cumQty, execution.avgPrice, execution.liquidation,
                                 execution.evRule, execution.evMultiplier, execution.modelCode, execution.lastLiquidity,
                                 execution.execId, execution.permId, execution.clientId, execution.orderId,
                                 execution.orderRef)
        self.request_contract_details(contract)

    def execDetailsEnd(self, reqId: int):
        # do not need to implement
        EWrapper.execDetailsEnd(self, reqId)

    def commissionReport(self, commissionReport: CommissionReport):
        EWrapper.commissionReport(self, commissionReport)
        self.commission_report.logRow(commissionReport.execId, commissionReport.currency, commissionReport.commission,
                                      commissionReport.realizedPNL, commissionReport.yield_,
                                      commissionReport.yieldRedemptionDate)

    ####
    # reqCompletedOrders
    ####

    def completedOrder(self, contract: Contract, order: Order, orderState: OrderState):
        EWrapper.completedOrder(self, contract, order, orderState)
        self.orders_completed.logRow(*logger_contract.vals(contract), *logger_order.vals(order),
                                     *logger_order_state.vals(orderState))
        self.request_contract_details(contract)

    def completedOrdersEnd(self):
        # do not ned to implement
        EWrapper.completedOrdersEnd(self)

    ####
    # reqAllOpenOrders
    ####

    def orderStatus(self, orderId: OrderId, status: str, filled: float,
                    remaining: float, avgFillPrice: float, permId: int,
                    parentId: int, lastFillPrice: float, clientId: int,
                    whyHeld: str, mktCapPrice: float):
        EWrapper.orderStatus(self, orderId, status, filled, remaining, avgFillPrice, permId, parentId, lastFillPrice,
                             clientId, whyHeld, mktCapPrice)
        self.orders_status.logRow(orderId, status, filled, remaining, avgFillPrice, permId, parentId, lastFillPrice,
                                  clientId, whyHeld, mktCapPrice)

    def openOrder(self, orderId: OrderId, contract: Contract, order: Order, orderState: OrderState):
        EWrapper.openOrder(self, orderId, contract, order, orderState)
        self.orders_open.logRow(orderId, *logger_contract.vals(contract), *logger_order.vals(order),
                                *logger_order_state.vals(orderState))
        self.request_contract_details(contract)

    def openOrderEnd(self):
        # do not ned to implement
        EWrapper.openOrderEnd(self)

    ####
    # reqMktData
    ####

    def tickPrice(self, reqId: TickerId, tickType: TickType, price: float, attrib: TickAttrib):
        EWrapper.tickPrice(self, reqId, tickType, price, attrib)

        self.tick_price.logRow(reqId, TickTypeEnum(tickType).name, price, *logger_tick_attrib.vals(attrib))

        # TODO: need to relate request to security ***

    def tickSize(self, reqId: TickerId, tickType: TickType, size: int):
        EWrapper.tickSize(self, reqId, tickType, size)
        self.tick_price.logRow(reqId, TickTypeEnum(tickType).name, size)

        # TODO: need to relate request to security ***

    def tickString(self, reqId: TickerId, tickType: TickType, value: str):
        EWrapper.tickString(self, reqId, tickType, value)
        self.tick_string.logRow(reqId, TickTypeEnum(tickType).name, value)

        # TODO: need to relate request to security ***

    def tickEFP(self, reqId: TickerId, tickType: TickType, basisPoints: float,
                formattedBasisPoints: str, totalDividends: float,
                holdDays: int, futureLastTradeDate: str, dividendImpact: float,
                dividendsToLastTradeDate: float):
        EWrapper.tickEFP(self, reqId, tickType, basisPoints, formattedBasisPoints, totalDividends, holdDays,
                         futureLastTradeDate, dividendImpact, dividendsToLastTradeDate)
        self.tick_efp.logRow(reqId, TickTypeEnum(tickType).name, basisPoints, formattedBasisPoints, totalDividends,
                             holdDays, futureLastTradeDate, dividendImpact, dividendsToLastTradeDate)
        # TODO: need to relate request to security ***

    def tickGeneric(self, reqId: TickerId, tickType: TickType, value: float):
        EWrapper.tickGeneric(self, reqId, tickType, value)
        self.tick_generic.logRow(reqId, TickTypeEnum(tickType).name, value)
        # TODO: need to relate request to security ***

    def tickOptionComputation(self, reqId: TickerId, tickType: TickType, tickAttrib: int,
                              impliedVol: float, delta: float, optPrice: float, pvDividend: float,
                              gamma: float, vega: float, theta: float, undPrice: float):
        EWrapper.tickOptionComputation(self, reqId, tickType, tickAttrib, impliedVol, delta, optPrice, pvDividend, gamma,
                                       vega, theta, undPrice)
        ta = map_values(tickAttrib, {0: "Return-based", 1: "Price-based"})
        self.tick_option_computation.logRow(reqId, TickTypeEnum(tickType).name, ta, impliedVol, delta, optPrice,
                                            pvDividend, gamma, vega, theta, undPrice)
        # TODO: need to relate request to security ***

    def tickSnapshotEnd(self, reqId: int):
        # do not ned to implement
        EWrapper.tickSnapshotEnd(self, reqId)

    ####
    # reqHistoricalData
    ####

    def historicalData(self, reqId: int, bar: BarData):
        EWrapper.historicalData(self, reqId, bar)
        self.historical_data.logRow(reqId, *logger_bar_data.vals(bar))
        # TODO: need to relate request to security ***

    def historicalDataEnd(self, reqId: int, start: str, end: str):
        # do not ned to implement
        EWrapper.historicalDataEnd(self, reqId, start, end)

    ####
    # reqRealTimeBars
    ####

    def realtimeBar(self, reqId: TickerId, time: int, open_: float, high: float, low: float, close: float,
                    volume: int, wap: float, count: int):
        EWrapper.realtimeBar(self, reqId, time, open_, high, low, close, volume, wap, count)
        self.realtime_bar.logRow(reqId, unix_sec_to_dh_datetime(time), open_, high, low, close, volume, wap, count)

    ####
    # reqTickByTickData and reqHistoricalTicks
    ####

    def tickByTickAllLast(self, reqId: int, tickType: int, time: int, price: float,
                          size: int, tickAttribLast: TickAttribLast, exchange: str,
                          specialConditions: str):
        EWrapper.tickByTickAllLast(self, reqId, tickType, time, price, size, tickAttribLast, exchange,
                                   specialConditions)

        t = HistoricalTickLast()
        t.time = time
        t.tickAttribLast = tickAttribLast
        t.price = price
        t.size = size
        t.exchange = exchange
        t.specialConditions = specialConditions

        self.tick_last.logRow(reqId, *logger_hist_tick_last.vals(t))

    # noinspection PyUnusedLocal
    def historicalTicksLast(self, reqId: int, ticks: ListOfHistoricalTickLast, done: bool):
        EWrapper.historicalTicksLast(self, reqId, ticks, done)

        for t in ticks:
            self.tick_last.logRow(reqId, *logger_hist_tick_last.vals(t))

    def tickByTickBidAsk(self, reqId: int, time: int, bidPrice: float, askPrice: float,
                         bidSize: int, askSize: int, tickAttribBidAsk: TickAttribBidAsk):
        EWrapper.tickByTickBidAsk(self, reqId, time, bidPrice, askPrice, bidSize, askSize, tickAttribBidAsk)

        t = HistoricalTickBidAsk()
        t.time = time
        t.tickAttribBidAsk = tickAttribBidAsk
        t.priceBid = bidPrice
        t.priceAsk = askPrice
        t.sizeBid = bidSize
        t.sizeAsk = askSize

        self.tick_bid_ask.logRow(reqId, *logger_hist_tick_bid_ask.vals(t))

    def historicalTicksBidAsk(self, reqId: int, ticks: ListOfHistoricalTickBidAsk, done: bool):

        for t in ticks:
            self.tick_bid_ask.logRow(reqId, *logger_hist_tick_bid_ask.vals(t))

    def tickByTickMidPoint(self, reqId: int, time: int, midPoint: float):
        EWrapper.tickByTickMidPoint(self, reqId, time, midPoint)
        self.tick_mid_point.logRow(reqId, unix_sec_to_dh_datetime(time), midPoint)

    def historicalTicks(self, reqId: int, ticks: ListOfHistoricalTick, done: bool):
        EWrapper.historicalTicks(self, reqId, ticks, done)

        for t in ticks:
            self.tick_mid_point.logRow(reqId, unix_sec_to_dh_datetime(t.time), t.price)



