
# Run this example in the Deephaven IDE Console

import deephaven_ib as dhib

print("==============================================================================================================")
print("==== ** Accept the connection in TWS **")
print("==============================================================================================================")

client = dhib.IbSessionTws(host="localhost", port=7497)
client.connect()

from ibapi.contract import Contract

c1 = Contract()
c1.symbol = 'DIA'
c1.secType = 'STK'
c1.exchange = 'SMART'
c1.currency = 'USD'

rc1 = client.get_registered_contract(c1)
print(rc1)

c2 = Contract()
c2.symbol = 'SPY'
c2.secType = 'STK'
c2.exchange = 'SMART'
c2.currency = 'USD'

rc2 = client.get_registered_contract(c2)
print(rc2)

client.set_market_data_type(dhib.MarketDataType.REAL_TIME)
client.request_market_data(rc1)
client.request_market_data(rc2)
client.request_bars_realtime(rc1, bar_type=dhib.BarDataType.MIDPOINT)
client.request_bars_realtime(rc2, bar_type=dhib.BarDataType.MIDPOINT)

bars_realtime = client.tables["bars_realtime"]

bars_dia = bars_realtime.where("Symbol=`DIA`")
bars_spy = bars_realtime.where("Symbol=`SPY`")
bars_joined = bars_dia.view(["Timestamp", "TimestampEnd", "Dia=Close"]) \
    .natural_join(bars_spy, on="TimestampEnd", joins="Spy=Close") \
    .update("Ratio = Dia/Spy")

from deephaven.plot import Figure

plot_prices = Figure().plot_xy("DIA", t=bars_dia, x="TimestampEnd", y="Close") \
    .x_twin() \
    .plot_xy("SPY", t=bars_dia, x="TimestampEnd", y="Close") \
    .show()

plot_ratio = Figure().plot_xy("Ratio", t=bars_joined, x="TimestampEnd", y="Ratio") \
    .show()


