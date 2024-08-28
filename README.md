# deephaven-ib

![Deephaven Data Labs Logo](https://raw.githubusercontent.com/deephaven-examples/deephaven-ib/main/docs/assets/Deephaven-Logo-Wordmark-Community-OnLight.png)

![Build CI](https://github.com/deephaven-examples/deephaven-ib/actions/workflows/build-and-publish.yml/badge.svg?branch=main)

An [Interactive Brokers](https://www.interactivebrokers.com/) integration for [Deephaven](https://deephaven.io).

[Interactive Brokers](https://www.interactivebrokers.com/) is a very popular brokerage in the quantitative finance world,
with about $200B of customer equity.  Quants and hedge funds often choose [Interactive Brokers](https://www.interactivebrokers.com/) because of its low trading costs and API that facilitates automated trading.  With low minimum account balances, 
it is also an attractive choice for individual investors.

[Deephaven](https://deephaven.io) is the real-time query engine that is the backbone for the quantitative trading of the 
world's largest hedge funds, banks, and exchanges.  [Deephaven](https://deephaven.io) makes working with real-time data easy and
facilitates very concise and easy-to-read code.  With [Deephaven](https://deephaven.io), quants can create new models 
and get them into production quickly, traders can monitor the market and their portfolios, and 
managers can monitor risk. 

[deephaven-ib](https://github.com/deephaven-examples/deephaven-ib) combines the low-cost trading of 
[Interactive Brokers](https://www.interactivebrokers.com/) with the analytical power and ease of use of 
[Deephaven Community Core](https://github.com/deephaven/deephaven-core) to yield an open, quantitative 
trading platform.  Basically, it provides an open platform for building quantitative trading strategies and
custom analytics.  You can build something simple, like a portfolio monitor, or something complex, like a 
fully-automated, multi-strategy quantitative hedge fund.

[deephaven-ib](https://github.com/deephaven-examples/deephaven-ib) supports trading essentially all common
exchange traded products.  These include:
* Stocks
* Mutual Funds
* Options
* Futures
* Futures Options
* Indexes
* Bonds
* Foreign Exchange (Forex or FX)
* Cryptocurrency
* Contracts for Differences (CFDs)
* Warrants
* Commodities

![Overview Image](https://raw.githubusercontent.com/deephaven-examples/deephaven-ib/main/docs/assets/overview.png)

**WARNING: Automated trading can go horribly wrong very quickly.  Verify your code on a paper trading account before 
unleashing trading on an account where money can be lost.  If you think this can not happen to you, read
[The Rise and Fall of Knight Capital](https://medium.com/dataseries/the-rise-and-fall-of-knight-capital-buy-high-sell-low-rinse-and-repeat-ae17fae780f6).
The [Setup](#setup) section shows configurations to prevent accidental trade submission.**

For more details, see:
* [Interactive Brokers](https://www.interactivebrokers.com/)
* [Deephaven](https://deephaven.io)
* [Deephaven Community Core](https://github.com/deephaven/deephaven-core)

For help with [deephaven-ib](https://github.com/deephaven-examples/deephaven-ib):
* [deephaven-ib Docs](https://deephaven-examples.github.io/deephaven-ib/)
* [Gitter: A relaxed chat room about all things Deephaven](https://gitter.im/deephaven/deephaven)
* [Deephaven Community Slack](https://join.slack.com/t/deephavencommunity/shared_invite/zt-11x3hiufp-DmOMWDAvXv_pNDUlVkagLQ)

For Deephaven how-to guides, see:
* [Deephaven Tutorial](https://deephaven.io/core/docs/tutorials/overview/) 
* [Deephaven Coummunity Core Documentation](https://deephaven.io/core/docs/).

For help with [Deephaven](https://deephaven.io):
* [Gitter: A relaxed chat room about all things Deephaven](https://gitter.im/deephaven/deephaven)
* [Deephaven Community Slack](https://join.slack.com/t/deephavencommunity/shared_invite/zt-11x3hiufp-DmOMWDAvXv_pNDUlVkagLQ)
* [Deephaven Community Core Discussions](https://github.com/deephaven/deephaven-core/discussions)


# Data Available in Deephaven

The [Deephaven](https://deephaven.io) query engine is built around the concept of tables, which are similar to Pandas dataframes.  
Unlike Pandas dataframes, [Deephaven](https://deephaven.io) tables can dynamically update as new data is streamed in.
As input tables change, the [Deephaven](https://deephaven.io) query engine ensures that all queries, no matter how complex, 
are kept up-to-date. 

Once data is converted to a [Deephaven](https://deephaven.io) table, it can be used in queries with any other 
[Deephaven](https://deephaven.io) tables.

## IB TWS data

Data available from [IB Trader Workstation (TWS)](https://www.interactivebrokers.com/en/trading/tws.php) can be accessed 
as [Deephaven](https://deephaven.io) tables by using [deephaven-ib](https://github.com/deephaven-examples/deephaven-ib).
As data streams in, the tables and queries using them will automatically update.

These tables include:

* General
    * `errors`: an error log
    * `requests`: requests to IB
* Contracts
    * `contract_details`: details describing contracts of interest.  Automatically populated.
    * `contracts_matching`: contracts matching query strings provided to `request_contracts_matching`.
    * `market_rules`: market rules indicating the price increment a contract can trade in.  Automatically populated.
    * `short_rates`: interest rates for shorting securities.  Automatically populated if `download_short_rates=True`.
* Accounts
    * `accounts_managed`: accounts managed by the TWS session login.  Automatically populated.
    * `accounts_family_codes`: account family.  Automatically populated.
    * `accounts_groups`: account groups.  Automatically populated.
    * `accounts_allocation_profiles`: allocation profiles for accounts.  Automatically populated.
    * `accounts_value`: account values.  Automatically populated.
    * `accounts_overview`: overview of account details.  Automatically populated.
    * `accounts_summary`: account summary.  Automatically populated.
    * `accounts_positions`: account positions.  Automatically populated.
    * `accounts_pnl`: account PNL.  Automatically populated.
* News
    * `news_providers`: currently subscribed news sources.  Automatically populated.
    * `news_bulletins`: news bulletins.  Automatically populated.
    * `news_articles`: the content of news articles requested via `request_news_article`.
    * `news_historical`: historical news headlines requested via `request_news_historical`.
* Market Data
    * `ticks_price`: real-time tick market data of price values requested via `request_market_data`.
    * `ticks_size`: real-time tick market data of size values requested via `request_market_data`.
    * `ticks_string`: real-time tick market data of string values requested via `request_market_data`.
    * `ticks_efp`: real-time tick market data of exchange for physical (EFP) values requested via `request_market_data`.
    * `ticks_generic`: real-time tick market data of generic floating point values requested via `request_market_data`.
    * `ticks_option_computation`: real-time tick market data of option computations requested via `request_market_data`.
    * `ticks_trade`: real-time tick market data of trade prices requested via `request_tick_data_historical` or `request_tick_data_realtime`.
    * `ticks_bid_ask`: real-time tick market data of bid and ask prices requested via `request_tick_data_historical` or `request_tick_data_realtime`.
    * `ticks_mid_point`: real-time tick market data of mid-point prices requested via `request_tick_data_historical` or `request_tick_data_realtime`.
    * `bars_historical`: historical price bars requested via `request_bars_historical`.  Real-time bars change as new data arrives.
    * `bars_realtime`: real-time price bars requested via `request_bars_realtime`.
* Order Management System (OMS)
    * `orders_submitted`: submitted orders **FOR THE THE CLIENT'S ID**.  A client ID of 0 contains manually entered orders.  Automatically populated.
    * `orders_status`: order statuses.  Automatically populated.
    * `orders_completed`: completed orders.  Automatically populated.
    * `orders_exec_details`: order execution details.  Automatically populated.
    * `orders_exec_commission_report`: order execution commission report.  Automatically populated.

Most tables include a `ReceiveTime` column.  This column indicates the time the data was received by [deephaven-ib](https://github.com/deephaven-examples/deephaven-ib). It does not represent the time the event occurred.

## Your data

You may want to combine data from other sources with your IB data.  [Deephaven](https://deephaven.io) can load data from:
* [CSV](https://deephaven.io/core/docs/how-to-guides/csv-import/)
* [Parquet](https://deephaven.io/core/docs/how-to-guides/parquet-flat/) 
* [Kafka](https://deephaven.io/core/docs/how-to-guides/kafka-topics/).  
See the [Deephaven Documentation](https://deephaven.io/core/docs) for details.

# Run deephaven-ib

Follow these steps to run a [Deephaven](https://deephaven.io) plus [Interactive Brokers](https://interactivebrokers.com) system.

These instructions produce a virtual environment with [deephaven-ib](https://github.com/deephaven-examples/deephaven-ib), [Deephaven](https://deephaven.io), and `ibapi` installed.
For more details on using pip-installed Deephaven, see [Deephaven's Installation Guide for pip](https://deephaven.io/core/docs/tutorials/pip-install/).

| :exclamation:  Windows users _must_ run these commands in WSL.   |
|------------------------------------------------------------------|

## Setup IB
To setup and configure the system:

1) Follow the [TWS Installation Instructions](https://www.interactivebrokers.com/en/trading/tws.php) to get [IB Trader Workstation (TWS)](https://www.interactivebrokers.com/en/trading/tws.php) running.
2) Launch [IB Trader Workstation (TWS)](https://www.interactivebrokers.com/en/trading/tws.php).
3) In [IB Trader Workstation (TWS)](https://www.interactivebrokers.com/en/trading/tws.php), click on the gear in the
upper right corner.  ![](https://raw.githubusercontent.com/deephaven-examples/deephaven-ib/main/docs/assets/config-gear.png)  
  In `API->Settings`, make sure:

    * "Enable ActiveX and Socket Clients" is selected.
    * "Allow connections from localhost only" is not selected.
    * "Read-Only API" is selected if you want to prevent trade submission from [deephaven-ib](https://github.com/deephaven-examples/deephaven-ib).  
        
    Also, note the "Socket port" value.  It is needed when connecting [deephaven-ib](https://github.com/deephaven-examples/deephaven-ib).
    ![](https://raw.githubusercontent.com/deephaven-examples/deephaven-ib/main/docs/assets/config-api.png)
4) [For Paper Trading] Log into the [Interactive Brokers Web Interface](https://interactivebrokers.com/).
5) [For Paper Trading] In the [Interactive Brokers Web Interface](https://interactivebrokers.com/), navigate to `Account->Settings->Paper Trading Account` and make sure that "Share real-time market data subscriptions with paper trading account?" is set to true.
6) Once [deephaven-ib](https://github.com/deephaven-examples/deephaven-ib) is launched (see [below](#launch)), accept incoming connections to [IB Trader Workstation (TWS)](https://www.interactivebrokers.com/en/trading/tws.php).  (May not be required for all sessions.)
![](https://raw.githubusercontent.com/deephaven-examples/deephaven-ib/main/docs/assets/allow-connections.png)

## Virtual Environment

Interactive Brokers does not make their Python wheels available via PyPI, and the wheels are not redistributable.
As a result, installing [deephaven-ib](https://github.com/deephaven-examples/deephaven-ib) requires a Python script to build the wheels locally before installation.
The script installs `deephaven-ib`, `ibapi`, and `deephaven` into the environment.

To keep your development environment clean, the script creates a virtual environment for [deephaven-ib](https://github.com/deephaven-examples/deephaven-ib).
Follow the directions below to build and activate the virtual environment using the [./dhib_env.py](./dhib_env.py) script.

An existing virtual environment can be used with the `--create_venv false` and `--path_venv <path>` options.

If you prefer to install directly into your system Python without a virtual environment, 
you can use the `--use_venv false` option to [./dhib_env.py](./dhib_env.py).


### Build the Virtual Environment

1) Install Java 17 and set the appropriate `JAVA_HOME` environment variable.    
2) Check out [deephaven-ib](https://github.com/deephaven-examples/deephaven-ib)
    ```bash
    git clone git@github.com:deephaven-examples/deephaven-ib.git
    ```
3) Change to the deephaven-ib directory:
    ```bash
    cd deephaven-ib
    ```
4) Build a [deephaven-ib](https://github.com/deephaven-examples/deephaven-ib) virtual environment:

   First, install the dependencies needed to run the script:
    ```bash
    python3 -m pip install -r requirements_dhib_env.txt
    ```

   To see all options:
    ```bash
    python3 ./dhib_env.py --help
    ```

   To install the latest production release version of [deephaven-ib](https://github.com/deephaven-examples/deephaven-ib) from PyPi plus the release-specified `ibapi` and `deephaven` versions: 
    ```bash
    python3 ./dhib_env.py release
    ```
   
   To install the latest development version of [deephaven-ib](https://github.com/deephaven-examples/deephaven-ib) from source plus the default `ibapi` and `deephaven` versions:
    ```bash
    python3 ./dhib_env.py dev
    ```

   To create a venv for developing [deephaven-ib](https://github.com/deephaven-examples/deephaven-ib) in PyCharm: (This will not install `deephaven-ib`, but it will install the default `ibapi` and `deephaven` versions.)
    ```bash
    python3 ./dhib_env.py dev --install_dhib false
    ```
   
5) In the logs, take note of where the virtual environment is located.  It will be in a directory like `./venv-<versiondetails>`.
   
### Activate the Virtual Environment

To activate the virtual environment:
```bash
source ./venv-<versiondetails>/bin/activate
```

Once the virtual environment is activated, `python` and `pip` will use the virtual environment's Python and packages --
including everything needed to run [deephaven-ib](https://github.com/deephaven-examples/deephaven-ib).

### Deactivate the Virtual Environment

To deactivate the virtual environment:
```bash
deactivate
```

Once the virtual environment is deactivated, `python` and `pip` will use the system's Python and packages.
[deephaven-ib](https://github.com/deephaven-examples/deephaven-ib) will not be available.


# Use deephaven-ib

To use [deephaven-ib](https://github.com/deephaven-examples/deephaven-ib), you need to start a [Deephaven](https://deephaven.io) server and connect to 
[IB Trader Workstation (TWS)](https://www.interactivebrokers.com/en/trading/tws.php).
You can optionally use the Deephaven IDE to visualize data and run queries.

## Start Deephaven

First, start a [Deephaven](https://deephaven.io) server.  This server will be used to process data and run queries.

The documentation and examples here illustrate using Deephaven's [Pre-Shared Key (PSK) authentication](https://deephaven.io/core/docs/how-to-guides/authentication/auth-psk/)
with the password `DeephavenRocks!`.  Other types of Deephaven authentication can also work.  
See the [Deephaven Documentation](https://deephaven.io/core/docs/) for details.


### Option 1: Use the `deephaven` command

The easiest way to start a deephaven server is using `deephaven` on the command line.
The `deephaven` command was added to the virtual environment when it was created.
It is available in [Deephaven](https://deephaven.io) versions `>= 0.34.0`.

This command will start a deephaven server with 4GB of memory and the password `DeephavenRocks!`.
It will also automatically open the Deephaven IDE in a web browser.

```bash
source ./venv-<versiondetails>/bin/activate
deephaven server --jvm-args "-Xmx4g -Dauthentication.psk=DeephavenRocks! -Dstorage.path=~/.deephaven"
```


### Option 2: Use a Python script

An alternative way to launch a deephaven server is to use a Python script.  This works with all versions of 
[Deephaven](https://deephaven.io) and can be used to populate the server with queries.  
See [Deephaven's Installation Guide for pip](https://deephaven.io/core/docs/tutorials/pip-install/) for more details on 
running [Deephaven](https://deephaven.io) this way.

To start Python with the virtual environment, run:
```bash
source ./venv-<versiondetails>/bin/activate
python
```

Once Python is running, you can start a deephaven server with the following script:
```python
import os
from time import sleep
from deephaven_server import Server

_server = Server(port=10000, jvm_args=['-Xmx4g','-Dauthentication.psk=DeephavenRocks!','-Dstorage.path=' + os.path.expanduser('~/.deephaven')])
_server.start()

# You can insert queries here

# Keep the server running
while True:
    sleep(1)
```
> :warning: These deephaven server commands **must** be run before importing `deephaven` or `deephaven_ib`.

At the indicated place in the script, you can put queries that you want to run when the server starts.  
This could be code to conenct to [IB Trader Workstation (TWS)](https://www.interactivebrokers.com/en/trading/tws.php), request data, analyze data, visualize data, or trade.  
See the examples below for more details.


## Launch the Deephaven IDE

Once the Deephaven server is started, you can launch the Deephaven IDE.
If you used the `deephaven` command to start the server, the Deephaven IDE will automatically open in your web browser.

The Deephaven IDE is a web-based interface for working with Deephaven.
Once in the IDE, you can run queries, create notebooks, and visualize data.
You can also run all of the example code below and the more complex examples in [./examples](./examples).

To launch the Deephaven IDE, navigate to [http://localhost:10000/ide/](http://localhost:10000/ide/) in your web browser.
Chrome, Edge, Chrome-based, and Firefox browsers are supported.  Safari is not supported.
How you authenticate will depend upon how authentication is configured.  
In the examples here, you will use the password `DeephavenRocks!`.


## Connect to TWS

All [deephaven-ib](https://github.com/deephaven-examples/deephaven-ib) sessions need to first create a client for interacting 
with [IB Trader Workstation (TWS)](https://www.interactivebrokers.com/en/trading/tws.php).

`host` is the computer to connect to.  When using [deephaven-ib](https://github.com/deephaven-examples/deephaven-ib) locally, `host` is usually set to `localhost`.
When using [deephaven-ib](https://github.com/deephaven-examples/deephaven-ib) inside
of Docker, `host` should be set to `host.docker.internal`.  

`port` is the network port [IB Trader Workstation (TWS)](https://www.interactivebrokers.com/en/trading/tws.php)
communicates on.  This value can be found in the [IB Trader Workstation (TWS)](https://www.interactivebrokers.com/en/trading/tws.php)
settings.  By default, production trading uses port 7496, and paper trading uses port 7497.  See [Setup](#setup) and [TWS Initial Setup](https://interactivebrokers.github.io/tws-api/initial_setup.html) for more details.

`read_only` is a boolean value that is used to enable trading.  By default `read_only=True`, preventing trading.  Use `read_only=False` to enable trading.

`is_fa` is a boolean value that is used to indicate if an account is a financial advisor (FA) account or a regular acccount. 
 By using `is_fa=True`, FA account configuration details are requested.  By default `is_fa=False`.  
 If `is_fa=True` is used on a non-FA account, everything should work fine, but there will be error messages.
 If `is_fa=False` (the default) is used on a FA account, FA account configurations will not be populated in tables such as
 `accounts_groups`, `accounts_allocation_profiles`, and `accounts_aliases`.

`order_id_strategy` is the strategy used for obtaining new order ids.  Order id algorithms have tradeoffs in execution time, support for multiple, concurrent sessions, and avoidance of TWS bugs.
* `OrderIdStrategy.RETRY` (default) - Request a new order ID from TWS every time one is needed.  Retry if TWS does not respond quickly.  This usually avoids a TWS bug where it does not always respond.
* `OrderIdStrategy.BASIC` - Request a new order ID from TWS every time one is needed.  Does not retry, so it may deadlock if TWS does not respond.
* `OrderIdStrategy.INCREMENT` - Use the initial order ID sent by TWS and increment the value upon every request.  This is fast, but it may fail for multiple, concurrent sessions connected to TWS.

For a read-write session that allows trading:
```python
import deephaven_ib as dhib

client = dhib.IbSessionTws(host="localhost", port=7497, read_only=False)
client.connect()
```

For a read-only session that does not allow trading:
```python
import deephaven_ib as dhib

client = dhib.IbSessionTws(host="localhost", port=7497, read_only=True)
client.connect()
```

For a read-only financial advisor (FA) session that does not allow trading:
```python
import deephaven_ib as dhib

client = dhib.IbSessionTws(host="localhost", port=7497, read_only=True, is_fa=True)
client.connect()
```

After `client.connect()` is called, TWS requires that the connection be accepted.
![](https://raw.githubusercontent.com/deephaven-examples/deephaven-ib/main/docs/assets/accept-connection.png)

## Get data

[IB Trader Workstation (TWS)](https://www.interactivebrokers.com/en/trading/tws.php) data is stored in
the [deephaven-ib](https://github.com/deephaven-examples/deephaven-ib) client as two dictionaries of tables:
* `tables` contains the tables most users will want.  
* `tables_raw` contains raw [IB Trader Workstation (TWS)](https://www.interactivebrokers.com/en/trading/tws.php)
data.

As an example, the `requests` table, that contains all of the requests made to [IB Trader Workstation (TWS)](https://www.interactivebrokers.com/en/trading/tws.php),
can be obtained by:

```python
requests = client.tables["requests"]
```

To display all of the tables in the [Deephaven IDE](https://github.com/deephaven/deephaven-core/blob/main/README.md#run-deephaven-ide),
place the tables in the global namespace.  This can most easily be done by:

```python
for k, v in client.tables.items():
    globals()[k] = v
```

Similarly, raw tables can be viewed by:

```python
for k, v in client.tables_raw.items():
    globals()[k] = v
```

A list of available tables can be obtained by:

```python
print(client.tables.keys())
print(client.tables_raw.keys())
```

## Create a contract

In IB, financial contracts include:
* Stocks
* FX
* Cryptocurrency
* Indexes
* CFDs
* Futures
* Options
* Futures Options
* Bonds
* Mutual Funds
* Warrants
* Commodities

To create a contract for use in [deephaven-ib](https://github.com/deephaven-examples/deephaven-ib),
the contract must first be created as an `ibapi.contract.Contract`.  Once the contract is created,
it must be registered with [deephaven-ib](https://github.com/deephaven-examples/deephaven-ib) before it
can be used.  

Details on creating contracts can be found at 
[https://interactivebrokers.github.io/tws-api/basic_contracts.html](https://interactivebrokers.github.io/tws-api/basic_contracts.html).

Registering the contract causes the contract details to appear in the `contracts_details` table.

```python
from ibapi.contract import Contract

c = Contract()
c.symbol = 'AAPL'
c.secType = 'STK'
c.exchange = 'SMART'
c.currency = 'USD'

rc = client.get_registered_contract(c)
print(rc)
```

[./examples/example_all_functionality.py](./examples/example_all_functionality.py) illustrates the creation and registration
of many different types of contracts.

## Request market data

Market data can be requested from the client using:
* `request_market_data`
* `request_bars_historical`
* `request_bars_realtime`
* `request_tick_data_realtime`
* `request_tick_data_historical`

```python
from ibapi.contract import Contract

import deephaven_ib as dhib

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
```

[./examples/example_all_functionality.py](./examples/example_all_functionality.py) illustrates requesting
many kinds of market data.


## Request news

Market data can be requested from the client using:
* `request_news_historical`
* `request_news_article`

```python
from ibapi.contract import Contract

from deephaven.time import to_datetime

contract = Contract()
contract.symbol = "GOOG"
contract.secType = "STK"
contract.currency = "USD"
contract.exchange = "SMART"

rc = client.get_registered_contract(contract)
print(contract)

start = "2021-01-01T00:00:00 ET"
end = "2021-01-10T00:00:00 ET"
client.request_news_historical(rc, start=start, end=end)

client.request_news_article(provider_code="BRFUPDN", article_id="BRFUPDN$107d53ea")
```

[./examples/example_all_functionality.py](./examples/example_all_functionality.py) illustrates requesting
news data.

## Request account details

Standard account details are requested by default.  [IB Trader Workstation (TWS)](https://www.interactivebrokers.com/en/trading/tws.php)
does not provide an API for requesting all model codes, so [deephaven-ib](https://github.com/deephaven-examples/deephaven-ib)
can not subscribe to data for different model codes.  If you need details on non-standard
account / model code combinations, you can use:
* `request_account_pnl`
* `request_account_overview`
* `request_account_positions`

## Order management

Orders can be created and canceled using:
* `order_place`
* `order_cancel`
* `order_cancel_all`

To place an order, register a contract with [deephaven-ib](https://github.com/deephaven-examples/deephaven-ib),
and create an `ibapi.order.Order` containing details for the order.

Details on creating orders can be found at [https://interactivebrokers.github.io/tws-api/orders.html](https://interactivebrokers.github.io/tws-api/orders.html).

```python
from ibapi.contract import Contract
from ibapi.order import Order

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
order.eTradeOnly = False
order.firmQuoteOnly = False

req = client.order_place(rc, order)
req.cancel()

client.order_place(rc, order)
client.order_cancel_all()
```

## Queries and Mathematics

[Deephaven](https://deephaven.io) has very powerful query engine that allows mathematics and queries 
to be applied to static and real-time data.  The queries can be as simple as filtering data and
as complex as artificial intelligence.

The example below computes the real-time price ratio of `DIA` (Dow Jones Index) and `SPY` (S&P 500 Index)
every 5 seconds.

For more details, see the [Deephaven Coummunity Core Documentation](https://deephaven.io/core/docs/).

```python
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
```

![DIA SPY Ratio](https://raw.githubusercontent.com/deephaven-examples/deephaven-ib/main/docs/assets/dia_spy_ratio.png)

## Plotting

[Deephaven](https://deephaven.io) has very powerful plotting functionality for both static and real-time data.
The example below plots the bid and ask prices of `AAPL` for every tick in the market.

For more details, see the [Deephaven Coummunity Core Documentation](https://deephaven.io/core/docs/).

```python

from ibapi.contract import Contract

c = Contract()
c.symbol = 'AAPL'
c.secType = 'STK'
c.exchange = 'SMART'
c.currency = 'USD'

rc = client.get_registered_contract(c)
print(rc)

client.set_market_data_type(dhib.MarketDataType.REAL_TIME)
client.request_market_data(rc)
client.request_tick_data_realtime(rc, dhib.TickDataType.BID_ASK)

ticks_bid_ask = client.tables["ticks_bid_ask"]

from deephaven.plot import Figure

plot_aapl = Figure().plot_xy("Bid",  t=ticks_bid_ask, x="ReceiveTime", y="BidPrice") \
    .plot_xy("Ask",  t=ticks_bid_ask, x="ReceiveTime", y="AskPrice") \
    .show()
```

![AAPL Bid Ask](https://raw.githubusercontent.com/deephaven-examples/deephaven-ib/main/docs/assets/aapl_bid_ask.png)

## Help!

### Error Table

[deephaven-ib](https://github.com/deephaven-examples/deephaven-ib) logs all [IB Trader Workstation (TWS)](https://www.interactivebrokers.com/en/trading/tws.php)
errors to the `errors` table.  This table should be monitored when using [deephaven-ib](https://github.com/deephaven-examples/deephaven-ib).

```python
errors = client.tables["errors"]
```

### Logging

[deephaven-ib](https://github.com/deephaven-examples/deephaven-ib) and `ibapi` both use Python's 
[`logging`](https://docs.python.org/3/howto/logging.html) framework.  By default, `ERROR` and higher
levels are logged.  More or less logging can be displayed by changing the logging level.

To see fewer log messages:
```python
import logging
logging.basicConfig(level=logging.CRITICAL)
```

To see all log messages:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

A discussion of available logging levels can be found in the [Python `logging` module documentation](https://docs.python.org/3/howto/logging.html).

### Support

If you can not solve your problems through either the `errors` table or through logging, you can try:

* [deephaven-ib API Documentation](https://deephaven-examples.github.io/deephaven-ib/)
* [Interactive Brokers Support](https://www.interactivebrokers.com/en/support/individuals.php)
* [Gitter: A relaxed chat room about all things Deephaven](https://gitter.im/deephaven/deephaven)
* [Deephaven Community Slack](https://deephaven.io/slack)

### `Takes N positional arguments but M were given`

You may encounter an error that looks like: `Takes N positional arguments but M were given`.  
If you see a problem like this, your `ibapi` version does not match the version needed by [deephaven-ib](https://github.com/deephaven-examples/deephaven-ib).  
The [`ibapi` version in PyPI](https://pypi.org/project/ibapi/) is ancient and appears to have been abandoned by [Interactive Brokers](https://www.interactivebrokers.com/).  
Currently [Interactive Brokers](https://www.interactivebrokers.com/) is delivering `ibapi` either via the [IB Trader Workstation (TWS)](https://www.interactivebrokers.com/en/trading/tws.php) 
download or via git. 

To check your `ibapi` version:
```python
import ibapi
print(ibapi.__version__)
```

The `ibapi` API is very unstable.  If your version does not exactly match the version needed by [deephaven-ib](https://github.com/deephaven-examples/deephaven-ib), 
you will need to install the correct version.  Regenerate your virtual environment as described above.

# Examples

Examples can be found in [./examples](./examples).

