
FROM ubuntu:22.04

ARG IB_VERSION

RUN apt update && \
    apt install -y openjdk-11-jdk python3-pip curl zip && \
    pip3 install --upgrade pip setuptools wheel

ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64/

RUN mkdir /build && \
    cd /build && \
    curl -o ./api.zip "https://interactivebrokers.github.io/downloads/twsapi_macunix.${IB_VERSION}.zip" && \
    unzip api.zip && \
    cd ./IBJts/source/pythonclient && \
    python3 setup.py install && \
    cd / && \
    rm -rf /build

COPY ./wheels /wheels

RUN pip3 install /wheels/*.whl && \
    rm -rf /wheels/

CMD python3