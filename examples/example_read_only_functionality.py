from typing import Dict

from deephaven.time import to_datetime
from ibapi.contract import Contract
from ibapi.order import Order

import deephaven_ib as dhib

print("==============================================================================================================")
print("==== Create a client and connect.")
print("==== ** Accept the connection in TWS **")
print("==============================================================================================================")

client = dhib.IbSessionTws(host="host.docker.internal", port=7497, client_id=0, download_short_rates=False, read_only=True)
print(f"IsConnected: {client.is_connected()}")

client.connect()
print(f"IsConnected: {client.is_connected()}")

print("==============================================================================================================")
print("==== Get registered contracts for all contract types.")
print("==== See https://interactivebrokers.github.io/tws-api/basic_contracts.html for details on supported contract types.")
print("==============================================================================================================")


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
    contract.symbol = "VIX"
    contract.secType = "IND"
    contract.currency = "USD"
    contract.exchange = "CBOE"
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
    contract.lastTradeDateOrContractMonth = "202209"
    rst["future_1"] = contract

    contract = Contract()
    contract.secType = "FUT"
    contract.exchange = "GLOBEX"
    contract.currency = "USD"
    contract.localSymbol = "MESU2"
    rst["future_2"] = contract

    contract = Contract()
    contract.symbol = "DAX"
    contract.secType = "FUT"
    contract.exchange = "EUREX"
    contract.currency = "EUR"
    contract.lastTradeDateOrContractMonth = "202209"
    contract.multiplier = "1"
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
    contract.lastTradeDateOrContractMonth = "20230120"
    contract.strike = 110
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
    contract.lastTradeDateOrContractMonth = "202209"
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

    # contract = Contract()
    # contract.localSymbol = "B881G"
    # contract.secType = "IOPT"
    # contract.exchange = "SBF"
    # contract.currency = "EUR"
    # rst["dutchwarrant_1"] = contract

    return rst


contracts = get_contracts()

for name, contract in contracts.items():
    print(f"{name} {contract}")
    rc = client.get_registered_contract(contract)
    print(rc)

registered_contracts = {name: client.get_registered_contract(contract) for name, contract in contracts.items()}

print("==============================================================================================================")
print("==== Request account pnl.")
print("==============================================================================================================")

client.request_account_pnl()

print("==============================================================================================================")
print("==== Request contracts matching.")
print("==============================================================================================================")

client.request_contracts_matching("AM")

print("==============================================================================================================")
print("==== Request news data.")
print("==============================================================================================================")

contract = Contract()
contract.symbol = "GOOG"
contract.secType = "STK"
contract.currency = "USD"
contract.exchange = "SMART"

rc = client.get_registered_contract(contract)
print(contract)

start = to_datetime("2021-01-01T00:00:00 NY")
end = to_datetime("2021-01-10T00:00:00 NY")
client.request_news_historical(rc, start=start, end=end)

client.request_news_article(provider_code="BRFUPDN", article_id="BRFUPDN$107d53ea")

print("==============================================================================================================")
print("==== Set market data type.")
print("==============================================================================================================")

# client.set_market_data_type(dhib.MarketDataType.DELAYED)
client.set_market_data_type(dhib.MarketDataType.REAL_TIME)

print("==============================================================================================================")
print("==== Request bars.")
print("==============================================================================================================")

contract = Contract()
contract.symbol = "IBKR"
contract.secType = "STK"
contract.currency = "USD"
contract.exchange = "SMART"

rc = client.get_registered_contract(contract)
print(contract)

client.request_bars_historical(rc, duration=dhib.Duration.days(10), bar_size=dhib.BarSize.MIN_5,
                               bar_type=dhib.BarDataType.MIDPOINT)
client.request_bars_historical(rc, duration=dhib.Duration.days(10), bar_size=dhib.BarSize.MIN_5,
                               bar_type=dhib.BarDataType.BID)
client.request_bars_historical(rc, duration=dhib.Duration.days(10), bar_size=dhib.BarSize.MIN_5,
                               bar_type=dhib.BarDataType.ASK)
client.request_bars_historical(rc, duration=dhib.Duration.days(10), bar_size=dhib.BarSize.MIN_5,
                               bar_type=dhib.BarDataType.BID_ASK, keep_up_to_date=False)
client.request_bars_historical(rc, duration=dhib.Duration.days(10), bar_size=dhib.BarSize.MIN_5,
                               bar_type=dhib.BarDataType.HISTORICAL_VOLATILITY, keep_up_to_date=False)
client.request_bars_historical(rc, duration=dhib.Duration.days(10), bar_size=dhib.BarSize.MIN_5,
                               bar_type=dhib.BarDataType.OPTION_IMPLIED_VOLATILITY, keep_up_to_date=False)
client.request_bars_historical(rc, duration=dhib.Duration.days(10), bar_size=dhib.BarSize.MIN_5,
                               bar_type=dhib.BarDataType.TRADES)
