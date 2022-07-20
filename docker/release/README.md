# Build Docker Image From The Most Recent pip-installable Deephaven-IB Release

This directory contains the ingredients to build Docker images from the most recent pip-installable deephaven-ib release.

## Build Image

```bash
./build.sh
```

## Run image in interactive mode

```bash
docker run -it -v data:/data --expose 10000 deephaven-examples/deephaven-ib:release
```
