#!/usr/bin/env bash

set -o errexit
set -o pipefail
set -o nounset

__dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

function build() {
    cd ${__dir}
    docker-compose pull
    #TODO: get rid of --no-cache
    docker-compose build --no-cache
}

function up() {
    cd ${__dir}
    docker-compose up -d
}

function down() {
    cd ${__dir}
    docker-compose down -v
}

function help() {
    file_name=`basename "$0"`
    echo "Usage: ${file_name} <build|up|down|help> [--dh-version <tag>] [--branch <branch>]"
    echo ""
    echo "${file_name} controls deephaven-ib Docker deployments."
    echo "The latest deephaven-ib for a branch is downloaded from GitHub.  Local changes are ignored."
    echo "User data is stored in ./docker/data"
    echo ""
    echo "Modes:"
    echo "------"
    echo "build - build Docker images for the system"
    echo "up - launch the system"
    echo "down - shut down the system"
    echo "help - print a help message"
    echo ""
    echo "Options:"
    echo "--------"
    echo "--dh-version <tag> - deephaven image versions to use"
    echo "--branch <branch> - deephaven-ib branch to use"
    exit -1
}

if [[ $# -eq 0 ]] ; then
    help
fi

ACTION=$1
shift
VERSION=latest
DH_IB_BRANCH=main

while [[ $# -gt 0 ]]; do
   case $1 in
      "--dh-version")
          shift
          VERSION=$1
          ;;
      "--branch")
          shift
          DH_IB_BRANCH=$1
          ;;
      *)
        help
        ;;
   esac
   shift
done

echo "ACTION=${ACTION}"
echo "DH_VERSION=${VERSION}"
echo "DH_IB_BRANCH=${DH_IB_BRANCH}"

case "$ACTION" in
    "build")
        build
        ;;
    "up")
        up
        ;;
    "down")
        down
        ;;
    *)
        help
        ;;
esac