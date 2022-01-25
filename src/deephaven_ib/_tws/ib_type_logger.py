"""Functionality for logging IB types to Deephaven tables."""

import sys
from typing import Any, List, Tuple, Dict, Callable, Union

# noinspection PyPep8Naming
from deephaven import Types as dht

from .._internal.tablewriter import map_values, to_string_val, to_string_set
from ..time import unix_sec_to_dh_datetime, ib_to_dh_datetime


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
        ("AccountID", dht.string, lambda fc: fc.accountID),
        ("FamilyCode", dht.string, lambda fc: fc.familyCodeStr),
    ]


logger_family_code = IbComplexTypeLogger("FamilyCode", _details_family_code())


####

def _details_contract() -> List[Tuple]:
    """ Details for logging Contract. """

    def map_right(right: str) -> Union[str, None]:
        if right == "?":
            return None

        return right

    return [
        ("ContractId", dht.int32, lambda contract: contract.conId),
        ("SecId", dht.string, lambda contract: contract.secId),
        ("SecIdType", dht.string, lambda contract: contract.secIdType),
        ("SecType", dht.string, lambda contract: contract.secType),
        ("Symbol", dht.string, lambda contract: contract.symbol),
        ("LocalSymbol", dht.string, lambda contract: contract.localSymbol),
        ("TradingClass", dht.string, lambda contract: contract.tradingClass),
        ("Currency", dht.string, lambda contract: contract.currency),
        ("Exchange", dht.string, lambda contract: contract.exchange),
        ("PrimaryExchange", dht.string, lambda contract: contract.primaryExchange),
        ("LastTradeDateOrContractMonth", dht.string, lambda contract: contract.lastTradeDateOrContractMonth),
        ("Strike", dht.float64, lambda contract: float(contract.strike)),
        ("Right", dht.string, lambda contract: map_right(contract.right)),
        ("Multiplier", dht.string, lambda contract: contract.multiplier),

        # combos
        ("ComboLegsDescrip", dht.string, lambda contract: contract.comboLegsDescrip),
        ("ComboLegs", dht.stringset, lambda contract: to_string_set(contract.comboLegs)),
        ("DeltaNeutralContract", dht.string, lambda contract: to_string_val(contract.deltaNeutralContract)),
    ]


logger_contract = IbComplexTypeLogger("Contract", _details_contract())


####

def _details_contract_details() -> List[Tuple]:
    """Details for logging ContractDetails."""

    def map_null_int(value: int) -> Union[int, None]:

        if value == 2147483647:
            return None

        return value

    def map_sec_id_list(value):
        if not value:
            return None

        return to_string_set([f"{v.tag}={v.value}" for v in value])

    return [
        *_include_details(_details_contract(), lambda cd: cd.contract),
        ("MarketName", dht.string, lambda cd: cd.marketName),
        ("MinTick", dht.float64, lambda cd: cd.minTick),
        ("OrderTypes", dht.stringset, lambda cd: to_string_set(cd.orderTypes.split(","))),
        ("ValidExchanges", dht.stringset, lambda cd: to_string_set(cd.validExchanges.split(","))),
        ("PriceMagnifier", dht.int32, lambda cd: cd.priceMagnifier),
        ("UnderConId", dht.int32, lambda cd: cd.underConId),
        ("LongName", dht.string, lambda cd: cd.longName),
        ("ContractMonth", dht.string, lambda cd: cd.contractMonth),
        ("Industry", dht.string, lambda cd: cd.industry),
        ("Category", dht.string, lambda cd: cd.category),
        ("SubCategory", dht.string, lambda cd: cd.subcategory),
        ("TimeZoneId", dht.string, lambda cd: cd.timeZoneId),
        ("TradingHours", dht.stringset, lambda cd: to_string_set(cd.tradingHours.split(";"))),
        ("LiquidHours", dht.stringset, lambda cd: to_string_set(cd.liquidHours.split(";"))),
        ("EvRule", dht.string, lambda cd: cd.evRule),
        ("EvMultiplier", dht.int32, lambda cd: cd.evMultiplier),
        ("MdSizeMultiplier", dht.int32, lambda cd: cd.mdSizeMultiplier),
        ("AggGroup", dht.int32, lambda cd: map_null_int(cd.aggGroup)),
        ("UnderSymbol", dht.string, lambda cd: cd.underSymbol),
        ("UnderSecType", dht.string, lambda cd: cd.underSecType),
        ("MarketRuleIds", dht.stringset, lambda cd: to_string_set(cd.marketRuleIds.split(","))),
        ("SecIdList", dht.stringset, lambda cd: map_sec_id_list(cd.secIdList)),
        ("RealExpirationDate", dht.string, lambda cd: cd.realExpirationDate),
        ("LastTradeTime", dht.string, lambda cd: cd.lastTradeTime),
        ("StockType", dht.string, lambda cd: cd.stockType),
        # BOND values
        ("CUSIP", dht.string, lambda cd: cd.cusip),
        ("Ratings", dht.string, lambda cd: cd.ratings),
        ("DescAppend", dht.string, lambda cd: cd.descAppend),
        ("BondType", dht.string, lambda cd: cd.bondType),
        ("CouponType", dht.string, lambda cd: cd.couponType),
        ("Callable", dht.bool_, lambda cd: cd.callable),
        ("Putable", dht.bool_, lambda cd: cd.putable),
        ("Coupon", dht.int32, lambda cd: cd.coupon),
        ("Convertible", dht.bool_, lambda cd: cd.convertible),
        ("Maturity", dht.string, lambda cd: cd.maturity),
        # TODO: convert date time?  Values are not provided in TWS, and the format is not documented.
        ("IssueDate", dht.string, lambda cd: cd.issueDate),
        # TODO: convert date time?  Values are not provided in TWS, and the format is not documented.
        ("NextOptionDate", dht.string, lambda cd: cd.nextOptionDate),
        # TODO: convert date time?  Values are not provided in TWS, and the format is not documented.
        ("NextOptionType", dht.string, lambda cd: cd.nextOptionType),
        ("NextOptionPartial", dht.bool_, lambda cd: cd.nextOptionPartial),
        ("Notes", dht.string, lambda cd: cd.notes),
    ]


