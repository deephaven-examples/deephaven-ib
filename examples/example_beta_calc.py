## Set the API port. Default port numbers are:
# 7496 - Trader Workstation, real trading
# 4001 - IB Gateway, real trading
# 7497 - Trader Workstation, paper trading
# 4002 - IB Gateway, paper trading
API_PORT = 7497

import deephaven_ib as dhib

# Disable read-only mode when connecting to the default ports for paper trading:
if API_PORT == 7497 or API_PORT == 4002:
    read_only_api = False
else:
    read_only_api = True

client = dhib.IbSessionTws(host="host.docker.internal", port=API_PORT, read_only=read_only_api)
client.connect()

if client.is_connected():
    print('Client connected!')
else:
    raise RuntimeError("Client not connected!")


def check_table_size(dh_table, table_name, expected_size=1):
    table_size = dh_table.size
    if (table_size < expected_size):
        raise RuntimeError(
            'Table "' + table_name + '" has ' + str(table_size) + ' rows! (Expected ' + str(expected_size) + '.)')
    else:
        print('Found ' + str(table_size) + ' rows in table "' + table_name + '".')


# Get the Deephaven table of position updates, and use 'last_by' to find the
# current positions (i.e. last row for each ContractId):
positions = client.tables['accounts_positions'].last_by(['ContractId'])

positions.j_table.awaitUpdate()

check_table_size(positions, "pos")

##########
##########
##########

import numpy as np
from deephaven.pandas import to_pandas

# Get a DH table containing only the distinct Symbols:
pos_syms = positions.select_distinct(['Symbol'])
mkt_data_syms_set = set(to_pandas(pos_syms)['Symbol'].values)
print('Found ' + str(len(mkt_data_syms_set)) + ' position symbols: ' + str(mkt_data_syms_set))

# Add SPY to the set of symbols to request data for:
mkt_data_syms_set.add('SPY')

from ibapi.contract import Contract

c = Contract()
c.secType = 'STK'
c.exchange = 'SMART'
c.currency = 'USD'

c.symbol = None
for sym in mkt_data_syms_set:
    print('Requesting data for symbol=' + str(sym))
    c.symbol = sym

    rc = client.get_registered_contract(c)
    client.request_bars_historical(
        rc,
        duration=dhib.Duration.days(253),
        bar_size=dhib.BarSize.DAY_1,
        bar_type=dhib.BarDataType.ADJUSTED_LAST,
        keep_up_to_date=False
    )

# Retrieve the Deephaven table of historical data bars:
hist_data_bars = client.tables['bars_historical']

# Wait for data to be retrieved:
from time import sleep

sleep(5)

hist_data_bars.j_table.awaitUpdate()
hist_data_recvd_syms = hist_data_bars.select_distinct(['Symbol'])
check_table_size(hist_data_recvd_syms, 'hist_data_recvd_syms', len(mkt_data_syms_set))

##########
##########
##########

# Use 'colname_[i-1]' to read a value from the previous row
hist_data_with_return = hist_data_bars \
    .update_view(formulas=[
    'SameTickerAsPrevRow = Symbol=Symbol_[i-1]',
    'Last   = !SameTickerAsPrevRow ? null : Close_[i-1]',
    'Chg    = Close - Last',
    'Return = Chg/Last',
])

# Join the SPY returns onto the returns for all stocks
spy = hist_data_with_return.where("Symbol=`SPY`")
hist_data_with_spy = hist_data_with_return.natural_join(spy, ['Timestamp'], ['SPY_Return=Return'])

##########
##########
##########


# Install sklearn and run a linear regression to calculate betas
print("Installing sklearn...")
import os

os.system("pip install sklearn")
from sklearn.linear_model import LinearRegression

## Use a DynamicTableWriter to store regression results in a Deephaven table
import deephaven.dtypes as dht
from deephaven import DynamicTableWriter
from deephaven.table import Table

table_writer = DynamicTableWriter(
    {"Symbol": dht.string,
     "Beta": dht.double,
     "Intercept": dht.double,
     "R2": dht.double
     }
)
regression_results = table_writer.table

# Partition the table, creating a distinct table for each Symbol:
data_partitioned = hist_data_with_spy.partition_by(['Symbol'])

