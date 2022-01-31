#!/usr/bin/env bash

set -o errexit
set -o pipefail
set -o nounset

__dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
__dir_root=${__dir}/../
__dir_docker=${__dir}/../docker/

function up() {
    IS_LOCAL_DEV=$1

    if [ ${IS_LOCAL_DEV} -eq 1 ]
    then
        cd ${__dir_root}

        export DH_IB_VERSION=development
        #TODO: will build work if they don't have deephaven or jpy installed?
        python3 -m pip install --upgrade build
        python3 -m build
    else
        #TODO: pull from pypi?  publish docker image??
        echo "TODO: pull from pypi --- need to implement ---"
        help
    fi

    cd ${__dir_docker}
    echo "DEBUG: In ${__dir_docker}"

    cp -r ../dist .
    #TODO: make this pull stuff into another command? --- make explicit pulls
#    docker-compose pull --ignore-pull-failures --quiet
    docker pull ghcr.io/deephaven/server:${VERSION:-latest}
    docker build --build-arg TAG=${VERSION:-latest} --tag deephaven-ib .
    rm -rf dist

    docker-compose up -d
}

function down() {
    cd ${__dir_docker}
    docker-compose down -v
}

function help() {
    file_name=`basename "$0"`
    echo "Usage: ${file_name} <up|down|help> [--local-dev]"
    echo "up - launch the system"
    echo "down - shut down the system"
    echo "help - print a help message"
    echo "--local-dev - local development mode"
    exit -1
}

if [[ $# -eq 0 ]] ; then
    help
fi

ACTION=$1
LOCAL_DEV=0

for arg in ${@:2}
do
   case $arg in
      "--local-dev" )
          LOCAL_DEV=1
          ;;
      *)
        help
        ;;
   esac
done

case "$ACTION" in
    "up")
        up ${LOCAL_DEV}
        ;;
    "down")
        down
        ;;
    *)
        help
        ;;
esac