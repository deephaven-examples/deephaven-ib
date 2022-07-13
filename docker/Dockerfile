ARG VERSION

FROM ghcr.io/deephaven/server-sklearn:${VERSION}

ARG DH_IB_VERSION
ARG DH_IB_BRANCH

COPY deephaven_ib-0.2.4-py3-none-any.whl /tmp/

# Install requirements
RUN apt update && \
    apt install --yes git python3-venv zip && \
    python3 -m pip install --upgrade pip

RUN mkdir /build && \
    cd /build && \
    curl -o ./api.zip "https://interactivebrokers.github.io/downloads/twsapi_macunix.1016.01.zip" && \ 
    unzip api.zip && \
    cd ./IBJts/source/pythonclient && \
    python3 setup.py install && \
    rm -rf ./build


RUN pip3 install /tmp/deephaven_ib-0.2.4-py3-none-any.whl 

# Invalidate the cache below here, so that the latest repo changes get cloned
ARG CACHEBUST