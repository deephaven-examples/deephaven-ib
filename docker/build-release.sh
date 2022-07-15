#!/bin/bash
#
# Build a docker image from released python packages
#

docker build -t deephaven-examples/deephaven-ib -f Dockerfile.release .