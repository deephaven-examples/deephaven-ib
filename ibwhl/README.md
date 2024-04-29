# Interactive Brokers Python Wheels Builder

This directory provides a Docker Compose setup for building Python wheels for the Interactive Brokers API.

## Requirements

- Docker
- Docker Compose

## Usage

1. Set the `IB_VERSION` environment variable to the version of Interactive Brokers' API you want to use.
2. Run `docker compose up` from the directory containing the Docker Compose file. This will build the wheels.
3. After the build process is complete, the wheels will be available in the `./dist` directory.
4. To install the wheels, run `pip install ./dist/*.whl`.

> **Note:** Steps 1 and 2 can be combined as `IB_VERSION=10.19.04 docker compose up`.

## Details

The build process is defined in the `build_ibpy.sh` script. 
The `./build` directory contains the scratch work for building the wheels.

By using Docker, you can build the wheels in a clean environment that is isolated from your local machine. 
This setup will work on any platform that supports Docker.

## Note

Interactive Brokers does not make their Python wheels available via PyPI, and the wheels are not redistributable. 
This script lets you build the wheels locally, and then install them via pip.