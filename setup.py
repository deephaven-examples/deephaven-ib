import os

import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

dh_ib_version = os.getenv("DH_IB_VERSION")

if not dh_ib_version:
    raise Exception("deephaven-ib version must be set via the DH_IB_VERSION environment varialble.")

dh_version = os.getenv("DH_VERSION")

if not dh_version:
    raise Exception("deephaven version must be set via the DH_VERSION environment varialble.")

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
    python_requires=">=3.6",
    install_requires=[
        f"deephaven-server=={dh_version}",
        "pandas",
        "ibapi==10.16.1",
        "lxml",
        "ratelimit",
    ],
)

