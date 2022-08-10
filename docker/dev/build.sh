#!/bin/bash
#
# Build a docker image from the current repository.
#

__dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd ${__dir}

rm -rf build
mkdir build
rsync -av ../.. build --exclude docker

docker build --build-arg IB_VERSION=1016.01 -t deephaven-examples/deephaven-ib:dev -f Dockerfile .

rm -rf build