import logging
from typing import List

from deephaven import DynamicTableWriter, Types as dht
from ibapi.commission_report import CommissionReport
from ibapi.common import ListOfNewsProviders
from ibapi.contract import Contract
from ibapi.execution import Execution, ExecutionFilter
from ibapi.wrapper import EWrapper
from ibapi import news

from ._client import _IbClient

logging.basicConfig(level=logging.DEBUG)


# TODO: no users need to see this
class _IbListener(EWrapper):
    """Listener for data from IB."""

    def __init__(self):
        EWrapper.__init__(self)
        self._client = None
        self.account_value = DynamicTableWriter(["Account", "Currency", "Key", "Value"],
                                                [dht.string, dht.string, dht.string, dht.string])
        self.portfolio = DynamicTableWriter(
            ["Account", *_IbListener._contract_names(), "Position", "MarketPrice", "MarketValue", "AvgCost",
             "UnrealizedPnl", "RealizedPnl"],
            [dht.string, *_IbListener._contract_types(), dht.float64, dht.float64, dht.float64, dht.float64,
             dht.float64, dht.float64])

        self.account_summary = DynamicTableWriter(["ReqId", "Account", "Tag", "Value", "Currency"],
                                                  [dht.int64, dht.string, dht.string, dht.string, dht.string])

        self.positions = DynamicTableWriter(["Account", *_IbListener._contract_names(), "Position", "AvgCost"],
                                            [dht.string, *_IbListener._contract_types(), dht.float64, dht.float64])

        self.news_bulletins = DynamicTableWriter(["MsgId", "MsgType", "Message", "OriginExch"],
                                                 [dht.int64, dht.string, dht.string, dht.string])

        self.exec_details = DynamicTableWriter(["ReqId", "Time", "Account", *_IbListener._contract_names(),
                                                "Exchange", "Side", "Shares", "Price",
                                                "CumQty", "AvgPrice", "Liquidation",
                                                "EvRule", "EvMultiplier", "ModelCode", "LastLiquidity"
                                                                                       "ExecId", "PermId", "ClientId",
                                                "OrderId", "OrderRef"],
                                               [dht.int64, dht.string, dht.string, *_IbListener._contract_types(),
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

    @staticmethod
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

    @staticmethod
    def _contract_types() -> List:
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

    @staticmethod
    def _contract_vals(contract: Contract) -> List:
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
        self.portfolio.logRow(accountName, *_IbListener._contract_vals(contract), position, marketPrice, marketValue,
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
        self.positions.logRow(account, *_IbListener._contract_vals(contract), position, avgCost)

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
        self.exec_details.logRow(reqId, execution.time, execution.acctNumber, *_IbListener._contract_vals(contract),
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

    # def completedOrder(self, contract:Contract, order:Order, orderState:OrderState):
    #
    #     ***
    #
    #     """This function is called to feed in completed orders.
    #
    #     contract: Contract - The Contract class attributes describe the contract.
    #     order: Order - The Order class gives the details of the completed order.
    #     orderState: OrderState - The orderState class includes completed order status details."""
    #
    #     self.logAnswer(current_fn_name(), vars())
    #
    # def completedOrdersEnd(self):
    #     # do not ned to implement
    #     EWrapper.completedOrdersEnd(self)
