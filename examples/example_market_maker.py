
from ibapi.contract import Contract
from ibapi.order import Order

import deephaven_ib as dhib
from deephaven.updateby import ema_time, emstd_time
from deephaven import time_table
from deephaven.plot import Figure
from deephaven.plot.selectable_dataset import one_click
from deephaven.plot import PlotStyle


###########################################################################
# WARNING: THIS SCRIPT EXECUTES TRADES!! ONLY USE ON PAPER TRADING ACCOUNTS
###########################################################################

print("==============================================================================================================")
print("==== Create a client and connect.")
print("==== ** Accept the connection in TWS **")
print("==============================================================================================================")

client = dhib.IbSessionTws(host="host.docker.internal", port=7497, client_id=0, download_short_rates=False, read_only=False)
print(f"IsConnected: {client.is_connected()}")

client.connect()
print(f"IsConnected: {client.is_connected()}")

## Setup

account = "DU4943848"
max_position_dollars = 10000.0
em_time = "PT00:02:00"

errors = client.tables["errors"]
requests = client.tables["requests"]
positions = client.tables["accounts_positions"].where("Account = account")
ticks_bid_ask = client.tables["ticks_bid_ask"]
orders_submitted = client.tables["orders_submitted"].where("Account = account")
orders_status = client.tables["orders_status"]
orders_exec_details = client.tables["orders_exec_details"].where("Account = account")

print("==============================================================================================================")
print("==== Request data.")
print("==============================================================================================================")

registered_contracts_data = {}
registred_contracts_orders = {}

def add_contract(symbol: str, exchange: str="SMART") -> None:
    """
    Configure a contract for trading.
    :param symbol: Symbol to trade.
    :param exchange: exchange where orders get routed.
    :return: None
    """

    contract = Contract()
    contract.symbol = symbol
    contract.secType = "STK"
    contract.currency = "USD"
    contract.exchange = "SMART"

    rc = client.get_registered_contract(contract)
    id = rc.contract_details[0].contract.conId
    registered_contracts_data[id] = rc
    client.request_tick_data_realtime(rc, dhib.TickDataType.BID_ASK)
    print(f"Registered contract: id={id} rc={rc}")

    if exchange != "SMART":
        contract.exchange = "NYSE"
        rc = client.get_registered_contract(contract)

    registred_contracts_orders[id] = rc
    print(f"Registered contract: id={id} rc={rc}")


add_contract("GOOG")
add_contract("BAC")
add_contract("AAPL", exchange="NYSE")

print("==============================================================================================================")
print("==== Compute predictions.")
print("==============================================================================================================")

preds = ticks_bid_ask \
    .update_view(["MidPrice=0.5*(BidPrice+AskPrice)"]) \
    .update_by([
        ema_time("Timestamp", em_time, ["PredPrice=MidPrice"]),
        emstd_time("Timestamp", em_time, ["PredSD=MidPrice"]),
    ], by="Symbol") \
    .view([
        "ReceiveTime",
        "Timestamp",
        "ContractId",
        "Symbol",
        "BidPrice",
        "AskPrice",
        "MidPrice",
        "PredPrice",
        "PredSD",
        "PredLow=PredPrice-PredSD",
        "PredHigh=PredPrice+PredSD",
    ])

preds_start = preds.first_by("Symbol").view(["Symbol", "Timestamp"])
preds = preds.natural_join(preds_start, on="Symbol", joins="TimestampFirst=Timestamp")

preds_one_click = one_click(preds, by=["Symbol"], require_all_filters=True)

preds_plot = Figure() \
    .plot_xy("BidPrice", t=preds_one_click, x="Timestamp", y="BidPrice") \
    .plot_xy("AskPrice", t=preds_one_click, x="Timestamp", y="AskPrice") \
    .plot_xy("MidPrice", t=preds_one_click, x="Timestamp", y="MidPrice") \
    .plot_xy("PredPrice", t=preds_one_click, x="Timestamp", y="PredPrice") \
    .plot_xy("PredLow", t=preds_one_click, x="Timestamp", y="PredLow") \
    .plot_xy("PredHigh", t=preds_one_click, x="Timestamp", y="PredHigh") \
    .show()

