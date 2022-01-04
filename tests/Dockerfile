ARG TAG
FROM ghcr.io/deephaven/grpc-api:${TAG}

COPY dist/ /dist

RUN pip install ibapi /dist/*.whl