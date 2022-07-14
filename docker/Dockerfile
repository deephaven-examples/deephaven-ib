ARG VERSION

FROM ghcr.io/deephaven/server:${VERSION}

ARG DH_IB_VERSION
ARG DH_IB_BRANCH

# Install requirements
RUN apt update && \
    apt install --yes git python3-venv zip && \
    python3 -m pip install --upgrade pip && \
    python3 -m pip install --upgrade setuptools wheel build twine


RUN mkdir /build && \
    cd /build && \
    curl -o ./api.zip "https://interactivebrokers.github.io/downloads/twsapi_macunix.1016.01.zip" && \ 
    unzip api && \
    cd ./IBJts/source/pythonclient && \
    python3 setup.py install 
    
# Invalidate the cache below here, so that the latest repo changes get cloned
ARG CACHEBUST

RUN git clone --branch ${DH_IB_BRANCH} https://github.com/Firelement/deephaven-ib.git && \
    cd deephaven-ib && \
    python3 -m build && \
    pip3 install dist/*.whl && \
    rm -rf /build && \
    ls -l

