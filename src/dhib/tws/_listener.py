import logging

from deephaven import DynamicTableWriter, Types as dht
from ibapi import news
from ibapi.commission_report import CommissionReport
from ibapi.common import ListOfNewsProviders, OrderId, TickerId, TickAttrib, BarData, TickAttribLast, \
    ListOfHistoricalTickLast, TickAttribBidAsk, ListOfHistoricalTickBidAsk, ListOfHistoricalTick, HistoricalTickBidAsk, \
    HistoricalTickLast, ListOfFamilyCode
from ibapi.contract import Contract
from ibapi.execution import Execution, ExecutionFilter
from ibapi.order import Order
from ibapi.order_state import OrderState
from ibapi.ticktype import TickType, TickTypeEnum
from ibapi.wrapper import EWrapper

from ._client import _IbClient
from ._ibtypelogger import IbContractLogger, IbOrderLogger, IbOrderStateLogger, IbTickAttribLogger, IbBarDataLogger, \
    IbHistoricalTickLastLogger, IbHistoricalTickBidAskLogger, IbFamilyCodeLogger, \
    _map_values
from ..utils import next_unique_id, unix_sec_to_dh_datetime

logging.basicConfig(level=logging.DEBUG)

_ib_contract_logger = IbContractLogger()
_ib_order_logger = IbOrderLogger()
_ib_order_state_logger = IbOrderStateLogger()
_ib_tick_attrib_logger = IbTickAttribLogger()
_ib_bar_data_logger = IbBarDataLogger()
_ib_hist_tick_last_logger = IbHistoricalTickLastLogger()
_ib_hist_tick_bid_ask_logger = IbHistoricalTickBidAskLogger()
_ib_family_code_logger = IbFamilyCodeLogger()

# TODO: map string "" to None
# TODO: parse time strings

