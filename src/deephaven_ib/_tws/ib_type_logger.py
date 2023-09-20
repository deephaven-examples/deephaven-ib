"""Functionality for logging IB types to Deephaven tables."""

import sys
from typing import Any, List, Tuple, Dict, Callable, Optional

from deephaven import dtypes

from .._internal.tablewriter import map_values, to_string_val, to_string_set
from ..time import unix_sec_to_j_instant, ib_to_j_instant


class IbComplexTypeLogger:
    """ Base class for logging complex IB types. """

    ib_type: str
    column_details: List[Tuple[str, Any, Callable]]

    def __init__(self, ib_type: str, column_details: List[Tuple[str, Any, Callable]]):
        self.ib_type = ib_type
        self.column_details = column_details

    # noinspection PyDefaultArgument
    def names(self, renames: Dict[str, str] = {}) -> List[str]:
        """ Column names. """
        return [renames.get(cd[0], cd[0]) for cd in self.column_details]

    def types(self) -> List[Any]:
        """ Column types. """
        return [cd[1] for cd in self.column_details]

    def vals(self, ib_obj: Any) -> List[Any]:
        """ Column values extracted from the IB object. """

        if ib_obj is None:
            return [None] * len(self.column_details)

        return [cd[2](ib_obj) for cd in self.column_details]


###

def _include_details(details: List[Tuple], lambda_for_field: Callable) -> List[Tuple]:
    """Details for logging one type within another.

    Args:
        details (List[Tuple]): details for logging the included type.
        lambda_for_field (Callable): lambda for extracting the included value from the type.

    Returns:
        Details for logging the inner type.
    """

    # To understand the bound variable voodoo, see: https://stackoverflow.com/questions/19837486/lambda-in-a-loop
    return [(d[0], d[1], lambda xx, bound_d2=d[2]: bound_d2(lambda_for_field(xx))) for d in details]


####

def _details_family_code() -> List[Tuple]:
    """Details for logging FamilyCode."""

    return [
        ("AccountID", dtypes.string, lambda fc: fc.accountID),
        ("FamilyCode", dtypes.string, lambda fc: fc.familyCodeStr),
    ]


logger_family_code = IbComplexTypeLogger("FamilyCode", _details_family_code())


####

def _details_contract() -> List[Tuple]:
    """ Details for logging Contract. """

    def map_right(right: str) -> Optional[str]:
        if right == "?":
            return None

        return right

    def map_multiplier(multiplier: str) -> float:
        if multiplier is None or multiplier == "":
            return 1.0

        return float(multiplier)

    return [
        ("ContractId", dtypes.int64, lambda contract: contract.conId),
        ("SecId", dtypes.string, lambda contract: contract.secId),
        ("SecIdType", dtypes.string, lambda contract: contract.secIdType),
        ("SecType", dtypes.string, lambda contract: contract.secType),
        ("Symbol", dtypes.string, lambda contract: contract.symbol),
        ("LocalSymbol", dtypes.string, lambda contract: contract.localSymbol),
        ("TradingClass", dtypes.string, lambda contract: contract.tradingClass),
        ("Currency", dtypes.string, lambda contract: contract.currency),
        ("Exchange", dtypes.string, lambda contract: contract.exchange),
        ("PrimaryExchange", dtypes.string, lambda contract: contract.primaryExchange),
        ("LastTradeDateOrContractMonth", dtypes.string, lambda contract: contract.lastTradeDateOrContractMonth),
        ("Strike", dtypes.float64, lambda contract: float(contract.strike)),
        ("Right", dtypes.string, lambda contract: map_right(contract.right)),
        ("Multiplier", dtypes.float64, lambda contract: map_multiplier(contract.multiplier)),

        # combos
        ("ComboLegsDescrip", dtypes.string, lambda contract: contract.comboLegsDescrip),
        ("ComboLegs", dtypes.StringSet, lambda contract: to_string_set(contract.comboLegs)),
        ("DeltaNeutralContract", dtypes.string, lambda contract: to_string_val(contract.deltaNeutralContract)),
    ]


logger_contract = IbComplexTypeLogger("Contract", _details_contract())


####

