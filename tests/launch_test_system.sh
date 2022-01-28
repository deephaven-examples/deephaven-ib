#!/usr/bin/env bash

set -o errexit
set -o pipefail
set -o nounset

__dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"


export DH_IB_VERSION=development

cd ${__dir}/..

python3 -m pip install --upgrade build
python3 -m build

cd ${__dir}

cp -r ../dist .
docker-compose pull --ignore-pull-failures
docker pull ghcr.io/deephaven/server:${VERSION:-latest}
docker build --build-arg TAG=${VERSION:-latest} --tag deephaven-ib "${__dir}"
rm -rf dist

docker-compose up -d