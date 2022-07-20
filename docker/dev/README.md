# Build Docker Image From Current Deephaven-IB Checkout

This directory contains the ingredients to build Docker images from the current, checked-out deephaven-ib repository.

## Build Image

```bash
./build.sh
```

## Run image in interactive mode

```bash
docker run -it -v data:/data --expose 10000 deephaven-examples/deephaven-ib:dev
```

