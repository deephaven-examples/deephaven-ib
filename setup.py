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


# def is_semver(version):
#     """
#     Checks if a string is in valid semver format.

#     Args:
#       version: The string to validate.

#     Returns:
#       True if the string is in valid semver format, False otherwise.
#     """

#     # Split the version string into components
#     components = version.split(".")

#     # Check for basic structure (3 components)
#     if len(components) != 3:
#         return False

#     # Validate each component as a non-negative integer
#     try:
#         for component in components:
#             if int(component) < 0:
#                 return False
#     except ValueError:
#         return False

#     # Check for optional pre-release and build identifiers
#     if "-" in version:
#         pre_release, build = version.split("-")
#         # Pre-release can be alphanumeric with hyphens or numeric with dots
#         if not (pre_release.isalnum() and all(c in "-.0123456789" for c in pre_release) or all(c.isdigit() for c in pre_release.split("."))):
#             return False
#     else:
#         pre_release = None

#     if "+" in version:
#         if pre_release is None:
#             return False  # Plus sign requires pre-release identifier
#         build = version.split("+")[-1]
#         # Build can be alphanumeric with hyphens
#         if not build.isalnum() and not all(c in "-" for c in build):
#             return False
#     else:
#         build = None

#     return True

_semver_regex = r"""
^
(?P<major>\d+)\.
(?P<minor>\d+)\.
(?P<patch>\d+)
(?:
  -(?P<prerelease>
    (?:[a-z][a-z0-9-]*)
    |(?:[0-9]+(?:\.[0-9]+)*)
  )
)?
(?:\+(?P<build>[a-z0-9]+(?:-[a-z0-9]+)*))?
$
"""


def is_semver(version):
    """
    Checks if a string is in valid semver format.

    Args:
        version: The string to validate.

    Returns:
        True if the string is in semver format, False otherwise.
    """
    match = re.match(_semver_regex, version, re.VERBOSE)
    return match is not None


def version_assert_format(version: str) -> None:
    """Assert that a version string is formatted correctly.

    Args:
        version: The version string to check.

    Raises:
        ValueError: If the version string is not formatted correctly.
    """
    if not version:
        raise ValueError("Version string is empty.")

    if not is_semver(version):
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

