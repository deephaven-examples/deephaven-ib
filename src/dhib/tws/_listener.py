import logging
from typing import Any, List, Tuple

import jpy
from deephaven import DynamicTableWriter, Types as dht
from ibapi import news
from ibapi.commission_report import CommissionReport
from ibapi.common import ListOfNewsProviders
from ibapi.contract import Contract
from ibapi.execution import Execution, ExecutionFilter
from ibapi.order import Order
from ibapi.order_state import OrderState
from ibapi.wrapper import EWrapper

from ._client import _IbClient

logging.basicConfig(level=logging.DEBUG)


def _contract_names() -> List[str]:
    return [
        "ContractId",
        "SecId",
        "SecIdType",
        "SecType",
        "Symbol",
        "LocalSymbol",
        "TradingClass",
        "Currency",
        "Exchange",
        "PrimaryExchange",
        "LastTradeDateOrContractMonth",
        "Strike",
        "Right",
        "Multiplier",
    ]


def _contract_types() -> List[Any]:
    return [
        dht.int64,
        dht.string,
        dht.string,
        dht.string,
        dht.string,
        dht.string,
        dht.string,
        dht.string,
        dht.string,
        dht.string,
        dht.string,
        dht.float64,
        dht.string,
        dht.string,
    ]


def _contract_vals(contract: Contract) -> List[Any]:
    return [
        contract.conId,
        contract.secId,
        contract.secIdType,
        contract.secType,
        contract.symbol,
        contract.localSymbol,
        contract.tradingClass,
        contract.currency,
        contract.exchange,
        contract.primaryExchange,
        contract.lastTradeDateOrContractMonth,
        contract.strike,
        contract.right,
        contract.multiplier,
    ]

