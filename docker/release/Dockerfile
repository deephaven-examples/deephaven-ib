#
# A docker image from released python packages
#

FROM ubuntu:22.04

RUN apt update && \
    apt install -y openjdk-11-jdk python3-pip && \
    ln -s /usr/lib/jvm/java-11-openjdk-*/ /usr/lib/jvm/java-11-openjdk && \

ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk/

RUN pip3 install deephaven-ib

CMD python3