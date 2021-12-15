import logging
from typing import List

from deephaven import DynamicTableWriter, Types as dht
from ibapi.contract import Contract
from ibapi.wrapper import EWrapper

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
                                                 [dht.int64, dht.int64, dht.string, dht.string])

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

    def managedAccounts(self, accountsList: str):
        EWrapper.managedAccounts(self, accountsList)

        for account in accountsList.split(","):
            self._client.reqAccountUpdates(subscribe=True, acctCode=account)

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

    def accountSummary(self, reqId: int, account: str, tag: str, value: str, currency: str):
        EWrapper.accountSummary(self, reqId, account, tag, value, currency)
        self.account_summary.logRow(reqId, account, tag, value, currency)

    def position(self, account: str, contract: Contract, position: float, avgCost: float):
        EWrapper.position(account, contract, position, avgCost)
        self.positions.logRow(account, *_IbListener._contract_vals(contract), position, avgCost)

    def updateNewsBulletin(self, msgId: int, msgType: int, newsMessage: str, originExch: str):
        EWrapper.updateNewsBulletin(msgId, msgType, newsMessage, originExch)
        self.news_bulletins.logRow(msgId, msgType, newsMessage, originExch)
