import logging
from typing import Dict

from ibapi.contract import Contract

import deephaven_ib as dhib

logging.basicConfig(level=logging.DEBUG)

client = dhib.IbSessionTws(download_short_rates=False)

print(f"IsConnected: {client.is_connected()}")

client.connect(host="host.docker.internal", port=7497)

print(f"IsConnected: {client.is_connected()}")

for k, v in client.tables.items():
    globals()[k] = v


# for k, v in client.tables2.items():
#     globals()[k] = v


def get_contracts() -> Dict[str, Contract]:
    rst = {}

    # FX Pairs
    contract = Contract()
    contract.symbol = "EUR"
    contract.secType = "CASH"
    contract.currency = "GBP"
    contract.exchange = "IDEALPRO"
    rst["fx_1"] = contract

    # Cryptocurrency
    contract = Contract()
    contract.symbol = "ETH"
    contract.secType = "CRYPTO"
    contract.currency = "USD"
    contract.exchange = "PAXOS"
    rst["crypto_1"] = contract

    # Stock
    contract = Contract()
    contract.symbol = "IBKR"
    contract.secType = "STK"
    contract.currency = "USD"
    # In the API side, NASDAQ is always defined as ISLAND in the exchange field
    contract.exchange = "ISLAND"
    rst["stock_1"] = contract

    contract = Contract()
    contract.symbol = "MSFT"
    contract.secType = "STK"
    contract.currency = "USD"
    contract.exchange = "SMART"
    # Specify the Primary Exchange attribute to avoid contract ambiguity
    # (there is an ambiguity because there is also a MSFT contract with primary exchange = "AEB")
    contract.primaryExchange = "ISLAND"
    rst["stock_2"] = contract

    # Index

    contract = Contract()
    contract.symbol = "DAX"
    contract.secType = "IND"
    contract.currency = "EUR"
    contract.exchange = "DTB"
    rst["index_1"] = contract

    # CFD

    contract = Contract()
    contract.symbol = "IBDE30"
    contract.secType = "CFD"
    contract.currency = "EUR"
    contract.exchange = "SMART"
    rst["cfd_1"] = contract

    # Futures

    contract = Contract()
    contract.symbol = "ES"
    contract.secType = "FUT"
    contract.exchange = "GLOBEX"
    contract.currency = "USD"
    contract.lastTradeDateOrContractMonth = "202203"
    rst["future_1"] = contract

    contract = Contract()
    contract.secType = "FUT"
    contract.exchange = "GLOBEX"
    contract.currency = "USD"
    contract.localSymbol = "ESH2"
    rst["future_2"] = contract

    contract = Contract()
    contract.symbol = "DAX"
    contract.secType = "FUT"
    contract.exchange = "DTB"
    contract.currency = "EUR"
    contract.lastTradeDateOrContractMonth = "202203"
    contract.multiplier = "5"
    rst["future_3"] = contract

    contract = Contract()
    contract.symbol = "ES"
    contract.secType = "CONTFUT"
    contract.exchange = "GLOBEX"
    rst["future_4"] = contract

    contract = Contract()
    contract.symbol = "ES"
    contract.secType = "FUT+CONTFUT"
    contract.exchange = "GLOBEX"
    rst["future_5"] = contract

    # Options

    contract = Contract()
    contract.symbol = "GOOG"
    contract.secType = "OPT"
    contract.exchange = "BOX"
    contract.currency = "USD"
    contract.lastTradeDateOrContractMonth = "20220318"
    contract.strike = 2800
    contract.right = "C"
    contract.multiplier = "100"
    rst["option_1"] = contract

    # contract = Contract()
    # contract.symbol = "SANT"
    # contract.secType = "OPT"
    # contract.exchange = "MEFFRV"
    # contract.currency = "EUR"
    # contract.lastTradeDateOrContractMonth = "20190621"
    # contract.strike = 7.5
    # contract.right = "C"
    # contract.multiplier = "100"
    # contract.tradingClass = "SANEU"
    # rst["option_2"] = contract

    # contract = Contract()
    # # Watch out for the spaces within the local symbol!
    # contract.localSymbol = "C BMW  JUL 20  4800"
    # contract.secType = "OPT"
    # contract.exchange = "DTB"
    # contract.currency = "EUR"
    # rst["option_3"] = contract

    # Futures Options

    contract = Contract()
    contract.symbol = "ES"
    contract.secType = "FOP"
    contract.exchange = "GLOBEX"
    contract.currency = "USD"
    contract.lastTradeDateOrContractMonth = "202203"
    contract.strike = 4700
    contract.right = "C"
    contract.multiplier = "50"
    rst["futureoption_1"] = contract

    # Bonds

    contract = Contract()
    # enter CUSIP as symbol
    contract.symbol = "912828C57"
    contract.secType = "BOND"
    contract.exchange = "SMART"
    contract.currency = "USD"
    rst["bond_1"] = contract

    contract = Contract()
    contract.conId = 147554578
    contract.exchange = "SMART"
    rst["bond_2"] = contract

    # Mutual Funds

    contract = Contract()
    contract.symbol = "VINIX"
    contract.secType = "FUND"
    contract.exchange = "FUNDSERV"
    contract.currency = "USD"
    rst["mutualfund_1"] = contract

    # Commodities

    contract = Contract()
    contract.symbol = "XAUUSD"
    contract.secType = "CMDTY"
    contract.exchange = "SMART"
    contract.currency = "USD"
    rst["commodity_1"] = contract

    # Standard warrants

    contract = Contract()
    contract.symbol = "OXY"
    contract.secType = "WAR"
    contract.exchange = "SMART"
    contract.currency = "USD"
    contract.lastTradeDateOrContractMonth = "20270803"
    contract.strike = 22.0
    contract.right = "C"
    contract.multiplier = "1"
    rst["standardwarrant_1"] = contract

    # Dutch warrants and structured products

    contract = Contract()
    contract.localSymbol = "PJ07S"
    contract.secType = "IOPT"
    contract.exchange = "SBF"
    contract.currency = "EUR"
    rst["dutchwarrant_1"] = contract

    return rst


contracts = get_contracts()
# registered_contracts = {name: client.get_registered_contract(contract) for name, contract in contracts.items()}

for name, contract in contracts.items():
    print(f"{name} {contract}")
    rc = client.get_registered_contract(contract)
    print(rc)
