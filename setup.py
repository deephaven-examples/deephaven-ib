import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="deephaven-ib",
    version="0.0.1****",
    author="****",
    author_email="****",
    description="****",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="****",
    project_urls={
        "Bug Tracker": "****",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: ****",
        "Operating System :: OS Independent****",
    ]
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.6",
)

