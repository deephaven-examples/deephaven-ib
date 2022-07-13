#Connect to the client
API_PORT = 7497

import deephaven_ib as dhib
client = dhib.IbSessionTws(host="host.docker.internal", port=API_PORT, read_only=False)
client.connect()

if client.is_connected():
    print('Client connected!')
else:
    raise RuntimeError("Client not connected!")

#Get market data for MSTR and BTC, both realtime and bars
from ibapi.contract import Contract

c = Contract()
c.secType = 'STK'
c.exchange = 'SMART'
c.currency = 'USD'
c.symbol = 'MSTR'

rc = client.get_registered_contract(c)
client.request_bars_historical(
  rc, 
  duration=dhib.Duration.days(253), 
  bar_size=dhib.BarSize.DAY_1, 
  bar_type=dhib.BarDataType.TRADES
)
client.request_bars_realtime(rc, bar_type=dhib.BarDataType.TRADES)

c2 = Contract()
c2.symbol = 'BTC'
c2.secType = 'CRYPTO'
c2.exchange = 'PAXOS'
c2.currency = 'USD'

rc2 = client.get_registered_contract(c2)
client.request_bars_historical(
  rc2, 
  duration=dhib.Duration.days(253), 
  bar_size=dhib.BarSize.DAY_1, 
  bar_type=dhib.BarDataType.AGGTRADES, 
  keep_up_to_date = False
)
client.request_bars_realtime(rc2, bar_type=dhib.BarDataType.TRADES)

#Get desired data and combine into tables
bars_hist = client.tables["bars_historical"] 
bars_btc_hist = bars_hist.where("Symbol=`BTC`")
bars_mstr_hist = bars_hist.where("Symbol=`MSTR`")

bars_realtime = client.tables['bars_realtime'] 
bars_btc = bars_realtime.where("Symbol=`BTC`")
bars_mstr = bars_realtime.where("Symbol=`MSTR`")

realtime_combined = bars_btc.view(["Timestamp","BTC = Close"])\
.natural_join(bars_mstr, on="Timestamp", joins="MSTR = Close")\
.where(filters=["!isNull(MSTR)","!isNull(BTC)"])\
.update(formulas=["BTCLog = log(BTC)","MSTRLog = log(MSTR)"])

hist_combined = bars_btc_hist.view(["Timestamp","BTC = Close"])\
.natural_join(bars_mstr_hist, on="Timestamp", joins="MSTR = Close")\
.where(filters=["!isNull(MSTR)","!isNull(BTC)"])\
.update(formulas=["BTCLog = log(BTC)","MSTRLog = log(MSTR)"])

import numpy as np
import numpy.polynomial.polynomial as poly

#Calculate linear regression
def calc_reg(x,y):
  x = np.array(x)
  y = np.array(y)
  reg, stats = poly.polyfit(x,y, 1, full=True)
  m = reg[1]
  c = reg[0]

  SSR = stats[0][0]
  diff = y - y.mean()
  square_diff = diff ** 2
  SST = square_diff.sum()
  R2 = 1- SSR/SST

  return (m, c, R2)

get_val = lambda rst, i: rst[i]

import time
time.sleep(5)

realtime_with_reg = realtime_combined\
  .group_by()\
  .update(formulas=["Reg = calc_reg(vec(BTCLog), vec(MSTRLog))", "Beta = (double) get_val(Reg,0)", "Intercept = (double) get_val(Reg,1)", "R2 = (double) get_val(Reg,2)"])\
  .drop_columns(cols=["Reg"])\
  .ungroup()\
  .update("MSTRLogPred = Beta * BTCLog + Intercept")\
  .move_columns(idx = 7, cols = "MSTRLogPred")

historical_with_reg = hist_combined\
  .group_by()\
  .update(formulas=["Reg = calc_reg(vec(BTCLog), vec(MSTRLog))", "Beta = (double) get_val(Reg,0)", "Intercept = (double) get_val(Reg,1)", "R2 = (double) get_val(Reg,2)"])\
  .drop_columns(cols=["Reg"])\
  .ungroup()\
  .update("MSTRLogPred = Beta * BTCLog + Intercept")\
  .move_columns(idx = 7, cols = "MSTRLogPred")

from deephaven.plot.figure import Figure
from deephaven.plot import PlotStyle, Colors, Shape
from deephaven.pandas import to_pandas

#Create pandas dataframes to display regression values as chart title
realtime_reg = to_pandas(realtime_with_reg.first_by())
historical_reg = to_pandas(historical_with_reg.first_by())


#Show the predicted price from the linear regressions alongside the actual price
realtime_prediction_plot = Figure()\
  .plot_xy(series_name="Actual", t=realtime_with_reg, x="Timestamp", y="MSTRLog")\
  .plot_xy(series_name="Predicted", t=realtime_with_reg, x="Timestamp", y="MSTRLogPred")\
  .chart_title(title=f"R2 = {realtime_reg['R2'][0]}, Beta = {realtime_reg['Beta'][0]}, Intercept = {realtime_reg['Intercept'][0]}") \
  .show()

historical_prediction_plot = Figure()\
  .plot_xy(series_name="Actual", t=historical_with_reg, x="Timestamp", y="MSTRLog")\
  .plot_xy(series_name="Predicted", t=historical_with_reg, x="Timestamp", y="MSTRLogPred")\
  .chart_title(title=f"R2 = {historical_reg['R2'][0]}, Beta = {historical_reg['Beta'][0]}, Intercept = {historical_reg['Intercept'][0]}") \
  .show()
