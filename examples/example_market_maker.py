
from ibapi.contract import Contract
from ibapi.order import Order

import deephaven_ib as dhib
from deephaven.updateby import ema_time_decay
from deephaven import time_table
from deephaven.plot import Figure
from deephaven.plot.selectable_dataset import one_click


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
ticks_bid_ask = client.tables["ticks_bid_ask"]
orders_submitted = client.tables["orders_submitted"]
orders_status = client.tables["orders_status"]
positions = client.tables["accounts_positions"].where("Account = account")

print("==============================================================================================================")
print("==== Request data.")
print("==============================================================================================================")

registered_contracts_data = {}
registred_contracts_orders = {}

def add_contract(symbol):

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

    contract.exchange = "NYSE"
    rc = client.get_registered_contract(contract)
    registred_contracts_orders[id] = rc
    print(f"Registered contract: id={id} rc={rc}")


add_contract("GOOG")

print("==============================================================================================================")
print("==== Compute predictions.")
print("==============================================================================================================")

preds = ticks_bid_ask \
    .update_view(["MidPrice=0.5*(BidPrice+AskPrice)", "MidPrice2=MidPrice*MidPrice"]) \
    .update_by([ema_time_decay("Timestamp", "00:02:00", ["PredPrice=MidPrice","MidPrice2Bar=MidPrice2"])], by="Symbol") \
    .view([
        "ReceiveTime",
        "Timestamp",
        "ContractId",
        "Symbol",
        "BidPrice",
        "AskPrice",
        "MidPrice",
        "PredPrice",
        "PredSD = sqrt(MidPrice2Bar-PredPrice*PredPrice)",
        "PredLow=PredPrice-PredSD",
        "PredHigh=PredPrice+PredSD",
    ])


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
    print(f"START: update_orders: contract_id={contract_id}")

    if contract_id in open_orders:
        for order in open_orders[contract_id]:
            print(f"Canceling order: contract_id={contract_id} order_id={order.request_id}")
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

        print(f"Placing sell order: {rc} {order_sell}")
        order = client.order_place(rc, order_sell)
        new_orders.append(order)
    else:
        print(f"Not placing sell order: {rc}")

    if buy_order:
        order_buy = Order()
        order_buy.account = account
        order_buy.action = "BUY"
        order_buy.orderType = "LIMIT"
        order_buy.totalQuantity = 100
        order_buy.lmtPrice = round( pred_low, 2)
        order_buy.transmit = True

        print(f"Placing buy order: {rc} {order_buy}")
        order = client.order_place(rc, order_buy)
        new_orders.append(order)
    else:
        print(f"Not placing buy order: {rc}")

    open_orders[contract_id] = new_orders
    print(f"END: update_orders: contract_id={contract_id}")
    return len(new_orders)


#TODO replace after bug fix
# orders = time_table("00:01:00") \
#     .rename_columns("SnapTime=Timestamp") \
#     .snapshot(preds.last_by(["Symbol"])) \
#     .natural_join(positions, on="ContractId", joins="Position") \
#     .update_view([
#         "Position = replaceIfNull(Position, 0.0)",
#         "PositionDollars = Position * MidPrice",
#         "MaxPositionDollars = max_position_dollars",
#         "BuyOrder = PositionDollars < MaxPositionDollars",
#         "SellOrder = PositionDollars > -MaxPositionDollars",
#     ]) \
#     .update("NumNewOrders = (long)update_orders(ContractId, PredLow, PredHigh, BuyOrder, SellOrder)")

orders = preds.last_by(["Symbol"]) \
    .natural_join(positions, on="ContractId", joins="Position") \
    .update_view([
        "Position = replaceIfNull(Position, 0.0)",
        "PositionDollars = Position * MidPrice",
        "MaxPositionDollars = max_position_dollars",
        "BuyOrder = PositionDollars < MaxPositionDollars",
        "SellOrder = PositionDollars > -MaxPositionDollars",
    ])


orders = time_table("00:01:00") \
    .rename_columns("SnapTime=Timestamp") \
    .snapshot(orders) \
    .update("NumNewOrders = (long)update_orders(ContractId, PredLow, PredHigh, BuyOrder, SellOrder)")


