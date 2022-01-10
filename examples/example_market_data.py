from ibapi.contract import Contract

import deephaven_ib as dhib

client = dhib.IbSessionTws(download_short_rates=False)
client.connect(host="host.docker.internal", port=7496)

# Makes all tables global variables so that they are displayed in the user interface
for k, v in client.tables.items():
    globals()[k] = v

c = Contract()
c.symbol = 'AAPL'
c.secType = 'STK'
c.exchange = 'SMART'
c.currency = 'USD'

rc = client.get_registered_contract(c)
print(rc)

# TODO: should the data be delayed?
client.set_market_data_type(dhib.MarketDataType.DELAYED)
client.request_market_data(rc)
client.request_tick_data_realtime(rc, dhib.TickDataType.BID_ASK)
client.request_tick_data_realtime(rc, dhib.TickDataType.LAST)
client.request_tick_data_realtime(rc, dhib.TickDataType.MIDPOINT)
