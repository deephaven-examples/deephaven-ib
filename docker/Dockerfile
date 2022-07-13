ARG VERSION

FROM ubuntu:22.04
#FROM ghcr.io/deephaven/server:${VERSION}

ARG DH_IB_VERSION
ARG DH_IB_BRANCH

# Install requirements
RUN apt update && \
    apt install --yes git python3-venv && \
    python3 -m pip install --upgrade pip && \
    python3 -m pip install --upgrade setuptools wheel build twine

RUN apt update && \
    apt install -y openjdk-11-jdk

ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64/

# Invalidate the cache below here, so that the latest repo changes get cloned
ARG CACHEBUST

#TODO publish whl
#TODO use whl here
# Build and install deephaven-ib
RUN mkdir /build && \
    cd /build && \
    git clone --branch ${DH_IB_BRANCH} https://github.com/deephaven-examples/deephaven-ib.git && \
    cd deephaven-ib && \
    python3 -m build && \
    pip3 install dist/*.whl && \
    rm -rf /build

#***
## Official Debian + Python image
#FROM python:3.7-bullseye
#
#
#RUN python -m pip install --upgrade pip && \
#    pip install deephaven-server==0.14.0
#
#CMD python

