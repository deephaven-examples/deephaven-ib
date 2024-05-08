import os
import re

import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

dh_ib_version = os.getenv("DH_IB_VERSION")

if not dh_ib_version:
    raise Exception("deephaven-ib version must be set via the DH_IB_VERSION environment variable.")

dh_version = os.getenv("DH_VERSION")

if not dh_version:
    raise Exception("deephaven version must be set via the DH_VERSION environment variable.")

ib_version = os.getenv("IB_VERSION")

if not ib_version:
    raise Exception("ibapi version must be set via the IB_VERSION environment variable.")


def version_assert_format(version: str) -> None:
    """Assert that a version string is formatted correctly.

    Args:
        version: The version string to check.

    Raises:
        ValueError: If the version string is not formatted correctly.
    """
    if not version:
        raise ValueError("Version string is empty.")

    # check if the version string is in semver format
    # check if the version string is in semver format
    pattern1 = re.compile(r"^([0-9]\d*)\.([0-9]\d*)\.([0-9]\d*)$")
    pattern2 = re.compile(r"^([0-9]\d*)\.([0-9]\d*)\.([0-9]\d*)\.dev([0-9]\d*)$")
    is_semver = bool(pattern1.match(version)) or bool(pattern2.match(version))

    if not is_semver:
        raise ValueError(f"Version string is not in semver format: {version}")


version_assert_format(dh_ib_version)
version_assert_format(dh_version)
version_assert_format(ib_version)

setuptools.setup(
    name="deephaven_ib",
    version=dh_ib_version,
    author="David R. (Chip) Kent IV",
    author_email="chipkent@deephaven.io",
    description="An Interactive Brokers integration for Deephaven",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/deephaven-examples/deephaven-ib",
    project_urls={
        "Deephaven": "https://deephaven.io",
        "Deephaven GitHub": "https://github.com/deephaven/deephaven-core",
        "GitHub Issues": "https://github.com/deephaven-examples/deephaven-ib/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Financial and Insurance Industry",
        "Topic :: Database :: Database Engines/Servers",
        "Topic :: Office/Business :: Financial :: Investment",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.10",
    install_requires=[
        f"deephaven-server~={dh_version}",
        "pandas",
        f"ibapi=={ib_version}",
        "lxml",
        "ratelimit",
    ],
)

