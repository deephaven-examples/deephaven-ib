#!/bin/bash
#
# Build a docker image from released python packages
#

__dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd ${__dir}

docker build -t deephaven-examples/deephaven-ib:release -f Dockerfile .