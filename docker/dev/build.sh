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

IB_VERSION_DEFAULT=10.19.04

if [ -z "$IB_VERSION" ]; then
  echo "Using default IB_VERSION=${IB_VERSION_DEFAULT}"
  IB_VERSION=${IB_VERSION_DEFAULT}
fi

docker build --build-arg DH_VERSION=${DH_VERSION} --build-arg IB_VERSION=${IB_VERSION} -t deephaven-examples/deephaven-ib:dev -f Dockerfile .

rm -rf build