# Run the full multi-image Deephaven system with deephaven-ib installed

This directory contains the ingredients to run the full multi-image Deephaven system with deephaven-ib installed.

This is useful when you need all features in the Deephaven IDE.

To find a list of available deephaven-ib versions, see [https://github.com/deephaven-examples/deephaven-ib/pkgs/container/deephaven-ib-dhserver](https://github.com/deephaven-examples/deephaven-ib/pkgs/container/deephaven-ib-dhserver).

## Run 

```bash
# Edit docker-compose.yml to set desired JVM memory and other Deephaven configurations
./run_system.sh <deephaven_ib_version>
```

