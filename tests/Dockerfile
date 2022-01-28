ARG TAG
FROM ghcr.io/deephaven/server:${TAG}

COPY dist/ /dist

RUN pip install ibapi lxml ratelimit /dist/*.whl