client.request_bars_historical(rc, duration=dhib.Duration.days(10), bar_size=dhib.BarSize.MIN_5,
                               bar_type=dhib.BarDataType.ADJUSTED_LAST, keep_up_to_date=False)

client.request_bars_realtime(rc, bar_type=dhib.BarDataType.MIDPOINT)
client.request_bars_realtime(rc, bar_type=dhib.BarDataType.BID)
client.request_bars_realtime(rc, bar_type=dhib.BarDataType.ASK)
client.request_bars_realtime(rc, bar_type=dhib.BarDataType.TRADES)


print("==============================================================================================================")
print("==== Request bars (bonds).")
print("==============================================================================================================")

# enter CUSIP as symbol
contract = Contract()
contract.symbol = "IBCID411964960"
contract.secType = "BOND"
contract.exchange = "SMART"
contract.currency = "USD"

rc = client.get_registered_contract(contract)
print(contract)

client.request_bars_historical(rc, duration=dhib.Duration.days(22), bar_size=dhib.BarSize.DAY_1,
                               bar_type=dhib.BarDataType.YIELD_BID, keep_up_to_date=False)
client.request_bars_historical(rc, duration=dhib.Duration.days(22), bar_size=dhib.BarSize.DAY_1,
                               bar_type=dhib.BarDataType.YIELD_ASK, keep_up_to_date=False)
client.request_bars_historical(rc, duration=dhib.Duration.days(22), bar_size=dhib.BarSize.DAY_1,
                               bar_type=dhib.BarDataType.YIELD_BID_ASK, keep_up_to_date=False)
client.request_bars_historical(rc, duration=dhib.Duration.days(22), bar_size=dhib.BarSize.DAY_1,
                               bar_type=dhib.BarDataType.YIELD_LAST, keep_up_to_date=False)

print("==============================================================================================================")
print("==== Request bars (Crypto).")
print("==============================================================================================================")

contract = Contract()
contract.symbol = "BTC"
contract.secType = "CRYPTO"
contract.exchange = "PAXOS"
contract.currency = "USD"

rc = client.get_registered_contract(c2)
client.request_bars_historical(rc2, duration=dhib.Duration.days(253),
  bar_size=dhib.BarSize.DAY_1,
  bar_type=dhib.BarDataType.AGGTRADES,
  keep_up_to_date = False
)
client.request_bars_realtime(rc2, bar_type=dhib.BarDataType.TRADES)

client.request_bars_historical(rc, duration=dhib.Duration.days(10), bar_size=dhib.BarSize.MIN_5,
                               bar_type=dhib.BarDataType.MIDPOINT)
client.request_bars_historical(rc, duration=dhib.Duration.days(10), bar_size=dhib.BarSize.MIN_5,
                               bar_type=dhib.BarDataType.BID)
client.request_bars_historical(rc, duration=dhib.Duration.days(10), bar_size=dhib.BarSize.MIN_5,
                               bar_type=dhib.BarDataType.ASK)
client.request_bars_historical(rc, duration=dhib.Duration.days(10), bar_size=dhib.BarSize.MIN_5,
                               bar_type=dhib.BarDataType.BID_ASK, keep_up_to_date=False)
client.request_bars_historical(rc, duration=dhib.Duration.days(10), bar_size=dhib.BarSize.MIN_5,
                               bar_type=dhib.BarDataType.AGGTRADES)
client.request_bars_historical(rc, duration=dhib.Duration.days(10), bar_size=dhib.BarSize.MIN_5,
                               bar_type=dhib.BarDataType.ADJUSTED_LAST, keep_up_to_date=False)

client.request_bars_realtime(rc, bar_type=dhib.BarDataType.MIDPOINT)
client.request_bars_realtime(rc, bar_type=dhib.BarDataType.BID)
client.request_bars_realtime(rc, bar_type=dhib.BarDataType.ASK)
client.request_bars_realtime(rc, bar_type=dhib.BarDataType.TRADES)

print("==============================================================================================================")
print("==== Request tick data.")
print("==============================================================================================================")

contract = Contract()
contract.symbol = "GOOG"
contract.secType = "STK"
contract.currency = "USD"
contract.exchange = "SMART"

rc = client.get_registered_contract(contract)
print(contract)

now = to_datetime("2021-01-01T00:00:00 NY")

client.request_tick_data_historical(rc, dhib.TickDataType.MIDPOINT, 100, start=now)
client.request_tick_data_historical(rc, dhib.TickDataType.MIDPOINT, 100, end=now)
client.request_tick_data_realtime(rc, dhib.TickDataType.MIDPOINT)

client.request_tick_data_realtime(rc, dhib.TickDataType.BID_ASK)