def _details_contract_details() -> List[Tuple]:
    """Details for logging ContractDetails."""

    def map_null_int(value: int) -> Optional[int]:

        if value == 2147483647:
            return None

        return value

    def map_sec_id_list(value):
        if not value:
            return None

        return to_string_set([f"{v.tag}={v.value}" for v in value])

    return [
        *_include_details(_details_contract(), lambda cd: cd.contract),
        ("MarketName", dtypes.string, lambda cd: cd.marketName),
        ("MinTick", dtypes.float64, lambda cd: cd.minTick),
        ("OrderTypes", dtypes.StringSet, lambda cd: to_string_set(cd.orderTypes.split(","))),
        ("ValidExchanges", dtypes.StringSet, lambda cd: to_string_set(cd.validExchanges.split(","))),
        ("PriceMagnifier", dtypes.int64, lambda cd: cd.priceMagnifier),
        ("UnderConId", dtypes.int64, lambda cd: cd.underConId),
        ("LongName", dtypes.string, lambda cd: cd.longName),
        ("ContractMonth", dtypes.string, lambda cd: cd.contractMonth),
        ("Industry", dtypes.string, lambda cd: cd.industry),
        ("Category", dtypes.string, lambda cd: cd.category),
        ("SubCategory", dtypes.string, lambda cd: cd.subcategory),
        ("TimeZoneId", dtypes.string, lambda cd: cd.timeZoneId),
        ("TradingHours", dtypes.StringSet, lambda cd: to_string_set(cd.tradingHours.split(";"))),
        ("LiquidHours", dtypes.StringSet, lambda cd: to_string_set(cd.liquidHours.split(";"))),
        ("EvRule", dtypes.string, lambda cd: cd.evRule),
        ("EvMultiplier", dtypes.int64, lambda cd: cd.evMultiplier),
        ("AggGroup", dtypes.int64, lambda cd: map_null_int(cd.aggGroup)),
        ("UnderSymbol", dtypes.string, lambda cd: cd.underSymbol),
        ("UnderSecType", dtypes.string, lambda cd: cd.underSecType),
        ("MarketRuleIds", dtypes.StringSet, lambda cd: to_string_set(cd.marketRuleIds.split(","))),
        ("SecIdList", dtypes.StringSet, lambda cd: map_sec_id_list(cd.secIdList)),
        ("RealExpirationDate", dtypes.string, lambda cd: cd.realExpirationDate),
        ("LastTradeTime", dtypes.string, lambda cd: cd.lastTradeTime),
        ("StockType", dtypes.string, lambda cd: cd.stockType),
        # BOND values
        ("CUSIP", dtypes.string, lambda cd: cd.cusip),
        ("Ratings", dtypes.string, lambda cd: cd.ratings),
        ("DescAppend", dtypes.string, lambda cd: cd.descAppend),
        ("BondType", dtypes.string, lambda cd: cd.bondType),
        ("CouponType", dtypes.string, lambda cd: cd.couponType),
        ("Callable", dtypes.bool_, lambda cd: cd.callable),
        ("Putable", dtypes.bool_, lambda cd: cd.putable),
        ("Coupon", dtypes.double, lambda cd: float(cd.coupon)),
        ("Convertible", dtypes.bool_, lambda cd: cd.convertible),
        ("Maturity", dtypes.string, lambda cd: cd.maturity),
        # TODO: convert date time?  Values are not provided in TWS, and the format is not documented. (https://github.com/deephaven-examples/deephaven-ib/issues/10)
        ("IssueDate", dtypes.string, lambda cd: cd.issueDate),
        # TODO: convert date time?  Values are not provided in TWS, and the format is not documented. (https://github.com/deephaven-examples/deephaven-ib/issues/10)
        ("NextOptionDate", dtypes.string, lambda cd: cd.nextOptionDate),
        # TODO: convert date time?  Values are not provided in TWS, and the format is not documented. (https://github.com/deephaven-examples/deephaven-ib/issues/10)
        ("NextOptionType", dtypes.string, lambda cd: cd.nextOptionType),
        ("NextOptionPartial", dtypes.bool_, lambda cd: cd.nextOptionPartial),
        ("Notes", dtypes.string, lambda cd: cd.notes),
    ]


logger_contract_details = IbComplexTypeLogger("ContractDetails", _details_contract_details())


####

