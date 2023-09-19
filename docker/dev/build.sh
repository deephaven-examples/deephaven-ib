#!/bin/bash
#
# Build a docker image from the current repository.
#

__dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd ${__dir}

rm -rf build
mkdir build
rsync -av ../.. build --exclude docker
rm -rf build/dist

if [ -z "$DH_VERSION" ]; then
  echo "DH_VERSION must be set"
  exit 1
fi

docker build --build-arg DH_VERSION=${DH_VERSION} --build-arg IB_VERSION=1016.01 -t deephaven-examples/deephaven-ib:dev -f Dockerfile .

rm -rf build