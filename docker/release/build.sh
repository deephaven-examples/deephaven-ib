#!/bin/bash
#
# Build a docker image from released python packages
#

__dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd ${__dir}

docker build --build-arg IB_VERSION=1016.01 -t deephaven-examples/deephaven-ib:release -f Dockerfile .