def _details_price_increment() -> List[Tuple]:
    """Details for logging PriceIncrement."""

    return [
        ("LowEdge", dtypes.float64, lambda pi: pi.lowEdge),
        ("Increment", dtypes.float64, lambda pi: pi.increment),
    ]


logger_price_increment = IbComplexTypeLogger("PriceIncrement", _details_price_increment())


####

def _details_bar_data() -> List[Tuple]:
    """ Details for logging BarData. """

    def map_null(val):
        if val <= 0:
            return None

        return val

    def parse_timestamp(bd):
        if len(bd.date) is 8:
            # bd.date is a date string
            year = bd.date[0:4]
            month = bd.date[4:6]
            day = bd.date[6:]
            time_string = f"{year}{month}{day} 23:59:59"
            return ib_to_j_instant(time_string)
        else:
            # bd.date is unix sec
            return unix_sec_to_j_instant(int(bd.date))

    return [
        ("Timestamp", dtypes.Instant, parse_timestamp),
        ("Open", dtypes.float64, lambda bd: bd.open),
        ("High", dtypes.float64, lambda bd: bd.high),
        ("Low", dtypes.float64, lambda bd: bd.low),
        ("Close", dtypes.float64, lambda bd: bd.close),
        ("Volume", dtypes.float64, lambda bd: map_null(bd.volume)),
        ("BarCount", dtypes.int64, lambda bd: map_null(bd.barCount)),
        ("WAP", dtypes.float64, lambda bd: map_null(bd.wap)),
    ]


logger_bar_data = IbComplexTypeLogger("BarData", _details_bar_data())


####

def _details_real_time_bar_data() -> List[Tuple]:
    """ Details for logging RealTimeBarData. """

    def map_null(val):
        if val <= 0:
            return None

        return val

    return [
        ("Timestamp", dtypes.Instant, lambda bd: unix_sec_to_j_instant(bd.time)),
        ("TimestampEnd", dtypes.Instant, lambda bd: unix_sec_to_j_instant(bd.endTime)),
        ("Open", dtypes.float64, lambda bd: bd.open_),
        ("High", dtypes.float64, lambda bd: bd.high),
        ("Low", dtypes.float64, lambda bd: bd.low),
        ("Close", dtypes.float64, lambda bd: bd.close),
        ("Volume", dtypes.float64, lambda bd: map_null(bd.volume)),
        ("WAP", dtypes.float64, lambda bd: map_null(bd.wap)),
        ("Count", dtypes.int64, lambda bd: map_null(bd.count)),
    ]


logger_real_time_bar_data = IbComplexTypeLogger("RealTimeBarData", _details_real_time_bar_data())


####

def _details_tick_attrib() -> List[Tuple]:
    """ Details for logging TickAttrib. """

    return [
        ("CanAutoExecute", dtypes.bool_, lambda ta: ta.canAutoExecute),
        ("PastLimit", dtypes.bool_, lambda ta: ta.pastLimit),
        ("PreOpen", dtypes.bool_, lambda ta: ta.preOpen),
    ]


logger_tick_attrib = IbComplexTypeLogger("TickAttrib", _details_tick_attrib())


###

def _details_tick_attrib_last() -> List[Tuple]:
    """Details for logging TickAttribLast."""

    return [
        ("PastLimit", dtypes.bool_, lambda ta: ta.pastLimit),
        ("Unreported", dtypes.bool_, lambda ta: ta.unreported),
    ]


logger_tick_attrib_last = IbComplexTypeLogger("TickAttribLast", _details_tick_attrib_last())


####