logger_contract_details = IbComplexTypeLogger("ContractDetails", _details_contract_details())


####

def _details_price_increment() -> List[Tuple]:
    """Details for logging PriceIncrement."""

    return [
        ("LowEdge", dht.float64, lambda pi: pi.lowEdge),
        ("Increment", dht.float64, lambda pi: pi.increment),
    ]


logger_price_increment = IbComplexTypeLogger("PriceIncrement", _details_price_increment())


####

def _details_bar_data() -> List[Tuple]:
    """ Details for logging BarData. """

    def map_null(val):
        if val <= 0:
            return None

        return val

    return [
        ("Timestamp", dht.datetime, lambda bd: unix_sec_to_dh_datetime(int(bd.date))),
        ("Open", dht.float64, lambda bd: bd.open),
        ("High", dht.float64, lambda bd: bd.high),
        ("Low", dht.float64, lambda bd: bd.low),
        ("Close", dht.float64, lambda bd: bd.close),
        ("Volume", dht.int32, lambda bd: map_null(bd.volume)),
        ("BarCount", dht.int32, lambda bd: map_null(bd.barCount)),
        ("Average", dht.float64, lambda bd: map_null(bd.average)),
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
        ("Timestamp", dht.datetime, lambda bd: unix_sec_to_dh_datetime(bd.time)),
        ("TimestampEnd", dht.datetime, lambda bd: unix_sec_to_dh_datetime(bd.endTime)),
        ("Open", dht.float64, lambda bd: bd.open_),
        ("High", dht.float64, lambda bd: bd.high),
        ("Low", dht.float64, lambda bd: bd.low),
        ("Close", dht.float64, lambda bd: bd.close),
        ("Volume", dht.int32, lambda bd: map_null(bd.volume)),
        ("WAP", dht.float64, lambda bd: map_null(bd.wap)),
        ("Count", dht.int32, lambda bd: map_null(bd.count)),
    ]


logger_real_time_bar_data = IbComplexTypeLogger("RealTimeBarData", _details_real_time_bar_data())


####

def _details_tick_attrib() -> List[Tuple]:
    """ Details for logging TickAttrib. """

    return [
        ("CanAutoExecute", dht.bool_, lambda ta: ta.canAutoExecute),
        ("PastLimit", dht.bool_, lambda ta: ta.pastLimit),
        ("PreOpen", dht.bool_, lambda ta: ta.preOpen),
    ]


logger_tick_attrib = IbComplexTypeLogger("TickAttrib", _details_tick_attrib())


###

