#!/usr/bin/env bash

# This script is used to build Python wheels for the Interactive Brokers' API.

# Exit script on first error
set -e

# check that IB_VERSION is set
if [ -z "$IB_VERSION" ]; then
  echo "IB_VERSION must be set"
  exit 1
fi

# IB has a funky versioning scheme, so we need to strip out the periods in some places before download
IB_VERSION_DOWNLOAD=$(echo ${IB_VERSION} | sed 's/[.]//')

if [ ! -d "./build" ]; then
  mkdir ./build
fi

if [ ! -d "./dist" ]; then
  mkdir ./dist
fi

rm -rf ./build/*
rm -rf ./dist/*

pushd ./build

python3 -m pip install build

echo "Downloading IB API version ${IB_VERSION} (${IB_VERSION_DOWNLOAD})"
curl -o ./api.zip "https://interactivebrokers.github.io/downloads/twsapi_macunix.${IB_VERSION_DOWNLOAD}.zip"
unzip api.zip
cd ./IBJts/source/pythonclient
python3 -m build --wheel
popd
cp ./build/IBJts/source/pythonclient/dist/* ./dist/