def _details_historical_tick_last() -> List[Tuple]:
    """Details for logging HistoricalTickLast."""

    # https://www.interactivebrokers.com/en/index.php?f=7235

    special_conditions_codes = {
        "B": "Average Price Trade",
        "Q": "Market Center Official Open",
        "C": "Cash Trade (Same Day Clearing)",
        "R": "Seller",
        "D": "Distribution",
        "T": "Extended Hours Trade",
        "E": "Automatic Execution",
        "U": "Extended Hours Sold (Out of Sequence)",
        "F": "Intermarket Sweep Order",
        "V": "Stock-Option Trade",
        "G": "Bunched Sold Trade",
        "X": "Cross Trade",
        "H": "Price Variation Trade",
        "Z": "Sold (Out of Sequence)",
        "I": "Odd Lot Trade",
        "4": "Derivatively priced",
        "K": "Rule 127 (NYSE only) or Rule 155 (NYSE MKT only)",
        "5": "Market Center Reopening Trade",
        "L": "Sold Last (Late Reporting)",
        "6": "Market Center Closing Trade",
        "M": "Market Center Official Close",
        "7": "Reserved",
        "N": "Next Day Trade (Next Day Clearing)",
        "8": "Reserved",
        "O": "Market Center Opening Trade",
        "9": "Corrected Consolidated Close Price as per Listing Market",
        "P": "Prior Reference Price",
    }

    def map_special_conditions(special_conditions: str) -> Any:
        if not special_conditions:
            return None

        return to_string_set([map_values(v, special_conditions_codes) for v in "".join(special_conditions.split())])


    return [
        ("Timestamp", dtypes.Instant, lambda t: unix_sec_to_j_instant(t.time)),
        ("Price", dtypes.float64, lambda t: t.price),
        ("Size", dtypes.float64, lambda t: t.size),
        *_include_details(_details_tick_attrib_last(), lambda t: t.tickAttribLast),
        ("Exchange", dtypes.string, lambda t: t.exchange),
        ("SpecialConditions", dtypes.StringSet, lambda t: map_special_conditions(t.specialConditions))
    ]


logger_hist_tick_last = IbComplexTypeLogger("HistoricalTickLast", _details_historical_tick_last())


####

def _details_tick_attrib_bid_ask() -> List[Tuple]:
    """Details for logging TickAttribBidAsk."""

    return [
        ("BidPastLow", dtypes.bool_, lambda ta: ta.bidPastLow),
        ("AskPastHigh", dtypes.bool_, lambda ta: ta.askPastHigh),
    ]


logger_tick_attrib_bid_ask = IbComplexTypeLogger("TickAttribBidAsk", _details_tick_attrib_bid_ask())


####

def _details_historical_tick_bid_ask() -> List[Tuple]:
    """Details for logging HistoricalTickBidAsk."""

    return [
        ("Timestamp", dtypes.Instant, lambda t: unix_sec_to_j_instant(t.time)),
        ("BidPrice", dtypes.float64, lambda t: t.priceBid),
        ("AskPrice", dtypes.float64, lambda t: t.priceAsk),
        ("BidSize", dtypes.float64, lambda t: t.sizeBid),
        ("AskSize", dtypes.float64, lambda t: t.sizeAsk),
        *_include_details(_details_tick_attrib_bid_ask(), lambda t: t.tickAttribBidAsk),
    ]


logger_hist_tick_bid_ask = IbComplexTypeLogger("HistoricalTickBidAsk", _details_historical_tick_bid_ask())


####

