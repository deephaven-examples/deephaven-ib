# Build Docker Image From The Most Recent pip-installable Deephaven-IB Release

This directory contains the ingredients to build Docker images from the most recent pip-installable deephaven-ib release.

In general, you will want to use the officially released images at [https://github.com/deephaven-examples/deephaven-ib/pkgs/container/deephaven-ib](https://github.com/deephaven-examples/deephaven-ib/pkgs/container/deephaven-ib).

## Build Image

```bash
./build.sh
```

## Run image in interactive mode

```bash
# Set jvm_args to the desired JVM memory for Deephaven
docker run -it -v data:/data -p 10000:10000 deephaven-examples/deephaven-ib:release python3 -i -c "from deephaven_server import Server; _server = Server(port=10000, jvm_args=['-Xmx4g']); _server.start()"
```