client.request_tick_data_historical(rc, dhib.TickDataType.LAST, 100, start=now)
client.request_tick_data_historical(rc, dhib.TickDataType.LAST, 100, end=now)
client.request_tick_data_realtime(rc, dhib.TickDataType.LAST)

print("==============================================================================================================")
print("==== Request market data.")
print("==============================================================================================================")

contract = Contract()
contract.symbol = "GOOG"
contract.secType = "STK"
contract.currency = "USD"
contract.exchange = "SMART"

rc = client.get_registered_contract(contract)
print(contract)

generic_tick_types = [
    dhib.GenericTickType.NEWS,
    dhib.GenericTickType.DIVIDENDS,
    dhib.GenericTickType.AUCTION,
    dhib.GenericTickType.MARK_PRICE,
    dhib.GenericTickType.MARK_PRICE_SLOW,

    dhib.GenericTickType.TRADING_RANGE,

    dhib.GenericTickType.TRADE_LAST_RTH,
    dhib.GenericTickType.TRADE_COUNT,
    dhib.GenericTickType.TRADE_COUNT_RATE,
    dhib.GenericTickType.TRADE_VOLUME,
    dhib.GenericTickType.TRADE_VOLUME_NO_UNREPORTABLE,
    dhib.GenericTickType.TRADE_VOLUME_RATE,
    dhib.GenericTickType.TRADE_VOLUME_SHORT_TERM,

    dhib.GenericTickType.SHORTABLE,
    dhib.GenericTickType.SHORTABLE_SHARES,

    # dhib.GenericTickType.FUTURE_OPEN_INTEREST,
    # dhib.GenericTickType.FUTURE_INDEX_PREMIUM,

    dhib.GenericTickType.OPTION_VOLATILITY_HISTORICAL,
    dhib.GenericTickType.OPTION_VOLATILITY_HISTORICAL_REAL_TIME,
    dhib.GenericTickType.OPTION_VOLATILITY_IMPLIED,
    dhib.GenericTickType.OPTION_VOLUME,
    dhib.GenericTickType.OPTION_VOLUME_AVERAGE,
    dhib.GenericTickType.OPTION_OPEN_INTEREST,

    # dhib.GenericTickType.ETF_NAV_CLOSE,
    # dhib.GenericTickType.ETF_NAV_PRICE,
    # dhib.GenericTickType.ETF_NAV_LAST,
    # dhib.GenericTickType.ETF_NAV_LAST_FROZEN,
    # dhib.GenericTickType.ETF_NAV_RANGE,
    #
    # dhib.GenericTickType.BOND_FACTOR_MULTIPLIER,
]
client.request_market_data(rc, generic_tick_types=generic_tick_types)

print("==============================================================================================================")
print("==== Request option greeks.")
print("==============================================================================================================")

contract = Contract()
contract.symbol = "GOOG"
contract.secType = "OPT"
contract.exchange = "BOX"
contract.currency = "USD"
contract.lastTradeDateOrContractMonth = "20230120"
contract.strike = 110
contract.right = "C"
contract.multiplier = "100"

rc = client.get_registered_contract(contract)
print(contract)

client.request_market_data(rc)

print("==============================================================================================================")
print("==== Orders.")
print("==============================================================================================================")

contract = Contract()
contract.symbol = "GOOG"
contract.secType = "STK"
contract.currency = "USD"
contract.exchange = "SMART"

rc = client.get_registered_contract(contract)
print(contract)

order = Order()
order.account = "DF4943843"
order.action = "BUY"
order.orderType = "LIMIT"
order.totalQuantity = 1
order.lmtPrice = 3000

print("Placing order -- confirm fail: START")
try:
    client.order_place(rc, order)
    raise AssertionError("Operation should not be possible")
except AssertionError as e:
    raise e
except Exception:
    pass
print("Placing order -- confirm fail: END")

order = Order()
order.account = "DF4943843"
order.action = "BUY"
order.orderType = "LIMIT"
order.totalQuantity = 1
order.lmtPrice = 2600

print("Placing order -- confirm fail: START")
try:
    client.order_place(rc, order)
    raise AssertionError("Operation should not be possible")
except AssertionError as e:
    raise e
except Exception:
    pass
print("Placing order -- confirm fail: START")

order = Order()
order.account = "DF4943843"
order.action = "BUY"
order.orderType = "LIMIT"
order.totalQuantity = 1
order.lmtPrice = 2700

print("Placing order -- confirm fail: START")
try:
    req = client.order_place(rc, order)
    raise AssertionError("Operation should not be possible")
except AssertionError as e:
    raise e
except Exception:
    pass
print("Placing order -- confirm fail: END")
# req.cancel()

# client.order_cancel_all()


print("==============================================================================================================")
print("==== Make all tables visible in the UI.")
print("==============================================================================================================")

for k, v in client.tables_raw.items():
    globals()[k] = v

for k, v in client.tables.items():
    globals()[k] = v