def _details_order() -> List[Tuple]:
    """ Details for logging Orders. """

    oca_types = {1: "CancelWithBlock", 2: "ReduceWithBlock", 3: "ReduceNonBlock"}
    trigger_methods = {0: "Default", 1: "DoubleBidAsk", 2: "Last", 3: "DoubleLast", 4: "BidAsk",
                       7: "LastOrBidAsk", 8: "MidPoint"}
    rule80_values = {"": None, "0": None, "I": "Individual", "A": "Agency", "W": "AgentOtherMember",
                     "J": "IndividualPTIA",
                     "U": "AgencyPTIA", "M": "AgentOtherMemberPTIA", "K": "IndividualPT", "Y": "AgencyPT",
                     "N": "AgentOtherMemberPT"}
    open_close_values = {"": None, "O": "Open", "C": "Close"}
    origin_values = {0: "Customer", 1: "Firm", 2: "Unknown"}
    short_sale_slot_values = {0: None, 1: "Holding", 2: "Elsewhere"}
    volatility_type = {0: None, 1: "Daily", 2: "Annual"}
    reference_price_type = {0: None, 1: "Average", 2: "BidOrAsk"}
    hedge_type = {"": None, "D": "Delta", "B": "Beta", "F": "FX", "P": "Pair"}
    auction_stragey_values = {0: "Unset", 1: "Match", 2: "Improvement", 3: "Transparent"}

    return [

        # order identifier
        ("OrderId", dtypes.int64, lambda o: o.orderId),
        ("ClientId", dtypes.int64, lambda o: o.clientId),
        ("PermId", dtypes.int64, lambda o: o.permId),

        # main order fields
        ("Action", dtypes.string, lambda o: o.action),
        ("TotalQuantity", dtypes.float64, lambda o: o.totalQuantity),
        ("OrderType", dtypes.string, lambda o: o.orderType),
        ("LmtPrice", dtypes.float64, lambda o: o.lmtPrice),
        ("AuxPrice", dtypes.float64, lambda o: o.auxPrice),

        # extended order fields
        ("TIF", dtypes.string, lambda o: o.tif),
        ("ActiveStartTime", dtypes.string, lambda o: o.activeStartTime),
        ("ActiveStopTime", dtypes.string, lambda o: o.activeStopTime),
        ("OcaGroup", dtypes.string, lambda o: o.ocaGroup),
        ("OcaType", dtypes.string, lambda o: map_values(o.ocaType, oca_types)),
        ("OrderRef", dtypes.string, lambda o: o.orderRef),
        ("Transmit", dtypes.bool_, lambda o: o.transmit),
        ("ParentId", dtypes.int64, lambda o: o.parentId),
        ("BlockOrder", dtypes.bool_, lambda o: o.blockOrder),
        ("SweepToFill", dtypes.bool_, lambda o: o.sweepToFill),
        ("DisplaySize", dtypes.int64, lambda o: o.displaySize),
        ("TriggerMethod", dtypes.string, lambda o: map_values(o.triggerMethod, trigger_methods)),
        ("OutsideRth", dtypes.bool_, lambda o: o.outsideRth),
        ("Hidden", dtypes.bool_, lambda o: o.hidden),
        ("GoodAfterTime", dtypes.string, lambda o: o.goodAfterTime),
        ("GoodTillDate", dtypes.string, lambda o: o.goodTillDate),
        ("Rule80A", dtypes.string, lambda o: map_values(o.rule80A, rule80_values)),
        ("AllOrNone", dtypes.bool_, lambda o: o.allOrNone),
        ("MinQty", dtypes.int64, lambda o: o.minQty),
        ("PercentOffset", dtypes.float64, lambda o: o.percentOffset),
        ("OverridePercentageConstraints", dtypes.bool_, lambda o: o.overridePercentageConstraints),
        ("TrailStopPrice", dtypes.float64, lambda o: o.trailStopPrice),
        ("TrailingPercent", dtypes.float64, lambda o: o.trailingPercent),

        # financial advisors only
        ("FaGroup", dtypes.string, lambda o: o.faGroup),
        ("FaProfile", dtypes.string, lambda o: o.faProfile),
        ("FaMethod", dtypes.string, lambda o: o.faMethod),
        ("FaPercentage", dtypes.string, lambda o: o.faPercentage),

        # institutional (ie non-cleared) only
        ("DesignatedLocation", dtypes.string, lambda o: o.designatedLocation),
        ("OpenClose", dtypes.string, lambda o: map_values(o.openClose, open_close_values)),
        ("Origin", dtypes.string, lambda o: map_values(o.origin, origin_values)),
        ("ShortSaleSlot", dtypes.string, lambda o: map_values(o.shortSaleSlot, short_sale_slot_values)),
        ("ExemptCode", dtypes.int64, lambda o: o.exemptCode),

        # SMART routing only
        ("DiscretionaryAmt", dtypes.float64, lambda o: o.discretionaryAmt),
        ("OptOutSmarRouting", dtypes.bool_, lambda o: o.optOutSmartRouting),

        # BOX exchange orders only
        ("AuctionStrategy", dtypes.string, lambda o: map_values(o.auctionStrategy, auction_stragey_values)),
        ("StartingPrice", dtypes.float64, lambda o: o.startingPrice),
        ("StockRefPrice", dtypes.float64, lambda o: o.stockRefPrice),
        ("Delta", dtypes.float64, lambda o: o.delta),

        # pegged to stock and VOL orders only
        ("StockRangeLower", dtypes.float64, lambda o: o.stockRangeLower),
        ("StockRangeUpper", dtypes.float64, lambda o: o.stockRangeUpper),

        ("RandomizePrice", dtypes.bool_, lambda o: o.randomizePrice),
        ("RandomizeSize", dtypes.bool_, lambda o: o.randomizeSize),

        # VOLATILITY ORDERS ONLY
        ("Volatility", dtypes.float64, lambda o: o.volatility),
        ("VolatilityType", dtypes.string, lambda o: map_values(o.volatilityType, volatility_type)),
        ("DeltaNeutralOrderType", dtypes.string, lambda o: o.deltaNeutralOrderType),
        ("DeltaNeutralAuxPrice", dtypes.float64, lambda o: o.deltaNeutralAuxPrice),
        ("DeltaNeutralConId", dtypes.int64, lambda o: o.deltaNeutralConId),
        ("DeltaNeutralSettlingFirm", dtypes.string, lambda o: o.deltaNeutralSettlingFirm),
        ("DeltaNeutralClearingAccount", dtypes.string, lambda o: o.deltaNeutralClearingAccount),
        ("DeltaNeutralClearingIntent", dtypes.string, lambda o: o.deltaNeutralClearingIntent),
        ("DeltaNeutralOpenClose", dtypes.string, lambda o: o.deltaNeutralOpenClose),
        ("DeltaNeutralShortSale", dtypes.bool_, lambda o: o.deltaNeutralShortSale),
        ("DeltaNeutralShortSaleSlot", dtypes.int64, lambda o: o.deltaNeutralShortSaleSlot),
        ("DeltaNeutralDesignatedLocation", dtypes.string, lambda o: o.deltaNeutralDesignatedLocation),
        ("ContinuousUpdate", dtypes.bool_, lambda o: o.continuousUpdate),
        ("ReferencePriceType", dtypes.string, lambda o: map_values(o.referencePriceType, reference_price_type)),

        # COMBO ORDERS ONLY
        ("BasisPoints", dtypes.float64, lambda o: o.basisPoints),
        ("BasisPointsType", dtypes.int64, lambda o: o.basisPointsType),

        # SCALE ORDERS ONLY
        ("ScaleInitLevelSize", dtypes.int64, lambda o: o.scaleInitLevelSize),
        ("ScaleSubsLevelSize", dtypes.int64, lambda o: o.scaleSubsLevelSize),
        ("ScalePriceIncrement", dtypes.float64, lambda o: o.scalePriceIncrement),
        ("ScalePriceAdjustValue", dtypes.float64, lambda o: o.scalePriceAdjustValue),
        ("ScalePriceAdjustInterval", dtypes.int64, lambda o: o.scalePriceAdjustInterval),
        ("ScaleProfitOffset", dtypes.float64, lambda o: o.scaleProfitOffset),
        ("ScaleAutoReset", dtypes.bool_, lambda o: o.scaleAutoReset),
        ("ScaleInitPosition", dtypes.int64, lambda o: o.scaleInitPosition),
        ("ScaleInitFillQty", dtypes.int64, lambda o: o.scaleInitFillQty),
        ("ScaleRandomPercent", dtypes.bool_, lambda o: o.scaleRandomPercent),
        ("ScaleTable", dtypes.string, lambda o: o.scaleTable),

        # HEDGE ORDERS
        ("HedgeType", dtypes.string, lambda o: map_values(o.hedgeType, hedge_type)),
        ("HedgeParam", dtypes.string, lambda o: o.hedgeParam),

        # Clearing info
        ("Account", dtypes.string, lambda o: o.account),
        ("SettlingFirm", dtypes.string, lambda o: o.settlingFirm),
        ("ClearingAccount", dtypes.string, lambda o: o.clearingAccount),
        ("ClearingIntent", dtypes.string, lambda o: o.clearingIntent),

        # ALGO ORDERS ONLY
        ("AlgoStrategy", dtypes.string, lambda o: o.algoStrategy),

        ("AlgoParams", dtypes.StringSet, lambda o: to_string_set(o.algoParams)),
        ("SmartComboRoutingParams", dtypes.StringSet, lambda o: to_string_set(o.smartComboRoutingParams)),

        ("AlgoId", dtypes.string, lambda o: o.algoId),

        # What-if
        ("WhatIf", dtypes.bool_, lambda o: o.whatIf),

        # Not Held
        ("NotHeld", dtypes.bool_, lambda o: o.notHeld),
        ("Solicited", dtypes.bool_, lambda o: o.solicited),

        # models
        ("ModelCode", dtypes.string, lambda o: o.modelCode),

        # order combo legs

        ("OrderComboLegs", dtypes.StringSet, lambda o: to_string_set(o.orderComboLegs)),

        ("OrderMiscOptions", dtypes.StringSet, lambda o: to_string_set(o.orderMiscOptions)),

        # VER PEG2BENCH fields:
        ("ReferenceContractId", dtypes.int64, lambda o: o.referenceContractId),
        ("PeggedChangeAmount", dtypes.float64, lambda o: o.peggedChangeAmount),
        ("IsPeggedChangeAmountDecrease", dtypes.bool_, lambda o: o.isPeggedChangeAmountDecrease),
        ("ReferenceChangeAmount", dtypes.float64, lambda o: o.referenceChangeAmount),
        ("ReferenceExchangeId", dtypes.string, lambda o: o.referenceExchangeId),
        ("AdjustedOrderType", dtypes.string, lambda o: o.adjustedOrderType),

        ("TriggerPrice", dtypes.float64, lambda o: o.triggerPrice),
        ("AdjustedStopPrice", dtypes.float64, lambda o: o.adjustedStopPrice),
        ("AdjustedStopLimitPrice", dtypes.float64, lambda o: o.adjustedStopLimitPrice),
        ("AdjustedTrailingAmount", dtypes.float64, lambda o: o.adjustedTrailingAmount),
        ("AdjustableTrailingUnit", dtypes.int64, lambda o: o.adjustableTrailingUnit),
        ("LmtPriceOffset", dtypes.float64, lambda o: o.lmtPriceOffset),

        ("Conditions", dtypes.StringSet, lambda o: to_string_set(o.conditions)),
        ("ConditionsCancelOrder", dtypes.bool_, lambda o: o.conditionsCancelOrder),
        ("ConditionsIgnoreRth", dtypes.bool_, lambda o: o.conditionsIgnoreRth),

        # ext operator
        ("ExtOperator", dtypes.string, lambda o: o.extOperator),

        # native cash quantity
        ("CashQty", dtypes.float64, lambda o: o.cashQty),

        ("Mifid2DecisionMaker", dtypes.string, lambda o: o.mifid2DecisionMaker),
        ("Mifid2DecisionAlgo", dtypes.string, lambda o: o.mifid2DecisionAlgo),
        ("Mifid2ExecutionTrader", dtypes.string, lambda o: o.mifid2ExecutionTrader),
        ("Mifid2ExecutionAlgo", dtypes.string, lambda o: o.mifid2ExecutionAlgo),

        ("DontUseAutoPriceForHedge", dtypes.bool_, lambda o: o.dontUseAutoPriceForHedge),

        ("IsOmsContainer", dtypes.bool_, lambda o: o.isOmsContainer),

        ("DiscretionaryUpToLimitPrice", dtypes.bool_, lambda o: o.discretionaryUpToLimitPrice),

        ("AutoCancelDate", dtypes.string, lambda o: o.autoCancelDate),
        ("FilledQuantity", dtypes.float64, lambda o: o.filledQuantity),
        ("RefFuturesConId", dtypes.int64, lambda o: o.refFuturesConId),
        ("AutoCancelParent", dtypes.bool_, lambda o: o.autoCancelParent),
        ("Shareholder", dtypes.string, lambda o: o.shareholder),
        ("ImbalanceOnly", dtypes.bool_, lambda o: o.imbalanceOnly),
        ("RouteMarketableToBbo", dtypes.bool_, lambda o: o.routeMarketableToBbo),
        ("ParentPermId", dtypes.int64, lambda o: o.parentPermId),

        ("UsePriceMgmtAlgo", dtypes.bool_, lambda o: o.usePriceMgmtAlgo),

        # soft dollars
        ("SoftDollarTier", dtypes.string, lambda o: to_string_val(o.softDollarTier)),
    ]