# TODO: no users need to see this
class _IbListener(EWrapper):
    """Listener for data from IB."""

    def __init__(self):
        EWrapper.__init__(self)
        self._client = None
        self.account_value = DynamicTableWriter(["Account", "Currency", "Key", "Value"],
                                                [dht.string, dht.string, dht.string, dht.string])
        self.portfolio = DynamicTableWriter(
            ["Account", *_ib_contract_logger.names(), "Position", "MarketPrice", "MarketValue", "AvgCost",
             "UnrealizedPnl", "RealizedPnl"],
            [dht.string, *_ib_contract_logger.types(), dht.float64, dht.float64, dht.float64, dht.float64,
             dht.float64, dht.float64])

        self.account_summary = DynamicTableWriter(["ReqId", "Account", "Tag", "Value", "Currency"],
                                                  [dht.int64, dht.string, dht.string, dht.string, dht.string])

        self.positions = DynamicTableWriter(["Account", *_ib_contract_logger.names(), "Position", "AvgCost"],
                                            [dht.string, *_ib_contract_logger.types(), dht.float64, dht.float64])

        self.news_bulletins = DynamicTableWriter(["MsgId", "MsgType", "Message", "OriginExch"],
                                                 [dht.int64, dht.string, dht.string, dht.string])

        self.exec_details = DynamicTableWriter(["ReqId", "Time", "Account", *_ib_contract_logger.names(),
                                                "Exchange", "Side", "Shares", "Price",
                                                "CumQty", "AvgPrice", "Liquidation",
                                                "EvRule", "EvMultiplier", "ModelCode", "LastLiquidity"
                                                                                       "ExecId", "PermId", "ClientId",
                                                "OrderId", "OrderRef"],
                                               [dht.int64, dht.string, dht.string, *_ib_contract_logger.types(),
                                                dht.string, dht.string, dht.float64, dht.float64,
                                                dht.float64, dht.float64, dht.int64,
                                                dht.string, dht.float64, dht.string, dht.int64,
                                                dht.string, dht.int64, dht.int64, dht.int64, dht.string])

        self.commission_report = DynamicTableWriter(
            ["ExecId", "Currency", "Commission", "RealizedPnl", "Yield", "YieldRedemptionDate"],
            [dht.string, dht.string, dht.float64, dht.float64, dht.float64, dht.int64])

        self.news_providers = DynamicTableWriter(["Provider"], [dht.string])

        self.orders_completed = DynamicTableWriter(
            [*_ib_contract_logger.names(), *_ib_order_logger.names(), *_ib_order_state_logger.names()],
            [*_ib_contract_logger.types(), *_ib_order_logger.types(), *_ib_order_state_logger.types()])

        self.orders_status = DynamicTableWriter(
            ["OrderId", "Status", "Filled", "Remaining", "AvgFillPrice", "PermId", "ParentId", "LastFillPrice",
             "ClientId", "WhyHeld", "MktCapPrice"],
            [dht.int64, dht.string, dht.float64, dht.float64, dht.float64, dht.int64, dht.int64, dht.float64, dht.int64,
             dht.string, dht.float64])

        self.orders_open = DynamicTableWriter(
            ["OrderId", *_ib_contract_logger.names(), *_ib_order_logger.names(), *_ib_order_state_logger.names()],
            [dht.int64, *_ib_contract_logger.types(), *_ib_order_logger.types(), *_ib_order_state_logger.types()])

        self.news_historical = DynamicTableWriter(
            ["RequestId", "Time", "ProviderCode", "ArticleId", "Headline"],
            [dht.int64, dht.string, dht.string, dht.string, dht.string])

        self.news_article = DynamicTableWriter(
            ["RequestId", "ArticleType", "ArticleText"],
            [dht.int64, dht.string, dht.string])

        self.tick_price = DynamicTableWriter(
            ["RequestId", "TickType", "Price", *_ib_tick_attrib_logger.names()],
            [dht.int64, dht.string, dht.float64, *_ib_tick_attrib_logger.types()])

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
            ["RequestId", *_ib_bar_data_logger.names()],
            [dht.int64, *_ib_bar_data_logger.types()])

        self.realtime_bar = DynamicTableWriter(
            ["RequestId", "Timestamp", "Open", "High", "Low", "Close", "Volume", "WAP", "Count"],
            [dht.int64, dht.datetime, dht.float64, dht.float64, dht.float64, dht.float64, dht.int64, dht.float64,
             dht.int64])

        self.tick_last = DynamicTableWriter(
            ["RequestId", *_ib_hist_tick_last_logger.names()],
            [dht.int64, *_ib_hist_tick_last_logger.types()])

        self.tick_bid_ask = DynamicTableWriter(
            ["RequestId", *_ib_hist_tick_bid_ask_logger.names()],
            [dht.int64, *_ib_hist_tick_bid_ask_logger.types()])

        self.tick_mid_point = DynamicTableWriter(
            ["RequestId", "Timestamp", "MidPoint"],
            [dht.int64, dht.datetime, dht.float64])

        self.family_codes = DynamicTableWriter(
            [*_ib_family_code_logger.names()],
            [*_ib_family_code_logger.types()])


    def connect(self, client: _IbClient):
        self._client = client

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



    ####
    # reqManagedAccts
    ####

    def managedAccounts(self, accountsList: str):
        EWrapper.managedAccounts(accountsList)

        for account in accountsList.split(","):
            self._client.reqAccountUpdates(subscribe=True, acctCode=account)

    ####
    # reqAccountUpdates
    ####

    def updateAccountValue(self, key: str, val: str, currency: str, accountName: str):
        EWrapper.updateAccountValue(key, val, currency, accountName)
        self.account_value.logRow(accountName, currency, key, val)

    def updatePortfolio(self, contract: Contract, position: float,
                        marketPrice: float, marketValue: float,
                        averageCost: float, unrealizedPNL: float,
                        realizedPNL: float, accountName: str):
        EWrapper.updatePortfolio(contract, position, marketPrice, marketValue, averageCost, unrealizedPNL,
                                 realizedPNL, accountName)
        self.portfolio.logRow(accountName, *_ib_contract_logger.vals(contract), position, marketPrice, marketValue,
                              averageCost, unrealizedPNL, realizedPNL)

    ####
    # reqAccountSummary
    ####

    def accountSummary(self, reqId: int, account: str, tag: str, value: str, currency: str):
        EWrapper.accountSummary(reqId, account, tag, value, currency)
        self.account_summary.logRow(reqId, account, tag, value, currency)

    ####
    # reqPositions
    ####

    def position(self, account: str, contract: Contract, position: float, avgCost: float):
        EWrapper.position(account, contract, position, avgCost)
        self.positions.logRow(account, *_ib_contract_logger.vals(contract), position, avgCost)

    ####
    # reqNewsBulletins
    ####

    def updateNewsBulletin(self, msgId: int, msgType: int, newsMessage: str, originExch: str):
        EWrapper.updateNewsBulletin(msgId, msgType, newsMessage, originExch)

        if msgType == news.NEWS_MSG:
            mtype = "NEWS"
        elif msgType == news.EXCHANGE_AVAIL_MSG:
            mtype = "EXCHANGE_AVAILABLE"
        elif msgType == news.EXCHANGE_UNAVAIL_MSG:
            mtype = "EXCHANGE_UNAVAILABLE"
        else:
            mtype = f"UNKNOWN({msgType})"

        self.news_bulletins.logRow(msgId, mtype, newsMessage, originExch)

    ####
    # reqExecutions
    ####

    def execDetails(self, reqId: int, contract: Contract, execution: Execution):
        EWrapper.execDetails(reqId, contract, execution)
        self.exec_details.logRow(reqId, execution.time, execution.acctNumber, *_ib_contract_logger.vals(contract),
                                 execution.exchange, execution.side, execution.shares, execution.price,
                                 execution.cumQty, execution.avgPrice, execution.liquidation,
                                 execution.evRule, execution.evMultiplier, execution.modelCode, execution.lastLiquidity,
                                 execution.execId, execution.permId, execution.clientId, execution.orderId,
                                 execution.orderRef)

    def execDetailsEnd(self, reqId: int):
        # do not need to implement
        EWrapper.execDetailsEnd(reqId)

    def commissionReport(self, commissionReport: CommissionReport):
        EWrapper.commissionReport(commissionReport)
        self.commission_report.logRow(commissionReport.execId, commissionReport.currency, commissionReport.commission,
                                      commissionReport.realizedPNL, commissionReport.yield_,
                                      commissionReport.yieldRedemptionDate)

    ####
    # reqNewsProviders
    ####

    def newsProviders(self, newsProviders: ListOfNewsProviders):
        EWrapper.newsProviders(newsProviders)

        for provider in newsProviders:
            self.news_providers.logRow(provider)

    ####
    # reqCompletedOrders
    ####

    def completedOrder(self, contract: Contract, order: Order, orderState: OrderState):
        EWrapper.completedOrder(contract, order, orderState)
        self.orders_completed.logRow(*_ib_contract_logger.vals(contract), *_ib_order_logger.vals(order),
                                     *_ib_order_state_logger.vals(orderState))

    def completedOrdersEnd(self):
        # do not ned to implement
        EWrapper.completedOrdersEnd()

    ####
    # reqAllOpenOrders
    ####

    def orderStatus(self, orderId: OrderId, status: str, filled: float,
                    remaining: float, avgFillPrice: float, permId: int,
                    parentId: int, lastFillPrice: float, clientId: int,
                    whyHeld: str, mktCapPrice: float):
        EWrapper.orderStatus(orderId, status, filled, remaining, avgFillPrice, permId, parentId, lastFillPrice,
                             clientId, whyHeld, mktCapPrice)
        self.orders_status.logRow(orderId, status, filled, remaining, avgFillPrice, permId, parentId, lastFillPrice,
                                  clientId, whyHeld, mktCapPrice)

    def openOrder(self, orderId: OrderId, contract: Contract, order: Order, orderState: OrderState):
        EWrapper.openOrder(orderId, contract, order, orderState)
        self.orders_open.logRow(orderId, *_ib_contract_logger.vals(contract), *_ib_order_logger.vals(order),
                                *_ib_order_state_logger.vals(orderState))

    def openOrderEnd(self):
        # do not ned to implement
        EWrapper.openOrderEnd()

    ####
    # reqHistoricalNews
    ####

    def historicalNews(self, requestId: int, time: str, providerCode: str, articleId: str, headline: str):
        EWrapper.historicalNews(requestId, time, providerCode, articleId, headline)
        self.news_historical.logRow(requestId, time, providerCode, articleId, headline)

    def historicalNewsEnd(self, requestId: int, hasMore: bool):
        # do not ned to implement
        self.historicalNewsEnd(requestId, hasMore)

    ####
    # reqNewsArticle
    ####

    def newsArticle(self, requestId: int, articleType: int, articleText: str):
        EWrapper.newsArticle(requestId, articleType, articleText)
        at = _map_values(articleType, {0: "Plain_Text_Or_Html", 1: "Binary_Data_Or_Pdf"})
        self.news_article.logRow(requestId, at, articleText)

    ####
    # reqMktData
    ####

    def tickPrice(self, reqId: TickerId, tickType: TickType, price: float, attrib: TickAttrib):
        EWrapper.tickPrice(reqId, tickType, price, attrib)

        self.tick_price.logRow(reqId, TickTypeEnum(tickType).name, price, *_ib_tick_attrib_logger.vals(attrib))

        # TODO: need to relate request to security ***

    def tickSize(self, reqId: TickerId, tickType: TickType, size: int):
        EWrapper.tickSize(reqId, tickType, size)
        self.tick_price.logRow(reqId, TickTypeEnum(tickType).name, size)

        # TODO: need to relate request to security ***

    def tickString(self, reqId: TickerId, tickType: TickType, value: str):
        EWrapper.tickString(reqId, tickType, value)
        self.tick_string.logRow(reqId, TickTypeEnum(tickType).name, value)

        # TODO: need to relate request to security ***

    def tickEFP(self, reqId: TickerId, tickType: TickType, basisPoints: float,
                formattedBasisPoints: str, totalDividends: float,
                holdDays: int, futureLastTradeDate: str, dividendImpact: float,
                dividendsToLastTradeDate: float):
        EWrapper.tickEFP(reqId, tickType, basisPoints, formattedBasisPoints, totalDividends, holdDays,
                         futureLastTradeDate, dividendImpact, dividendsToLastTradeDate)
        self.tick_efp.logRow(reqId, TickTypeEnum(tickType).name, basisPoints, formattedBasisPoints, totalDividends,
                             holdDays, futureLastTradeDate, dividendImpact, dividendsToLastTradeDate)
        # TODO: need to relate request to security ***

    def tickGeneric(self, reqId: TickerId, tickType: TickType, value: float):
        EWrapper.tickGeneric(reqId, tickType, value)
        self.tick_generic.logRow(reqId, TickTypeEnum(tickType).name, value)
        # TODO: need to relate request to security ***

    def tickOptionComputation(self, reqId: TickerId, tickType: TickType, tickAttrib: int,
                              impliedVol: float, delta: float, optPrice: float, pvDividend: float,
                              gamma: float, vega: float, theta: float, undPrice: float):
        EWrapper.tickOptionComputation(reqId, tickType, tickAttrib, impliedVol, delta, optPrice, pvDividend, gamma,
                                       vega, theta, undPrice)
        ta = _map_values(tickAttrib, {0: "Return-based", 1: "Price-based"})
        self.tick_option_computation.logRow(reqId, TickTypeEnum(tickType).name, ta, impliedVol, delta, optPrice,
                                            pvDividend, gamma, vega, theta, undPrice)
        # TODO: need to relate request to security ***

    def tickSnapshotEnd(self, reqId: int):
        # do not ned to implement
        EWrapper.tickSnapshotEnd(reqId)

    ####
    # reqHistoricalData
    ####

    def historicalData(self, reqId: int, bar: BarData):
        EWrapper.historicalData(self, reqId, bar)
        self.historical_data.logRow(reqId, *_ib_bar_data_logger.vals(bar))
        # TODO: need to relate request to security ***

    def historicalDataEnd(self, reqId: int, start: str, end: str):
        # do not ned to implement
        EWrapper.historicalDataEnd(reqId, start, end)

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

        self.tick_last.logRow(reqId, *_ib_hist_tick_last_logger.vals(t))

    # noinspection PyUnusedLocal
    def historicalTicksLast(self, reqId: int, ticks: ListOfHistoricalTickLast, done: bool):
        EWrapper.historicalTicksLast(self, reqId, ticks, done)

        for t in ticks:
            self.tick_last.logRow(reqId, *_ib_hist_tick_last_logger.vals(t))

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

        self.tick_bid_ask.logRow(reqId, *_ib_hist_tick_bid_ask_logger.vals(t))

    def historicalTicksBidAsk(self, reqId: int, ticks: ListOfHistoricalTickBidAsk, done: bool):

        for t in ticks:
            self.tick_bid_ask.logRow(reqId, *_ib_hist_tick_bid_ask_logger.vals(t))

    def tickByTickMidPoint(self, reqId: int, time: int, midPoint: float):
        EWrapper.tickByTickMidPoint(self, reqId, time, midPoint)
        self.tick_mid_point.logRow(reqId, unix_sec_to_dh_datetime(time), midPoint)

    def historicalTicks(self, reqId: int, ticks: ListOfHistoricalTick, done: bool):
        EWrapper.historicalTicks(self, reqId, ticks, done)

        for t in ticks:
            self.tick_mid_point.logRow(reqId, unix_sec_to_dh_datetime(t.time), t.price)

    ####
    # reqFamilyCodes
    ####

    def familyCodes(self, familyCodes: ListOfFamilyCode):
        EWrapper.familyCodes(familyCodes)

        for fc in familyCodes:
            self.family_codes.logRow(*_ib_family_code_logger.vals(fc))
