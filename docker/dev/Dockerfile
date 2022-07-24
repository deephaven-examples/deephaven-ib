#
# A docker image from the current repository.
#

FROM ubuntu:22.04

ARG DH_IB_VERSION=dev

# Install requirements

RUN apt update && \
    apt install -y openjdk-11-jdk && \
    ln -s /usr/lib/jvm/java-11-openjdk-*/ /usr/lib/jvm/java-11-openjdk && \
    apt install --yes git python3-venv python3-pip && \
    pip3 install --upgrade setuptools wheel build twine

ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk

# Build and install deephaven-ib

COPY ./build /build

RUN cd /build && \
    python3 -m build && \
    pip3 install dist/*.whl && \
    rm -rf /build

CMD python3
