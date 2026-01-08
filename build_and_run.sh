#!/bin/bash

# Convenience script to build a release virtual environment and start the Deephaven server.
# This script automates the process of:
# 1. Creating a temporary installer virtual environment
# 2. Building the release virtual environment with deephaven-ib, deephaven-server, and ibapi
# 3. Starting the Deephaven server
#
# Press Ctrl-C to stop the server when done.

# Display Java home (required for Deephaven)
echo $JAVA_HOME

# Clean up any existing virtual environments
deactivate 2>/dev/null || true  # Deactivate if already in a venv
rm -rf .venv-installer
rm -rf venv-release-dhib*

# Create temporary installer virtual environment
# This small venv is only used to run the dhib_env.py script
python3.12 -m venv .venv-installer
source .venv-installer/bin/activate

# Install dependencies needed to run dhib_env.py
python -m pip install --upgrade pip
pip install -r requirements_dhib_env.txt

# Build the release virtual environment
# This creates venv-release-dhib-<version> with all required packages
python ./dhib_env.py release 

# Clean up temporary installer venv
deactivate
rm -rf .venv-installer

# Activate the release virtual environment and start Deephaven server
source ./venv-release-dhib*/bin/activate
deephaven server
deactivate