logger_order = IbComplexTypeLogger("Order", _details_order())


####

def _details_order_state() -> List[Tuple]:
    """ Details for logging OrderState. """

    return [
        ("Status", dtypes.string, lambda os: os.status),

        ("InitMarginBefore", dtypes.string, lambda os: os.initMarginBefore),
        ("MaintMarginBefore", dtypes.string, lambda os: os.maintMarginBefore),
        ("EquityWithLoanBefore", dtypes.string, lambda os: os.equityWithLoanBefore),
        ("InitMarginChange", dtypes.string, lambda os: os.initMarginChange),
        ("MaintMarginChange", dtypes.string, lambda os: os.maintMarginChange),
        ("EquityWithLoanChange", dtypes.string, lambda os: os.equityWithLoanChange),
        ("InitMarginAfter", dtypes.string, lambda os: os.initMarginAfter),
        ("MaintMarginAfter", dtypes.string, lambda os: os.maintMarginAfter),
        ("EquityWithLoanAfter", dtypes.string, lambda os: os.equityWithLoanAfter),

        ("Commission", dtypes.float64, lambda os: os.commission),
        ("MinCommission", dtypes.float64, lambda os: os.minCommission),
        ("MaxCommission", dtypes.float64, lambda os: os.maxCommission),
        ("CommissionCurrency", dtypes.string, lambda os: os.commissionCurrency),
        ("WarningText", dtypes.string, lambda os: os.warningText),
        ("CompletedTime", dtypes.string, lambda os: os.completedTime),
        ("CompletedStatus", dtypes.string, lambda os: os.completedStatus),
    ]


