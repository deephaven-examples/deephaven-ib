from ibapi.contract import Contract

import deephaven_ib as dhib

client = dhib.IbSessionTws(download_short_rates=False)

print(f"IsConnected: {client.is_connected()}")

client.connect(host="host.docker.internal", port=7496)

print(f"IsConnected: {client.is_connected()}")

c = Contract()
c.exchange = "NASDAQ"
c.symbol = "AAPL"

rc = client.get_registered_contract(c)

client.request_market_data(rc)

# # Below is the program execution
#
# if __name__ == '__main__':
#
#     # Specifies that we are on local host with port 7497 (paper trading port number)
#     app = TestApp("127.0.0.1", 7497, 0)
#
#     # A printout to show the program began
#     print("The program has begun")
#
#     #assigning the return from our clock method to a variable
#     requested_time = app.server_clock()
#
#     #printing the return from the server
#     print("")
#     print("This is the current time from the server " )
#     print(requested_time)
#
#     #disconnect the app when we are done with this one execution
#     # app.disconnect()
#
# # Below is the input area