# TODO: no users need to see this
class _IbListener(EWrapper):
    """Listener for data from IB."""

    def __init__(self):
        EWrapper.__init__(self)
        self._client = None
        self.account_value = DynamicTableWriter(["Account", "Currency", "Key", "Value"],
                                                [dht.string, dht.string, dht.string, dht.string])
        self.portfolio = DynamicTableWriter(
            ["Account", *_contract_names(), "Position", "MarketPrice", "MarketValue", "AvgCost",
             "UnrealizedPnl", "RealizedPnl"],
            [dht.string, *_contract_types(), dht.float64, dht.float64, dht.float64, dht.float64,
             dht.float64, dht.float64])

        self.account_summary = DynamicTableWriter(["ReqId", "Account", "Tag", "Value", "Currency"],
                                                  [dht.int64, dht.string, dht.string, dht.string, dht.string])

        self.positions = DynamicTableWriter(["Account", *_contract_names(), "Position", "AvgCost"],
                                            [dht.string, *_contract_types(), dht.float64, dht.float64])

        self.news_bulletins = DynamicTableWriter(["MsgId", "MsgType", "Message", "OriginExch"],
                                                 [dht.int64, dht.string, dht.string, dht.string])

        self.exec_details = DynamicTableWriter(["ReqId", "Time", "Account", *_contract_names(),
                                                "Exchange", "Side", "Shares", "Price",
                                                "CumQty", "AvgPrice", "Liquidation",
                                                "EvRule", "EvMultiplier", "ModelCode", "LastLiquidity"
                                                                                       "ExecId", "PermId", "ClientId",
                                                "OrderId", "OrderRef"],
                                               [dht.int64, dht.string, dht.string, *_contract_types(),
                                                dht.string, dht.string, dht.float64, dht.float64,
                                                dht.float64, dht.float64, dht.int64,
                                                dht.string, dht.float64, dht.string, dht.int64,
                                                dht.string, dht.int64, dht.int64, dht.int64, dht.string])

        self.commission_report = DynamicTableWriter(
            ["ExecId", "Currency", "Commission", "RealizedPnl", "Yield", "YieldRedemptionDate"],
            [dht.string, dht.string, dht.float64, dht.float64, dht.float64, dht.int64])

        self.news_providers = DynamicTableWriter(["Provider"], [dht.string])


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

        client.reqAccountSummary(reqId=0, groupName="All", tags=",".join(account_summary_tags))
        client.reqPositions()
        client.reqNewsBulletins(allMsgs=True)
        client.reqExecutions(reqId=0, execFilter=ExecutionFilter())
        client.reqCompletedOrders(apiOnly=False)
        client.reqNewsProviders()


    def disconnect(self):
        self._client = None



    ####
    # reqManagedAccts
    ####

    def managedAccounts(self, accountsList: str):
        EWrapper.managedAccounts(self, accountsList)

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
        EWrapper.updatePortfolio(self, contract, position, marketPrice, marketValue, averageCost, unrealizedPNL,
                                 realizedPNL, accountName)
        self.portfolio.logRow(accountName, *_contract_vals(contract), position, marketPrice, marketValue,
                              averageCost, unrealizedPNL, realizedPNL)

    ####
    # reqAccountSummary
    ####

    def accountSummary(self, reqId: int, account: str, tag: str, value: str, currency: str):
        EWrapper.accountSummary(self, reqId, account, tag, value, currency)
        self.account_summary.logRow(reqId, account, tag, value, currency)

    ####
    # reqPositions
    ####

    def position(self, account: str, contract: Contract, position: float, avgCost: float):
        EWrapper.position(account, contract, position, avgCost)
        self.positions.logRow(account, *_contract_vals(contract), position, avgCost)

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
        EWrapper.execDetails(self, reqId, contract, execution)
        self.exec_details.logRow(reqId, execution.time, execution.acctNumber, *_contract_vals(contract),
                                 execution.exchange, execution.side, execution.shares, execution.price,
                                 execution.cumQty, execution.avgPrice, execution.liquidation,
                                 execution.evRule, execution.evMultiplier, execution.modelCode, execution.lastLiquidity,
                                 execution.execId, execution.permId, execution.clientId, execution.orderId,
                                 execution.orderRef)

    def execDetailsEnd(self, reqId: int):
        # do not need to implement
        EWrapper.execDetailsEnd(self, reqId)

    def commissionReport(self, commissionReport: CommissionReport):
        EWrapper.commissionReport(self, commissionReport)
        self.commission_report.logRow(commissionReport.execId, commissionReport.currency, commissionReport.commission,
                                      commissionReport.realizedPNL, commissionReport.yield_,
                                      commissionReport.yieldRedemptionDate)

    ####
    # reqNewsProviders
    ####

    def newsProviders(self, newsProviders: ListOfNewsProviders):
        EWrapper.newsProviders(self, newsProviders)

        for provider in newsProviders:
            self.news_providers.logRow(provider)

    ####
    # reqCompletedOrders
    ####

    def completedOrder(self, contract: Contract, order: Order, orderState: OrderState):

        self.orders_completed = DynamicTableWriter(
            [*_contract_names(), *_order_names(), *_order_state_names()],
            [*_contract_types(), *_order_types(), *_order_state_types()])

        EWrapper.completedOrder(self, contract, order, orderState)

        self.orders_completed.logRow(*_contract_vals(contract), *_order_vals(order), *_order_state_vals(orderState))

    def completedOrdersEnd(self):
        # do not ned to implement
        EWrapper.completedOrdersEnd(self)


def _order_names() -> List[str]:
    return [od[0] for od in _order_data()]


def _order_types() -> List[Any]:
    return [od[1] for od in _order_data()]


def _order_vals(order: Order) -> List[Any]:
    return [od[2](order) for od in _order_data()]


# TODO: make private
def map_values(value, map, default=lambda v: f"UNKNOWN(v)"):
    try:
        return map[value]
    except KeyError:
        # TODO: log bad mapping
        return default(value)


ArrayStringSet = jpy.get_type("io.deephaven.stringset.ArrayStringSet")


def tag_value_list(value):
    if value is None:
        return None

    return ArrayStringSet(",".join([str(v) for v in value]))


def str_val(value):
    if value is None:
        return None

    return str(value)


