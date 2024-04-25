#
# A docker image from the current repository.
#

FROM ubuntu:22.04

ARG DH_IB_VERSION=0.0.0dev
ARG IB_VERSION
ARG DH_VERSION

# Install requirements

RUN apt update && \
    apt install -y openjdk-17-jdk && \
    ln -s /usr/lib/jvm/java-17-openjdk-*/ /usr/lib/jvm/java-17-openjdk && \
    apt install --yes git python3-venv python3-pip curl unzip && \
    pip3 install --upgrade pip setuptools wheel build

ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk

# Build and install ibapi

RUN mkdir /build && \
    cd /build && \
    IB_VERSION_DOWNLOAD=$(echo ${IB_VERSION} | sed 's/[.]//') && \
    echo "Downloading IB API version ${IB_VERSION_DOWNLOAD}" && \
    curl -o ./api.zip "https://interactivebrokers.github.io/downloads/twsapi_macunix.${IB_VERSION_DOWNLOAD}.zip" && \
    unzip api.zip && \
    cd ./IBJts/source/pythonclient && \
    python3 setup.py install && \
    cd / && \
    rm -rf /build

# Build and install deephaven-ib

COPY ./build /build

RUN cd /build && \
    python3 -m build && \
    pip3 install dist/*.whl && \
    rm -rf /build

CMD python3
