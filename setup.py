import os

import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

version = os.getenv("DH_IB_VERSION")

if not version:
    raise Exception("Version must be set via the DH_IB_VERSION environment varialble.")

setuptools.setup(
    name="deephaven_ib",
    version=version,
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
        "deephaven-server",
        "pandas",
        "ibapi",
        "lxml",
        "ratelimit",
    ],
)