logger_order_state = IbComplexTypeLogger("OrderState", _details_order_state())


####

def _details_execution() -> List[Tuple]:
    """ Details for logging Execution. """

    return [
        ("ExecId", dtypes.string, lambda e: e.execId),
        ("Timestamp", dtypes.Instant, lambda e: ib_to_j_instant(e.time)),
        ("AcctNumber", dtypes.string, lambda e: e.acctNumber),
        ("Exchange", dtypes.string, lambda e: e.exchange),
        ("Side", dtypes.string, lambda e: e.side),
        ("Shares", dtypes.float64, lambda e: e.shares),
        ("Price", dtypes.float64, lambda e: e.price),
        ("PermId", dtypes.int64, lambda e: e.permId),
        ("ClientId", dtypes.int64, lambda e: e.clientId),
        ("OrderId", dtypes.int64, lambda e: e.orderId),
        ("Liquidation", dtypes.int64, lambda e: e.liquidation),
        ("CumQty", dtypes.float64, lambda e: e.cumQty),
        ("AvgPrice", dtypes.float64, lambda e: e.avgPrice),
        ("OrderRef", dtypes.string, lambda e: e.orderRef),
        ("EvRule", dtypes.string, lambda e: e.evRule),
        ("EvMultiplier", dtypes.float64, lambda e: e.evMultiplier),
        ("ModelCode", dtypes.string, lambda e: e.modelCode),
        ("LastLiquidity", dtypes.int64, lambda e: e.lastLiquidity),
    ]


