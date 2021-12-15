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

    def connect(self, client: _IbClient):
        self._client = client

        client.reqManagedAccts()

        # client.reqAccountSummary()
        # client.reqAccountUpdates() -> account value and portfolio
        # client.reqAllOpenOrders()
        # client.reqContractDetails()
        # client.reqHistoricalData()
        # client.reqHistoricalNews()
        # client.reqHistoricalTicks()
        # client.reqIds()
        # client.reqMarketDataType()
        # client.reqMarketRule()
        # client.reqMatchingSymbols()
        # client.reqNewsArticle()
        # client.reqNewsBulletins()
        # client.reqNewsProviders()
        # client.reqFundamentalData()
        # client.reqOpenOrders()
        # client.reqAutoOpenOrders()
        # client.reqCompletedOrders()
        # client.reqExecutions()
        # client.reqFamilyCodes()
        # client.reqGlobalCancel()
        # client.reqMktData()
        # client.reqContractDetails()
        # client.reqPnL()
        # client.reqPositions()
        # client.reqPositionsMulti()
        # client.reqRealTimeBars()
        # client.reqTickByTickData()

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
