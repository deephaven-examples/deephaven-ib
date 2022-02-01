
# deephaven-ib

<!-- TODO: add an imagge -->

An Interactive Brokers integration for Deephaven.

![Build CI](https://github.com/deephaven-examples/deephaven-ib/actions/workflows/build-and-publish.yml/badge.svg?branch=main)
![Documentation](https://github.com/deephaven-examples/deephaven-ib/actions/workflows/sphinx.yml/badge.svg?branch=main)

# Run deephaven-ib

Follow these setps to run a [Deephaven](https://deephaven.io) plus [Interactive Brokers](https://interactivebrokers.com) system. 

`<deephaven_version>` is the version of [Deephaven](https://deephaven.io) to run (e.g. `0.9.0`).  A list of availble versions 
can be found on the [Deephaven Releases GitHub page](https://github.com/deephaven/deephaven-core/releases).

**Windows users need to run the commands in WSL.**

1) Follow the [Deephaven Quick Start Guide](https://deephaven.io/core/docs/tutorials/quickstart/) to get [Deephaven](https://deephaven.io) running.  
1) Follow the [TWS Installation Instructions](https://www.interactivebrokers.com/en/trading/tws.php) to get [IB Trader Workstation (TWS)](https://www.interactivebrokers.com/en/trading/tws.php) running.
1) Launch [IB Trader Workstation (TWS)](https://www.interactivebrokers.com/en/trading/tws.php).
1) Check out the [deephaven-ib](https://github.com/deephaven-examples/deephaven-ib) repository:
    ```bash
    git clone https://github.com/deephaven-examples/deephaven-ib.git
    cd deephaven-ib
    ```
1) Build the Docker images:
    ```bash
    ./docker/deephaven_ib_docker.sh build --dh-version <deephaven_version>
    ```
1) Launch the system:
    ```bash
    ./docker/deephaven_ib_docker.sh up --dh-version <deephaven_version>
    ```
1) Launch the [Deephaven IDE](https://github.com/deephaven/deephaven-core/blob/main/README.md#run-deephaven-ide) by navigating to [http://localhost:10000/ide/](http://localhost:10000/ide/) in a browser.

To shut down the system:
```bash
./docker/deephaven_ib_docker.sh down --dh-version <deephaven_version>
```

To get help on running the system:
```bash
./docker/deephaven_ib_docker.sh help
```


*** configure IB


# Examples

Look in [./examples](./examples).

#TODO document logging configuration
# logging.basicConfig(level=logging.DEBUG)

#TODO pydoc all modules
#TODO sphinx doc
#TODO: shutdown

Contracts: https://interactivebrokers.github.io/tws-api/basic_contracts.html