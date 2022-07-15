#!/bin/bash
#
# Build a docker image from the current repository.
#

rm -rf build
mkdir build
cp -r .. build

docker build -t deephaven-examples/deephaven-ib:dev -f Dockerfile.dev .

rm -rf build