def _details_tick_attrib_last() -> List[Tuple]:
    """Details for logging TickAttribLast."""

    return [
        ("PastLimit", dht.bool_, lambda ta: ta.pastLimit),
        ("Unreported", dht.bool_, lambda ta: ta.unreported),
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

        return to_string_set(
            [map_values(v.strip(), special_conditions_codes) for v in special_conditions.strip().split(" ")])


    return [
        ("Timestamp", dht.datetime, lambda t: unix_sec_to_dh_datetime(t.time)),
        ("Price", dht.float64, lambda t: t.price),
        ("Size", dht.int32, lambda t: t.size),
        *_include_details(_details_tick_attrib_last(), lambda t: t.tickAttribLast),
        ("Exchange", dht.string, lambda t: t.exchange),
        ("SpecialConditions", dht.stringset, lambda t: map_special_conditions(t.specialConditions))
    ]


logger_hist_tick_last = IbComplexTypeLogger("HistoricalTickLast", _details_historical_tick_last())


####

def _details_tick_attrib_bid_ask() -> List[Tuple]:
    """Details for logging TickAttribBidAsk."""

    return [
        ("BidPastLow", dht.bool_, lambda ta: ta.bidPastLow),
        ("AskPastHigh", dht.bool_, lambda ta: ta.askPastHigh),
    ]


logger_tick_attrib_bid_ask = IbComplexTypeLogger("TickAttribBidAsk", _details_tick_attrib_bid_ask())


####

def _details_historical_tick_bid_ask() -> List[Tuple]:
    """Details for logging HistoricalTickBidAsk."""

    return [
        ("Timestamp", dht.datetime, lambda t: unix_sec_to_dh_datetime(t.time)),
        ("BidPrice", dht.float64, lambda t: t.priceBid),
        ("AskPrice", dht.float64, lambda t: t.priceAsk),
        ("BidSize", dht.int32, lambda t: t.sizeBid),
        ("AskSize", dht.int32, lambda t: t.sizeAsk),
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
        ("OrderId", dht.int32, lambda o: o.orderId),
        ("ClientId", dht.int32, lambda o: o.clientId),
        ("PermId", dht.int32, lambda o: o.permId),

        # main order fields
        ("Action", dht.string, lambda o: o.action),
        ("TotalQuantity", dht.float64, lambda o: o.totalQuantity),
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
        ("ParentId", dht.int32, lambda o: o.parentId),
        ("BlockOrder", dht.bool_, lambda o: o.blockOrder),
        ("SweepToFill", dht.bool_, lambda o: o.sweepToFill),
        ("DisplaySize", dht.int32, lambda o: o.displaySize),
        ("TriggerMethod", dht.string, lambda o: map_values(o.triggerMethod, trigger_methods)),
        ("OutsideRth", dht.bool_, lambda o: o.outsideRth),
        ("Hidden", dht.bool_, lambda o: o.hidden),
        ("GoodAfterTime", dht.string, lambda o: o.goodAfterTime),
        ("GoodTillDate", dht.string, lambda o: o.goodTillDate),
        ("Rule80A", dht.string, lambda o: map_values(o.rule80A, rule80_values)),
        ("AllOrNone", dht.bool_, lambda o: o.allOrNone),
        ("MinQty", dht.int32, lambda o: o.minQty),
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
        ("ExemptCode", dht.int32, lambda o: o.exemptCode),

        # SMART routing only
        ("DiscretionaryAmt", dht.float64, lambda o: o.discretionaryAmt),
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
        ("DeltaNeutralConId", dht.int32, lambda o: o.deltaNeutralConId),
        ("DeltaNeutralSettlingFirm", dht.string, lambda o: o.deltaNeutralSettlingFirm),
        ("DeltaNeutralClearingAccount", dht.string, lambda o: o.deltaNeutralClearingAccount),
        ("DeltaNeutralClearingIntent", dht.string, lambda o: o.deltaNeutralClearingIntent),
        ("DeltaNeutralOpenClose", dht.string, lambda o: o.deltaNeutralOpenClose),
        ("DeltaNeutralShortSale", dht.bool_, lambda o: o.deltaNeutralShortSale),
        ("DeltaNeutralShortSaleSlot", dht.int32, lambda o: o.deltaNeutralShortSaleSlot),
        ("DeltaNeutralDesignatedLocation", dht.string, lambda o: o.deltaNeutralDesignatedLocation),
        ("ContinuousUpdate", dht.bool_, lambda o: o.continuousUpdate),
        ("ReferencePriceType", dht.string, lambda o: map_values(o.referencePriceType, reference_price_type)),

        # COMBO ORDERS ONLY
        ("BasisPoints", dht.float64, lambda o: o.basisPoints),
        ("BasisPointsType", dht.int32, lambda o: o.basisPointsType),

        # SCALE ORDERS ONLY
        ("ScaleInitLevelSize", dht.int32, lambda o: o.scaleInitLevelSize),
        ("ScaleSubsLevelSize", dht.int32, lambda o: o.scaleSubsLevelSize),
        ("ScalePriceIncrement", dht.float64, lambda o: o.scalePriceIncrement),
        ("ScalePriceAdjustValue", dht.float64, lambda o: o.scalePriceAdjustValue),
        ("ScalePriceAdjustInterval", dht.int32, lambda o: o.scalePriceAdjustInterval),
        ("ScaleProfitOffset", dht.float64, lambda o: o.scaleProfitOffset),
        ("ScaleAutoReset", dht.bool_, lambda o: o.scaleAutoReset),
        ("ScaleInitPosition", dht.int32, lambda o: o.scaleInitPosition),
        ("ScaleInitFillQty", dht.int32, lambda o: o.scaleInitFillQty),
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

        ("AlgoParams", dht.stringset, lambda o: to_string_set(o.algoParams)),
        ("SmartComboRoutingParams", dht.stringset, lambda o: to_string_set(o.smartComboRoutingParams)),

        ("AlgoId", dht.string, lambda o: o.algoId),

        # What-if
        ("WhatIf", dht.bool_, lambda o: o.whatIf),

        # Not Held
        ("NotHeld", dht.bool_, lambda o: o.notHeld),
        ("Solicited", dht.bool_, lambda o: o.solicited),

        # models
        ("ModelCode", dht.string, lambda o: o.modelCode),

        # order combo legs

        ("OrderComboLegs", dht.stringset, lambda o: to_string_set(o.orderComboLegs)),

        ("OrderMiscOptions", dht.stringset, lambda o: to_string_set(o.orderMiscOptions)),

        # VER PEG2BENCH fields:
        ("ReferenceContractId", dht.int32, lambda o: o.referenceContractId),
        ("PeggedChangeAmount", dht.float64, lambda o: o.peggedChangeAmount),
        ("IsPeggedChangeAmountDecrease", dht.bool_, lambda o: o.isPeggedChangeAmountDecrease),
        ("ReferenceChangeAmount", dht.float64, lambda o: o.referenceChangeAmount),
        ("ReferenceExchangeId", dht.string, lambda o: o.referenceExchangeId),
        ("AdjustedOrderType", dht.string, lambda o: o.adjustedOrderType),

        ("TriggerPrice", dht.float64, lambda o: o.triggerPrice),
        ("AdjustedStopPrice", dht.float64, lambda o: o.adjustedStopPrice),
        ("AdjustedStopLimitPrice", dht.float64, lambda o: o.adjustedStopLimitPrice),
        ("AdjustedTrailingAmount", dht.float64, lambda o: o.adjustedTrailingAmount),
        ("AdjustableTrailingUnit", dht.int32, lambda o: o.adjustableTrailingUnit),
        ("LmtPriceOffset", dht.float64, lambda o: o.lmtPriceOffset),

        ("Conditions", dht.stringset, lambda o: to_string_set(o.conditions)),
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

        ("DontUseAutoPriceForHedge", dht.bool_, lambda o: o.dontUseAutoPriceForHedge),

        ("IsOmsContainer", dht.bool_, lambda o: o.isOmsContainer),

        ("DiscretionaryUpToLimitPrice", dht.bool_, lambda o: o.discretionaryUpToLimitPrice),

        ("AutoCancelDate", dht.string, lambda o: o.autoCancelDate),
        ("FilledQuantity", dht.float64, lambda o: o.filledQuantity),
        ("RefFuturesConId", dht.int32, lambda o: o.refFuturesConId),
        ("AutoCancelParent", dht.bool_, lambda o: o.autoCancelParent),
        ("Shareholder", dht.string, lambda o: o.shareholder),
        ("ImbalanceOnly", dht.bool_, lambda o: o.imbalanceOnly),
        ("RouteMarketableToBbo", dht.bool_, lambda o: o.routeMarketableToBbo),
        ("ParentPermId", dht.int32, lambda o: o.parentPermId),

        ("UsePriceMgmtAlgo", dht.bool_, lambda o: o.usePriceMgmtAlgo),

        # soft dollars
        ("SoftDollarTier", dht.string, lambda o: to_string_val(o.softDollarTier)),
    ]


logger_order = IbComplexTypeLogger("Order", _details_order())


####

def _details_order_state() -> List[Tuple]:
    """ Details for logging OrderState. """

    return [
        ("Status", dht.string, lambda os: os.status),

        ("InitMarginBefore", dht.string, lambda os: os.initMarginBefore),
        ("MaintMarginBefore", dht.string, lambda os: os.maintMarginBefore),
        ("EquityWithLoanBefore", dht.string, lambda os: os.equityWithLoanBefore),
        ("InitMarginChange", dht.string, lambda os: os.initMarginChange),
        ("MaintMarginChange", dht.string, lambda os: os.maintMarginChange),
        ("EquityWithLoanChange", dht.string, lambda os: os.equityWithLoanChange),
        ("InitMarginAfter", dht.string, lambda os: os.initMarginAfter),
        ("MaintMarginAfter", dht.string, lambda os: os.maintMarginAfter),
        ("EquityWithLoanAfter", dht.string, lambda os: os.equityWithLoanAfter),

        ("Commission", dht.float64, lambda os: os.commission),
        ("MinCommission", dht.float64, lambda os: os.minCommission),
        ("MaxCommission", dht.float64, lambda os: os.maxCommission),
        ("CommissionCurrency", dht.string, lambda os: os.commissionCurrency),
        ("WarningText", dht.string, lambda os: os.warningText),
        ("CompletedTime", dht.string, lambda os: os.completedTime),
        ("CompletedStatus", dht.string, lambda os: os.completedStatus),
    ]


logger_order_state = IbComplexTypeLogger("OrderState", _details_order_state())


####

def _details_execution() -> List[Tuple]:
    """ Details for logging Execution. """

    return [
        ("ExecId", dht.string, lambda e: e.execId),
        ("Timestamp", dht.datetime, lambda e: ib_to_dh_datetime(e.time)),
        ("AcctNumber", dht.string, lambda e: e.acctNumber),
        ("Exchange", dht.string, lambda e: e.exchange),
        ("Side", dht.string, lambda e: e.side),
        ("Shares", dht.float64, lambda e: e.shares),
        ("Price", dht.float64, lambda e: e.price),
        ("PermId", dht.int32, lambda e: e.permId),
        ("ClientId", dht.int32, lambda e: e.clientId),
        ("OrderId", dht.int32, lambda e: e.orderId),
        ("Liquidation", dht.int32, lambda e: e.liquidation),
        ("CumQty", dht.float64, lambda e: e.cumQty),
        ("AvgPrice", dht.float64, lambda e: e.avgPrice),
        ("OrderRef", dht.string, lambda e: e.orderRef),
        ("EvRule", dht.string, lambda e: e.evRule),
        ("EvMultiplier", dht.float64, lambda e: e.evMultiplier),
        ("ModelCode", dht.string, lambda e: e.modelCode),
        ("LastLiquidity", dht.int32, lambda e: e.lastLiquidity),
    ]


logger_execution = IbComplexTypeLogger("Execution", _details_execution())

####

def _details_commission_report() -> List[Tuple]:
    """ Details for logging CommissionReport. """

    def format_yield_redemption_date(date: int) -> Union[str, None]:
        if date == 0:
            return None

        # YYYYMMDD format
        d = date % 100
        m = int((date / 100) % 100)
        y = int(date / 10000)
        return f"{y:04}-{m:02}-{d:02}"

    def map_null_value(value: float) -> Union[float, None]:

        if value == sys.float_info.max:
            return None

        return value


    return [
        ("ExecId", dht.string, lambda cr: cr.execId),
        ("Commission", dht.float64, lambda cr: cr.commission),
        ("Currency", dht.string, lambda cr: cr.currency),
        ("RealizedPNL", dht.float64, lambda cr: map_null_value(cr.realizedPNL)),
        ("Yield", dht.float64, lambda cr: map_null_value(cr.yield_)),
        ("YieldRedemptionDate", dht.string, lambda cr: format_yield_redemption_date(cr.yieldRedemptionDate)),
    ]


logger_commission_report = IbComplexTypeLogger("CommissionReport", _details_commission_report())


####

def _details_news_provider() -> List[Tuple]:
    """ Details for logging NewsProvider. """

    return [
        ("Code", dht.string, lambda np: np.code),
        ("Name", dht.string, lambda np: np.name),
    ]


logger_news_provider = IbComplexTypeLogger("NewsProvider", _details_news_provider())

####