logger_execution = IbComplexTypeLogger("Execution", _details_execution())

####

def _details_commission_report() -> List[Tuple]:
    """ Details for logging CommissionReport. """

    def format_yield_redemption_date(date: int) -> Optional[str]:
        if date == 0:
            return None

        # YYYYMMDD format
        d = date % 100
        m = int((date / 100) % 100)
        y = int(date / 10000)
        return f"{y:04}-{m:02}-{d:02}"

    def map_null_value(value: float) -> Optional[float]:

        if value == sys.float_info.max:
            return None

        return value


    return [
        ("ExecId", dtypes.string, lambda cr: cr.execId),
        ("Commission", dtypes.float64, lambda cr: cr.commission),
        ("Currency", dtypes.string, lambda cr: cr.currency),
        ("RealizedPNL", dtypes.float64, lambda cr: map_null_value(cr.realizedPNL)),
        ("Yield", dtypes.float64, lambda cr: map_null_value(cr.yield_)),
        ("YieldRedemptionDate", dtypes.string, lambda cr: format_yield_redemption_date(cr.yieldRedemptionDate)),
    ]


logger_commission_report = IbComplexTypeLogger("CommissionReport", _details_commission_report())


####

def _details_news_provider() -> List[Tuple]:
    """ Details for logging NewsProvider. """

    return [
        ("Code", dtypes.string, lambda np: np.code),
        ("Name", dtypes.string, lambda np: np.name),
    ]


logger_news_provider = IbComplexTypeLogger("NewsProvider", _details_news_provider())

####
