![Build CI](https://github.com/deephaven-examples/deephaven-ib/actions/workflows/build-and-publish.yml/badge.svg?branch=main)
![Documentation](https://github.com/deephaven-examples/deephaven-ib/actions/workflows/sphinx.yml/badge.svg?branch=main)

# deephaven-ib

An Interactive Brokers integration for Deephaven.

# Quick Start

Build
```bash
./docker/deephaven_ib_docker.sh build
```

Launch
```bash
./docker/deephaven_ib_docker.sh up
```

Shutdown
```bash
./docker/deephaven_ib_docker.sh down
```

Help
```bash
./docker/deephaven_ib_docker.sh help
```

# Examples

Look in [./examples](./examples).

#TODO document logging configuration
# logging.basicConfig(level=logging.DEBUG)

#TODO pydoc all modules
#TODO sphinx doc
#TODO add badges
#TODO: shutdown

Contracts: https://interactivebrokers.github.io/tws-api/basic_contracts.html