def _order_data() -> List[Tuple]:
    oca_types = {1: "CANCEL_WITH_BLOCK", 2: "REDUCE_WITH_BLOCK", 3: "REDUCE_NON_BLOCK"}
    trigger_methods = {0: "Default", 1: "Double_Bid_Ask", 2: "Last", 3: "Double_Last", 4: "Bid_Ask",
                       7: "Last_or_Bid_Ask", 8: "Mid-point"}
    rule80_values = {"I": "Individual", "A": "Agency", "W": "AgentOtherMember", "J": "IndividualPTIA",
                     "U": "AgencyPTIA", "M": "AgentOtherMemberPTIA", "K": "IndividualPT", "Y": "AgencyPT",
                     "N": "AgentOtherMemberPT"}
    open_close_values = {"O": "Open", "C": "Close"}
    origin_values = {0: "Customer", 1: "Firm", 2: "Unknown"}
    short_sale_slot_values = {1: "Holding", 2: "Elsewhere"}
    volatility_type = {1: "Daily", 2: "Annual"}
    reference_price_type = {1: "Average", 2: "BidOrAsk"}
    hedge_type = {"D": "Delta", "B": "Beta", "F": "FX", "P": "Pair"}
    auction_stragey_values = {0: "Unset", 1: "Match", 2: "Improvement", 3: "Transparent"}

    return [

        # order identifier
        ("OrderId", dht.int64, lambda o: o.orderId),
        ("ClientId", dht.int64, lambda o: o.clientId),
        ("PermId", dht.int64, lambda o: o.permId),

        # main order fields
        ("Action", dht.string, lambda o: o.action),
        ("TotalQuantity", dht.int64, lambda o: o.totalQuantity),
        ("OrderType", dht.string, lambda o: o.orderType),
        ("LmtPrice", dht.float64, lambda o: o.lmtPrice),
        ("AuxPrice", dht.float64, lambda o: o.auxPrice),

        # extended order fields
        ("TIF", dht.string, lambda o: o.tif),
        ("ActiveStartTime", dht.string, lambda o: o.activeStartTime),
        ("ActiveStopTime", dht.string, lambda o: o.activeStopTime),
        ("OcaGroup", dht.string, lambda o: o.ocaGroup),
        ("OcaType", dht.string, lambda o: map_values(o.ocaType, oca_types)),
        ("OrderRef", dht.string, lambda o: o.orderRef),
        ("Transmit", dht.bool_, lambda o: o.transmit),
        ("ParentId", dht.int64, lambda o: o.parentId),
        ("BlockOrder", dht.bool_, lambda o: o.blockOrder),
        ("SweepToFill", dht.bool_, lambda o: o.sweepToFill),
        ("DisplaySize", dht.int64, lambda o: o.displaySize),
        ("TriggerMethod", dht.string, lambda o: map_values(o.triggerMethod, trigger_methods)),
        ("OutsideRth", dht.bool_, lambda o: o.outsideRth),
        ("Hidden", dht.bool_, lambda o: o.hidden),
        ("GoodAfterTime", dht.string, lambda o: o.goodAfterTime),
        ("GoodTillDate", dht.string, lambda o: o.goodTillDate),
        ("Rule80A", dht.string, lambda o: map_values(o.rule80A, rule80_values)),
        ("AllOrNone", dht.bool_, lambda o: o.allOrNone),
        ("MinQty", dht.int64, lambda o: o.minQty),
        ("PercentOffset", dht.float64, lambda o: o.percentOffset),
        ("OverridePercentageConstraints", dht.bool_, lambda o: o.overridePercentageConstraints),
        ("TrailStopPrice", dht.float64, lambda o: o.trailStopPrice),
        ("TrailingPercent", dht.float64, lambda o: o.trailingPercent),

        # financial advisors only
        ("FaGroup", dht.string, lambda o: o.faGroup),
        ("FaProfile", dht.string, lambda o: o.faProfile),
        ("FaMethod", dht.string, lambda o: o.faMethod),
        ("FaPercentage", dht.string, lambda o: o.faPercentage),

        # institutional (ie non-cleared) only
        ("DesignatedLocation", dht.string, lambda o: o.designatedLocation),
        ("OpenClose", dht.string, lambda o: map_values(o.openClose, open_close_values)),
        ("Origin", dht.string, lambda o: map_values(o.origin, origin_values)),
        ("ShortSaleSlot", dht.string, lambda o: map_values(o.shortSaleSlot, short_sale_slot_values)),
        ("ExemptClode", dht.int64, lambda o: o.exemptCode),

        # SMART routing only
        ("DiscretionaryAmt", dht.int64, lambda o: o.discretionaryAmt),
        ("ETradeOnly", dht.bool_, lambda o: o.eTradeOnly),
        ("FirmQuoteOnly", dht.bool_, lambda o: o.firmQuoteOnly),
        ("NbboPriceCap", dht.float64, lambda o: o.nbboPriceCap),
        ("OptOutSmarRouting", dht.bool_, lambda o: o.optOutSmartRouting),

        # BOX exchange orders only
        ("AuctionStrategy", dht.string, lambda o: map_values(o.auctionStrategy, auction_stragey_values)),
        ("StartingPrice", dht.float64, lambda o: o.startingPrice),
        ("StockRefPrice", dht.float64, lambda o: o.stockRefPrice),
        ("Delta", dht.float64, lambda o: o.delta),

        # pegged to stock and VOL orders only
        ("StockRangeLower", dht.float64, lambda o: o.stockRangeLower),
        ("StockRangeUpper", dht.float64, lambda o: o.stockRangeUpper),

        ("RandomizePrice", dht.bool_, lambda o: o.randomizePrice),
        ("RandomizeSize", dht.bool_, lambda o: o.randomizeSize),

        # VOLATILITY ORDERS ONLY
        ("Volatility", dht.float64, lambda o: o.volatility),
        ("VolatilityType", dht.string, lambda o: map_values(o.volatilityType, volatility_type)),
        ("DeltaNeutralOrderType", dht.string, lambda o: o.deltaNeutralOrderType),
        ("DeltaNeutralAuxPrice", dht.float64, lambda o: o.deltaNeutralAuxPrice),
        ("DeltaNeutralConId", dht.int64, lambda o: o.deltaNeutralConId),
        ("DeltaNeutralSettlingFirm", dht.string, lambda o: o.deltaNeutralSettlingFirm),
        ("DeltaNeutralClearingAccount", dht.string, lambda o: o.deltaNeutralClearingAccount),
        ("DeltaNeutralClearingIntent", dht.string, lambda o: o.deltaNeutralClearingIntent),
        ("DeltaNeutralOpenClose", dht.string, lambda o: o.deltaNeutralOpenClose),
        ("DeltaNeutralShortSale", dht.bool_, lambda o: o.deltaNeutralShortSale),
        ("DeltaNeutralShortSaleSlot", dht.int64, lambda o: o.deltaNeutralShortSaleSlot),
        ("DeltaNeutralDesignatedLocation", dht.string, lambda o: o.deltaNeutralDesignatedLocation),
        ("ContinuousUpdate", dht.bool_, lambda o: o.continuousUpdate),
        ("ReferencePriceType", dht.string, lambda o: map_values(o.referencePriceType, reference_price_type)),

        # COMBO ORDERS ONLY
        ("BasisPoints", dht.float64, lambda o: o.basisPoints),
        ("BasisPointsType", dht.int64, lambda o: o.basisPointsType),

        # SCALE ORDERS ONLY
        ("ScaleInitLevelSize", dht.int64, lambda o: o.scaleInitLevelSize),
        ("ScaleSubsLevelSize", dht.int64, lambda o: o.scaleSubsLevelSize),
        ("ScalePriceIncrement", dht.float64, lambda o: o.scalePriceIncrement),
        ("ScalePriceAdjustValue", dht.float64, lambda o: o.scalePriceAdjustValue),
        ("ScalePriceAdjustInterval", dht.int64, lambda o: o.scalePriceAdjustInterval),
        ("ScaleProfitOffset", dht.float64, lambda o: o.scaleProfitOffset),
        ("ScaleAutoReset", dht.bool_, lambda o: o.scaleAutoReset),
        ("ScaleInitPosition", dht.int64, lambda o: o.scaleInitPosition),
        ("ScaleInitFillQty", dht.int64, lambda o: o.scaleInitFillQty),
        ("ScaleRandomPercent", dht.bool_, lambda o: o.scaleRandomPercent),
        ("ScaleTable", dht.string, lambda o: o.scaleTable),

        # HEDGE ORDERS
        ("HedgeType", dht.string, lambda o: map_values(o.hedgeType, hedge_type)),
        ("HedgeParam", dht.string, lambda o: o.hedgeParam),

        # Clearing info
        ("Account", dht.string, lambda o: o.account),
        ("SettlingFirm", dht.string, lambda o: o.settlingFirm),
        ("ClearingAccount", dht.string, lambda o: o.clearingAccount),
        ("ClearingIntent", dht.string, lambda o: o.clearingIntent),

        # ALGO ORDERS ONLY
        ("AlgoStrategy", dht.string, lambda o: o.algoStrategy),

        ("AlgoParams", dht.stringset, lambda o: tag_value_list(o.algoParams)),
        ("SmartComboRoutingParams", dht.stringset, lambda o: tag_value_list(o.smartComboRoutingParams)),

        ("AlgoId", dht.string, lambda o: o.algoId),

        # What-if
        ("WhatIf", dht.bool_, lambda o: o.whatIf),

        # Not Held
        ("NotHeld", dht.bool_, lambda o: o.notHeld),
        ("Solicited", dht.bool_, lambda o: o.solicited),

        # models
        ("ModelCode", dht.string, lambda o: o.modelCode),

        # order combo legs

        ("OrderComboLegs", dht.stringset, lambda o: tag_value_list(o.orderComboLegs)),

        ("OrderMiscOptions", dht.stringset, lambda o: tag_value_list(o.orderMiscOptions)),

        # VER PEG2BENCH fields:
        ("ReferenceContractId", dht.int64, lambda o: o.referenceContractId),
        ("PeggedChangeAmount", dht.float64, lambda o: o.peggedChangeAmount),
        ("IsPeggedChangeAmountDecrease", dht.bool_, lambda o: o.isPeggedChangeAmountDecrease),
        ("ReferenceChangeAmount", dht.float64, lambda o: o.referenceChangeAmount),
        ("ReferenceExchangeId", dht.string, lambda o: o.referenceExchangeId),
        ("AdjustedOrderType", dht.string, lambda o: o.adjustedOrderType),

        ("TriggerPrice", dht.float64, lambda o: o.triggerPrice),
        ("AdjustedStopPrice", dht.float64, lambda o: o.adjustedStopPrice),
        ("AdjustedStopLimitPrice", dht.float64, lambda o: o.adjustedStopLimitPrice),
        ("AdjustedTrailingAmount", dht.float64, lambda o: o.adjustedTrailingAmount),
        ("AdjustableTrailingUnit", dht.int64, lambda o: o.adjustableTrailingUnit),
        ("LmtPriceOffset", dht.float64, lambda o: o.lmtPriceOffset),

        ("Conditions", dht.stringset, lambda o: tag_value_list(o.conditions)),
        ("ConditionsCancelOrder", dht.bool_, lambda o: o.conditionsCancelOrder),
        ("ConditionsIgnoreRth", dht.bool_, lambda o: o.conditionsIgnoreRth),

        # ext operator
        ("ExtOperator", dht.string, lambda o: o.extOperator),

        # native cash quantity
        ("CashQty", dht.float64, lambda o: o.cashQty),

        ("Mifid2DecisionMaker", dht.string, lambda o: o.mifid2DecisionMaker),
        ("Mifid2DecisionAlgo", dht.string, lambda o: o.mifid2DecisionAlgo),
        ("Mifid2ExecutionTrader", dht.string, lambda o: o.mifid2ExecutionTrader),
        ("Mifid2ExecutionAlgo", dht.string, lambda o: o.mifid2ExecutionAlgo),

        ("Don'tUseAutoPriceForHedge", dht.bool_, lambda o: o.dontUseAutoPriceForHedge),

        ("IsOmsContainer", dht.bool_, lambda o: o.isOmsContainer),

        ("DiscretionaryUpToLimitPrice", dht.bool_, lambda o: o.discretionaryUpToLimitPrice),

        ("AutoCancelDate", dht.string, lambda o: o.autoCancelDate),
        ("FilledQuantity", dht.float64, lambda o: o.filledQuantity),
        ("RefFuturesConId", dht.int64, lambda o: o.refFuturesConId),
        ("AutoCancelParent", dht.bool_, lambda o: o.autoCancelParent),
        ("Shareholder", dht.string, lambda o: o.shareholder),
        ("ImbalanceOnly", dht.bool_, lambda o: o.imbalanceOnly),
        ("RouteMarketableToBbo", dht.bool_, lambda o: o.routeMarketableToBbo),
        ("ParentPermId", dht.int64, lambda o: o.parentPermId),

        ("UsePriceMgmtAlgo", dht.bool_, lambda o: o.usePriceMgmtAlgo),

        # soft dollars
        ("SoftDollarTier", dht.string, lambda o: str_val(o.softDollarTier)),
    ]
