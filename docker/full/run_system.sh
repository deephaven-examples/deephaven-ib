#!/usr/bin/env bash
#
# Run the full multi-image Deephaven system with deephaven-ib installed.
#
# Usage: ./run_system.sh <deephaven_ib_version>
#

set -o errexit
set -o pipefail
set -o nounset

__dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd ${__dir}

# get deephaven-ib version to run

if [ $# -eq 0 ]
then
  export DH_IB_VERSION=latest
else
  export DH_IB_VERSION=$1
fi

echo "DH_IB_VERSION=${DH_IB_VERSION}"

# pull images

docker pull ghcr.io/deephaven-examples/deephaven-ib-dhserver:${DH_IB_VERSION}
export DH_VERSION=$(docker inspect --format '{{ index .Config.Labels "deephaven_version" }}' ghcr.io/deephaven-examples/deephaven-ib-dhserver:${DH_IB_VERSION})
echo "DH_VERSION=${DH_VERSION}"
docker-compose pull

# print images being used

docker compose images

# launch

docker-compose up
