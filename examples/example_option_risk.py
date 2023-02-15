# Compute real-time risk scenarios for a portfolio of options

import math
from ibapi.contract import Contract
from deephaven.constants import NULL_DOUBLE
from deephaven.time import to_datetime
from deephaven.plot import Figure
import deephaven_ib as dhib


print("==============================================================================================================")
print("==== ** Accept the connection in TWS **")
print("==============================================================================================================")

client = dhib.IbSessionTws(host="host.docker.internal", port=7497, download_short_rates=False)
client.connect()

print("==============================================================================================================")
print("==== Get IB data tables.")
print("==============================================================================================================")

# Use delayed market data if you do not have access to real-time
# client.set_market_data_type(dhib.MarketDataType.DELAYED)
client.set_market_data_type(dhib.MarketDataType.REAL_TIME)

positions = client.tables["accounts_positions"]
contract_details = client.tables["contracts_details"]
ticks_generic = client.tables["ticks_generic"]
ticks_bid_ask = client.tables["ticks_bid_ask"]


print("==============================================================================================================")
print("==== Request data for the underlying symbol.")
print("==============================================================================================================")

usym = 'SPY'

c = Contract()
c.symbol = usym
c.secType = 'STK'
c.exchange = 'SMART'
c.currency = 'USD'

rc = client.get_registered_contract(c)
print(rc)

client.request_tick_data_realtime(rc, dhib.TickDataType.BID_ASK)

print("==============================================================================================================")
print("==== Get positions just for this options strategy and subscribe to data for positions in the portfolio.")
print("==============================================================================================================")

is_subscribed = set()

def null_to_empty(x) -> str:
    return "" if x is None else x

def subscribe_to_data(sec_type, symbol, expiry, strike, right, multiplier, currency) -> bool:
    key = (sec_type, symbol, expiry, strike, right, multiplier)

    if key in is_subscribed:
        return False

    c = Contract()
    c.symbol = symbol
    c.secType = sec_type
    c.exchange = "SMART"
    c.lastTradeDateOrContractMonth = null_to_empty(expiry)
    c.strike = null_to_empty(strike)
    c.right = null_to_empty(right)
    c.multiplier = null_to_empty(f"{multiplier}")
    c.currency = currency

    print(f"Subscribing to contract: {c}")
    rc = client.get_registered_contract(c)
    client.request_bars_realtime(rc, bar_type=dhib.BarDataType.MIDPOINT)

    if sec_type == "OPT":
        client.request_market_data(rc, generic_tick_types=[dhib.GenericTickType.OPTION_VOLATILITY_IMPLIED])

    is_subscribed.add(key)
    return True

pos = positions \
    .where("Symbol = usym") \
    .view(["Account", "ContractId", "SecType", "Symbol", "LocalSymbol", "Expiry=LastTradeDateOrContractMonth", "Strike", "Right", "Multiplier", "Currency", "Position"]) \
    .update("IsSubscribed = subscribe_to_data(SecType, Symbol, Expiry, Strike, Right, Multiplier, Currency)") \
    .drop_columns("IsSubscribed")

net_pos = pos \
    .drop_columns("Account") \
    .sum_by(["ContractId", "SecType", "Symbol", "LocalSymbol", "Expiry", "Strike", "Right", "Multiplier", "Currency"])

uprices = ticks_bid_ask \
    .where(["Symbol = usym", "SecType=`STK`"]) \
    .update("MidPrice = 0.5*(BidPrice + AskPrice)")

last_uprices = uprices.last_by("ContractId")

vols = ticks_generic \
    .where(["Symbol = usym", "TickType = `OPTION_IMPLIED_VOL`"]) \
    .view(["ContractId", "SecType", "Symbol", "LocalSymbol", "Expiry=LastTradeDateOrContractMonth", "Strike", "Right", "Multiplier", "Currency", "Vol=Value"])

last_vols = vols.last_by("ContractId")


print("==============================================================================================================")
print("==== Option pricing model.")
print("==============================================================================================================")

def cnd(d):
    A1 = 0.31938153
    A2 = -0.356563782
    A3 = 1.781477937
    A4 = -1.821255978
    A5 = 1.330274429
    RSQRT2PI = 0.39894228040143267793994605993438
    K = 1.0 / (1.0 + 0.2316419 * math.fabs(d))
    ret_val = (RSQRT2PI * math.exp(-0.5 * d * d) *
               (K * (A1 + K * (A2 + K * (A3 + K * (A4 + K * A5))))))
    if d > 0:
        ret_val = 1.0 - ret_val
    return ret_val

def black_scholes(S: float, X: float, T: float, R: float, V: float, isCall: bool) -> float:
    if T == NULL_DOUBLE:
        return NULL_DOUBLE

    sqrtT = math.sqrt(T)
    d1 = (math.log(S / X) + (R + 0.5 * V * V) * T) / (V * sqrtT)
    d2 = d1 - V * sqrtT
    cndd1 = cnd(d1)
    cndd2 = cnd(d2)
    expRT = math.exp((-1. * R) * T)

    if isCall:
        rst = S * cndd1 - X * expRT * cndd2
    else:
        rst = X * expRT * (1.0 - cndd2) - S * (1.0 - cndd1)

    return rst


print("==============================================================================================================")
print("==== Risk scenario calculations.")
print("==============================================================================================================")


def expiry_datetime(expiry):
    if expiry is None:
        return expiry

    s = f"{expiry[0:4]}-{expiry[4:6]}-{expiry[6:8]}T14:00:00 NY"
    return to_datetime(s)

scenarios = pos \
    .natural_join(last_vols, on="ContractId", joins="Vol") \
    .join(last_uprices, on="Symbol", joins="UPrice=MidPrice") \
    .lazy_update("ExpiryTime = (DateTime) expiry_datetime(Expiry)") \
    .update([
        "T = yearDiff(currentTime(), ExpiryTime)", 
        "IsCall = Right == `C`", 
        "IsStock = SecType == `STK`",
        "Rate = 0.04",
        "TheoBase = (double)black_scholes(UPrice, Strike, T, Rate, Vol, IsCall)", 
        "TheoBase = IsStock ? UPrice : TheoBase",
        ]) \
    .update(["Scenario = new double[]{-0.2, -0.15, -0.1, -0.05, -0.02, -0.01, 0, 0.01, 0.02, 0.05, 0.1, 0.15, 0.2}"]) \
    .ungroup() \
    .update([
        "UPriceScenario = (1+Scenario)*UPrice",
        "TheoScenario = (double) black_scholes(UPriceScenario, Strike, T, Rate, Vol, IsCall)", 
        "TheoScenario = IsStock ? UPriceScenario : TheoScenario",
        "TheoChange = TheoScenario - TheoBase",
        ])


print("==============================================================================================================")
print("==== Risk aggregation.")
print("==============================================================================================================")


risks = scenarios \
    .update("Risk = Position * Multiplier * TheoChange") \
    .view(["Account", "Scenario", "Risk"]) \
    .sum_by(["Account", "Scenario"])


print("==============================================================================================================")
print("==== Risk plots.")
print("==============================================================================================================")


risk_plot = Figure() \
    .plot_xy("Risk Scenarios", t=risks, x="Scenario", y="Risk", by=["Account"]) \
    .chart_title(title="Scenario Risks") \
    .show()
