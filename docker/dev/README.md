# Build Docker Image From Current Deephaven-IB Checkout

This directory contains the ingredients to build Docker images from the current, checked-out deephaven-ib repository.

This is useful when doing local development or when offical images are not available for your platform.

## Build Image

```bash
./build.sh
```

## Run image in interactive mode

```bash
# Set jvm_args to the desired JVM memory for Deephaven
docker run -it -v data:/data --expose 10000 deephaven-examples/deephaven-ib:dev python3 -i -c "from deephaven_server import Server; _server = Server(port=10000, jvm_args=["-Xmx4g"]); _server.start()"
```