print("==============================================================================================================")
print("==== Generate orders.")
print("==============================================================================================================")

open_orders = {}

def update_orders(contract_id: int, pred_low: float, pred_high: float, buy_order: bool, sell_order:bool) -> int:
    """
    Update orders on a contract.  First existing orders are canceled.  Then new buy/sell limit orders are placed.

    :param contract_id: Contract id.
    :param pred_low: Price for buy limit orders.
    :param pred_high: Price for sell limit orders.
    :param buy_order: True to post a buy order; False to not post a buy order.
    :param sell_order: True to post a sell order; False to not post a sell order.
    :return: Number of orders submitted.
    """

    if contract_id in open_orders:
        for order in open_orders[contract_id]:
            # print(f"Canceling order: contract_id={contract_id} order_id={order.request_id}")
            order.cancel()

    new_orders = []
    rc = registred_contracts_orders[contract_id]

    if sell_order:
        order_sell = Order()
        order_sell.account = account
        order_sell.action = "SELL"
        order_sell.orderType = "LIMIT"
        order_sell.totalQuantity = 100
        order_sell.lmtPrice = round( pred_high, 2)
        order_sell.transmit = True

        order = client.order_place(rc, order_sell)
        new_orders.append(order)

    if buy_order:
        order_buy = Order()
        order_buy.account = account
        order_buy.action = "BUY"
        order_buy.orderType = "LIMIT"
        order_buy.totalQuantity = 100
        order_buy.lmtPrice = round( pred_low, 2)
        order_buy.transmit = True

        order = client.order_place(rc, order_buy)
        new_orders.append(order)

    open_orders[contract_id] = new_orders
    return len(new_orders)

orders = preds.last_by(["Symbol"]) \
    .snapshot_when(time_table("PT00:01:00"), stamp_cols="SnapTime=Timestamp") \
    .where(f"Timestamp > TimestampFirst + '{em_time}'") \
    .natural_join(positions, on="ContractId", joins="Position") \
    .update_view([
        "Position = replaceIfNull(Position, 0.0)",
        "PositionDollars = Position * MidPrice",
        "MaxPositionDollars = max_position_dollars",
        "BuyOrder = PositionDollars < MaxPositionDollars",
        "SellOrder = PositionDollars > -MaxPositionDollars",
    ]) \
    .update("NumNewOrders = (long)update_orders(ContractId, PredLow, PredHigh, BuyOrder, SellOrder)")


print("==============================================================================================================")
print("==== Plot trade executions.")
print("==============================================================================================================")


trades = orders_exec_details \
    .natural_join(preds_start, on="Symbol", joins="TimestampFirst=Timestamp") \
    .where("ReceiveTime >= TimestampFirst") \
    .view(["Timestamp=ReceiveTime", "ContractId", "Symbol", "ExecutionExchange", "Side", "Shares", "Price"])

buys_one_click = one_click(trades.where("Side=`BOT`"), by=["Symbol"], require_all_filters=True)
sells_one_click = one_click(trades.where("Side=`SLD`"), by=["Symbol"], require_all_filters=True)

execution_plot = Figure() \
    .plot_xy("BidPrice", t=preds_one_click, x="Timestamp", y="BidPrice") \
    .plot_xy("AskPrice", t=preds_one_click, x="Timestamp", y="AskPrice") \
    .plot_xy("MidPrice", t=preds_one_click, x="Timestamp", y="MidPrice") \
    .plot_xy("PredPrice", t=preds_one_click, x="Timestamp", y="PredPrice") \
    .plot_xy("PredLow", t=preds_one_click, x="Timestamp", y="PredLow") \
    .plot_xy("PredHigh", t=preds_one_click, x="Timestamp", y="PredHigh") \
    .twin() \
    .axes(plot_style=PlotStyle.SCATTER) \
    .plot_xy("Buys", t=buys_one_click, x="Timestamp", y="Price") \
    .plot_xy("Sells", t=sells_one_click, x="Timestamp", y="Price") \
    .show()