print('Calculating betas...')
for symbol in mkt_data_syms_set:
    print('Calculating beta for ' + symbol + '...')
    returns_for_betas = data_partitioned.get_constituent(symbol) \
        .where(['!isNull(Return)', '!isNull(SPY_Return)'])

    returns_for_betas_df = to_pandas(returns_for_betas)

    reg = LinearRegression()
    X = returns_for_betas_df['SPY_Return'].values.reshape(-1, 1)
    Y = returns_for_betas_df['Return']
    reg.fit(X, Y)
    r2 = reg.score(X, Y).real

    print(symbol + ' coef: ' + str(reg.coef_) +
          '; intercept: ' + str(reg.intercept_) +
          '; R2: ', str(r2))

    # Append to the 'regression_results' table:
    table_writer.write_row(
        symbol,
        reg.coef_[0],
        reg.intercept_,
        r2
    )
print('Finished calculating betas!')

##########
##########
##########


# Request live prices:
ticks_price = client.tables['ticks_price']
live_prices = ticks_price.last_by(['ContractId'])

for sym in mkt_data_syms_set:
    print('Requesting data for symbol=' + str(sym))
    c.symbol = sym
    rc = client.get_registered_contract(c)
    client.request_market_data(
        rc,
        snapshot=False
    )

sleep(2)
live_prices.j_table.awaitUpdate()
check_table_size(live_prices, 'live_prices', len(mkt_data_syms_set))

##########
##########
##########

# Join the table of betas onto the positions
pos_with_beta = positions.natural_join(live_prices, ['ContractId'], ['Price']) \
    .natural_join(regression_results, ['Symbol'], ['Beta', 'R2']) \
    .view([
    'Symbol',
    'ContractId',
    'SecType',
    'Currency',
    'Position',
    'PosValue = Position * Price',
    'Price',
    'AvgCost',
    'PNL = PosValue - AvgCost * Position',
    'Beta',
    'R2',
    'SPYBetaValue = Beta * PosValue',
])

##########
##########
##########

# Calculate hedge, excluding positions with a very low R2:
hedge_shares = pos_with_beta \
    .view([
    'PosValue',
    'WeightedBeta = Beta * PosValue',
    'SPYBetaValue',
    'SPYBetaValueForHedge = R2 > 1/5 ? SPYBetaValue : 0'
]) \
    .sum_by() \
    .natural_join(live_prices.where('Symbol=`SPY`'), [], ['SPY_Price=Price']) \
    .view([
    'PortfolioValue = PosValue',
    'PortfolioBeta = WeightedBeta / PosValue',
    'SPYBetaValue',
    'SPYBetaValueForHedge',
    'HedgeShares = -round(SPYBetaValueForHedge / SPY_Price)',
    'HedgeCost = HedgeShares * SPY_Price',
    'SPY_Price'
])

##########
##########
##########

# Set send_hedge_order to True to submit the order, not just generate it.
# (Must also set read_only to False when creating the IbSessionTws instance.)
send_hedge_order = False

from ibapi.order import Order

c.symbol = "SPY"
rc = client.get_registered_contract(c)
print(c)

# Extract the hedge information from the hedge_shares table:
hedge_info = hedge_shares.j_table.getRecord(0, 'HedgeShares', 'SPY_Price')
hedge_qty = hedge_info[0]
hedge_last_px = hedge_info[1]
hedge_side = "BUY" if hedge_qty > 0 else "SELL"
hedge_limit_px = hedge_last_px + 0.05 * (1 if hedge_side == "BUY" else -1)

# Create an order with the IB API:
order = Order()
# order.account = "<account number>"
order.action = hedge_side
order.orderType = "LIMIT"
order.totalQuantity = hedge_qty
order.lmtPrice = hedge_limit_px
order.eTradeOnly = False
order.firmQuoteOnly = False

print('Order: ' + str(order))

if send_hedge_order:
    print('***** Sending order to ' + order.action + ' ' + str(
        order.totalQuantity) + ' shares of ' + c.symbol + '! *****')
    req = client.order_place(rc, order)

else:
    print('Not actually sending order.')

# To cancel orders:
# req.cancel()
# client.order_cancel_all()
