
# Run this example in the Deephaven IDE Console

from ibapi.contract import Contract

import deephaven_ib as dhib

print("==============================================================================================================")
print("==== ** Accept the connection in TWS **")
print("==============================================================================================================")

client = dhib.IbSessionTws(host="localhost", port=7497, download_short_rates=False)
client.connect()

# Makes all tables global variables so that they are displayed in the user interface
for k, v in client.tables.items():
    globals()[k] = v

# Use delayed market data if you do not have access to real-time
# client.set_market_data_type(dhib.MarketDataType.DELAYED)
client.set_market_data_type(dhib.MarketDataType.REAL_TIME)


c = Contract()
c.symbol = 'AAPL'
c.secType = 'STK'
c.exchange = 'SMART'
c.currency = 'USD'

rc = client.get_registered_contract(c)
print(rc)

client.request_market_data(rc)
client.request_tick_data_realtime(rc, dhib.TickDataType.BID_ASK)
client.request_tick_data_realtime(rc, dhib.TickDataType.LAST)
client.request_tick_data_realtime(rc, dhib.TickDataType.MIDPOINT)
