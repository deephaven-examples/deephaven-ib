
FROM ubuntu:22.04

RUN apt update && \
    apt install -y openjdk-11-jdk python3-pip

ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64/

COPY ./wheels /wheels

RUN pip3 install /wheels/*.whl && \
    rm -rf /wheels/

CMD python3