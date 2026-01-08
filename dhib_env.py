#!/usr/bin/env python3

""" A script to build a virtual environment for Deephaven-IB development or release."""

import atexit
import logging
import os
import re
import shutil
from pathlib import Path
from types import ModuleType
from typing import Optional, Dict, Union
import click
import pkginfo
import requests

IB_VERSION_DEFAULT="10.19.04"
DH_VERSION_DEFAULT="0.36.1"
MIN_PY_VERSION="3.10.0"

########################################################################################################################
# Version Numbers
########################################################################################################################


def version_tuple(version: str) -> tuple[int, ...]:
    """Convert a version string to a tuple of integers.

    Args:
        version: The version string to convert.

    Returns:
        A tuple of integers representing the version.
    """
    return tuple(map(int, (version.split("."))))


def version_str(version: tuple[int, ...], wide: bool) -> str:
    """Convert a version tuple to a string.

    Args:
        version: The version tuple to convert.
        wide: Whether to use a wide format that includes leading zeros.

    Returns:
        A string representing the version.
    """
    if wide:
        return ".".join(f"{x:02d}" for x in version)
    else:
        return ".".join(map(str, version))


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
    pattern1 = re.compile(r"^([0-9]\d*)\.([0-9]\d*)\.([0-9]\d*)$")
    pattern2 = re.compile(r"^([0-9]\d*)\.([0-9]\d*)\.([0-9]\d*)\.dev([0-9]\d*)$")
    is_semver = bool(pattern1.match(version)) or bool(pattern2.match(version))

    if not is_semver:
        raise ValueError(f"Version string is not in semver format: {version}")


########################################################################################################################
# Shell
########################################################################################################################


def shell_exec(cmd: str) -> None:
    """Execute a shell command.

    Args:
        cmd: The command to execute.
    """
    logging.warning(f"Executing shell command: {cmd}")
    e = os.system(cmd)

    if e != 0:
        raise Exception(f"Error executing shell command: {cmd}")


########################################################################################################################
# URL
########################################################################################################################


def url_download(url: str, path: Union[str, Path]) -> None:
    """Download a file from a URL.

    Args:
        url: The URL to download from.
        path: The path to save the downloaded file to.
    """
    logging.warning(f"Downloading file: {url}, path: {path}")
    response = requests.get(url)
    response.raise_for_status()

    with open(path, "wb") as f:
        f.write(response.content)


########################################################################################################################
# Package Query Functions
########################################################################################################################


def delete_file_on_exit(file_path: Union[str, Path]) -> None:
    """Register a file to be deleted on program exit."""

    def delete_file():
        if os.path.exists(file_path):
            os.remove(file_path)
            logging.debug(f"{file_path} has been deleted.")

    atexit.register(delete_file)


def download_wheel(python: str, package: str, version: Optional[str], delete_on_exit: bool = True) -> Path:
    """Download a wheel file for a package with a specific version.

    Args:
        python: The path to the Python executable to use.
        package: The name of the package to download.
        version: The version of the package to download. If None, the latest version will be downloaded.
        delete_on_exit: Whether to delete the wheel file on program exit.

    Returns:
        The path of the downloaded wheel file.

    Raises:
        subprocess.CalledProcessError: If the download process fails.
    """
    logging.warning(f"Downloading wheel for package: {package}, version: {version}, delete_on_exit: {delete_on_exit}")

    if not version:
        logging.warning(f"Determining latest version of package: {package}")
        response = requests.get(f"https://pypi.org/pypi/{package}/json")
        response.raise_for_status()
        version = response.json()["info"]["version"]

    ver = f"=={version}" if version else ""
    shell_exec(f"{python} -m pip download {package}{ver} --no-deps")
    p = Path(f"{package}-{version}-py3-none-any.whl").absolute()

    if delete_on_exit:
        delete_file_on_exit(str(p))

    return p


def pkg_dependencies(path_or_module: Union[str, Path, ModuleType]) -> Dict[str, Optional[str]]:
    """Get the dependencies of a package.

    Args:
        path_or_module: The path to the package or the module object.

    Returns:
        A dictionary containing the dependencies of the package and their version specifications.
    """

    if isinstance(path_or_module, Path):
        path_or_module = str(path_or_module)

    meta = pkginfo.get_metadata(path_or_module)

    if not meta:
        raise ValueError(f"Package could not be found: {path_or_module}")

    rst = {}

    for req in meta.requires_dist:
        s = req.split(" ")
        name = s[0]

        if len(s) > 1:
            version = s[1].strip("()")
        else:
            version = None

        rst[name] = version

    return rst


########################################################################################################################
# Venv
########################################################################################################################


def python_version(python: str) -> tuple[int, ...]:
    """Get the version of Python.

    Args:
        python: The path to the Python executable.

    Returns:
        A tuple of integers representing the version of Python.
    """
    cmd = f"{python} --version"
    logging.warning(f"Getting Python version: {cmd}")
    version = os.popen(cmd).read().strip().split(" ")[1]
    return version_tuple(version)

def assert_python_version(python: str) -> None:
    """Assert that the version of Python is at least the minimum required version.

    Args:
        python: The path to the Python executable.

    Raises:
        ValueError: If the version of Python is less than the minimum required version.
    """
    version = python_version(python)
    min_version = version_tuple(MIN_PY_VERSION)

    if version < min_version:
        raise ValueError(f"Python version {version_str(version, True)} is less than the minimum required version {version_str(min_version, True)}.")


class Pyenv:
    """A python environment."""

    def __init__(self, python: str):
        """Create a python environment.

        Args:
            python: The path to the Python executable.
        """
        self._python = python

    @property
    def python(self) -> str:
        """The path to the Python executable in the virtual environment."""
        return self._python

    def pip_install(self, package: Union[str, Path], version: str = "") -> None:
        """Install a package into the virtual environment.

        Args:
            package: The name of the package to install.
            version: The version constraint of the package to install. If None, the latest version will be installed.
                For example, provide "==1.2.3" to install version 1.2.3.
        """
        logging.warning(f"Installing package in environment: {package}, version: {version}, python: {self.python}")

        if isinstance(package, Path):
            package = package.absolute()

        cmd = f"""{self.python} -m pip install {package}{version}"""
        shell_exec(cmd)


class Venv(Pyenv):
    """A Python virtual environment."""

    def __init__(self, path: Path):
        """Create a virtual environment.

        Args:
            path: The path to the virtual environment.
        """
        super().__init__(os.path.join(path, "bin", "python"))
        self.path = path


def new_venv(path: Path, python: str, delete_if_exists: bool) -> Venv:
    """Create a new virtual environment.

    Args:
        path: The path to the virtual environment.
        python: The path to the Python executable to use.
        delete_if_exists: Whether to delete the virtual environment if it already exists.

    Returns:
        The new virtual environment.
    """

    logging.warning(f"Building new virtual environment: {path}")

    if delete_if_exists and path.exists():
        logging.warning(f"Deleting existing virtual environment: {path}")
        shutil.rmtree(path)

    if path.exists():
        logging.error(
            f"Virtual environment already exists.  Please remove it before running this script. venv={path}")
        raise FileExistsError(
            f"Virtual environment already exists.  Please remove it before running this script. venv={path}")

    logging.warning(f"Creating virtual environment: {path}")
    shell_exec(f"{python} -m venv {path}")

    v = Venv(path)

    logging.warning(f"Updating virtual environment: {path}")
    shell_exec(f"{v.python} -m pip install --upgrade pip")
    shell_exec(f"{v.python} -m pip install --upgrade build")

    return v


def venv_path(is_release: bool, dh_version: str, dh_ib_version: str) -> Path:
    """Get the standard path to a new virtual environment.

    Args:
        is_release: Whether the virtual environment is for a release.
        dh_version: The version of Deephaven.
        dh_ib_version: The version of deephaven-ib.

    Returns:
        The path to the new virtual environment.
    """
    if is_release:
        return Path(f"venv-release-dhib={dh_version}").absolute()
    else:
        return Path(f"venv-dev-dhib={dh_ib_version}-dh={dh_version}").absolute()


########################################################################################################################
# IB Wheel
########################################################################################################################

class IbWheel:
    def __init__(self, version: str):
        """Create an IB wheel.

        Args:
            version: The version of the IB wheel.
        """
        self.version = version_tuple(version)

    def build(self, pyenv: Pyenv) -> None:
        """Build the IB wheel.

        Interactive Brokers does not make their Python wheels available via PyPI,
        and the wheels are not redistributable.
        As a result, we need to build the IB wheel locally.

        Args:
            pyenv: The python environment to build the wheel in.
        """
        logging.warning(f"Building IB wheel: {self.version}")

        shutil.rmtree("build/ib", ignore_errors=True)
        shutil.rmtree("dist/ib", ignore_errors=True)

        os.makedirs("build/ib", exist_ok=True)
        os.makedirs("dist/ib", exist_ok=True)

        logging.warning(f"Downloading IB API version {self.version}")
        ver_ib = f"{self.version[0]:02d}{self.version[1]:02d}.{self.version[2]:02d}"
        url_download(f"https://interactivebrokers.github.io/downloads/twsapi_macunix.{ver_ib}.zip", "build/ib/api.zip")

        logging.warning(f"Unzipping IB API")
        shell_exec("cd build/ib && unzip api.zip")

        logging.warning(f"Building IB Python API")
        shell_exec(f"cd build/ib/IBJts/source/pythonclient && {pyenv.python} -m build --wheel")
        shell_exec("cp build/ib/IBJts/source/pythonclient/dist/* dist/ib/")

    @property
    def path(self) -> Path:
        """The path to the IB wheel."""
        return Path(f"dist/ib/ibapi-{version_str(self.version, False)}-py3-none-any.whl").absolute()

    def install(self, pyenv: Pyenv) -> None:
        """Install the IB wheel into a virtual environment.

        Args:
            pyenv: The python environment to install the wheel into.
        """
        logging.warning(f"Installing IB wheel in python environment: {self.version} python: {pyenv.python}")
        ver_narrow = version_str(self.version, False)
        pyenv.pip_install(self.path)


########################################################################################################################
# deephaven-ib
########################################################################################################################

class DhIbWheel:
    def __init__(self, version: str, dh_version: str, ib_version: str):
        """Create a deephaven-ib wheel.

        Args:
            version: The version of the deephaven-ib wheel.
            dh_version: The version of Deephaven.
            ib_version: The version of ibapi.
        """
        self.version = version
        self.dh_version = dh_version
        self.ib_version = ib_version

    def build(self, pyenv: Pyenv) -> None:
        """Build the deephaven-ib wheel."""
        logging.warning(f"Building deephaven-ib: {self.version}")
        shell_exec(f"DH_IB_VERSION={self.version} DH_VERSION={self.dh_version} IB_VERSION={self.ib_version} {pyenv.python} -m build --wheel")

    @property
    def path(self) -> Path:
        """The path to the deephaven-ib wheel."""
        return Path(f"dist/deephaven_ib-{self.version}-py3-none-any.whl").absolute()

    def install(self, pyenv: Pyenv) -> None:
        """Install the deephaven-ib wheel into a virtual environment."""
        logging.warning(f"Installing deephaven-ib in python environment: {self.version} python: {pyenv.python}")
        pyenv.pip_install(self.path)


########################################################################################################################
# Messages
########################################################################################################################

def success(pyenv: Pyenv) -> None:
    """Print a success message.

    Args:
        pyenv: The python environment.
    """
    logging.warning("Deephaven-ib environment created successfully.")
    logging.warning(f"Python environment: {pyenv.python}")

    if isinstance(pyenv, Venv):
        logging.warning(f"Success!  Virtual environment created: {pyenv.path}")
        logging.warning(f"Activate the virtual environment with: source {pyenv.path}/bin/activate")
        logging.warning(f"Deactivate the virtual environment with: deactivate")


########################################################################################################################
# Click CLI
########################################################################################################################


@click.group()
def cli():
    """A script to build Deephaven-IB virtual environments."""
    pass


@click.command()
@click.option('--python', default="python3", help='The path to the Python executable to use.')
@click.option('--ib_version', default=IB_VERSION_DEFAULT, help='The version of ibapi.')
def ib_wheel(
        python: str,
        ib_version: str,
):
    """Create an ibapi wheel."""
    logging.warning(f"Creating an ib wheel: python={python}, ib_version={ib_version}")

    version_assert_format(ib_version)

    python = Path(python).absolute() if python.startswith("./") else python
    logging.warning(f"Using system python: {python}")
    assert_python_version(python)

    pyenv = Pyenv(python)

    ib_wheel = IbWheel(ib_version)
    ib_wheel.build(pyenv)

    logging.warning(f"IB wheel created successfully.")
    logging.warning(f"IB wheel path: {ib_wheel.path}")


@click.command()
@click.option('--python', default="python3", help='The path to the Python executable to use.')
@click.option('--dh_version', default=DH_VERSION_DEFAULT, help='The version of Deephaven.')
@click.option('--ib_version', default=IB_VERSION_DEFAULT, help='The version of ibapi.')
@click.option('--dh_ib_version', default=None, help='The version of deephaven-ib.')
def dhib_wheel(
        python: str,
        dh_version: str,
        ib_version: str,
        dh_ib_version: Optional[str],
):
    """Create a deephaven-ib wheel."""
    logging.warning(f"Creating a deephaven-ib wheel: python={python}, ib_version={ib_version} dh_version={dh_version}, dh_ib_version={dh_ib_version}")

    if dh_ib_version is None:
        dh_ib_version = "0.0.0.dev0"

    version_assert_format(ib_version)
    version_assert_format(dh_version)
    version_assert_format(dh_ib_version)

    python = Path(python).absolute() if python.startswith("./") else python
    logging.warning(f"Using system python: {python}")
    assert_python_version(python)

    pyenv = Pyenv(python)

    logging.warning(f"Building deephaven-ib from source: {dh_ib_version}")
    dh_ib_wheel = DhIbWheel(dh_ib_version, dh_version, ib_version)
    dh_ib_wheel.build(pyenv)

    logging.warning(f"Deephaven-ib wheel created successfully.")
    logging.warning(f"Deephaven-ib wheel path: {dh_ib_wheel.path}")


@click.command()
@click.option('--python', default="python3", help='The path to the Python executable to use.')
@click.option('--dh_version', default=DH_VERSION_DEFAULT, help='The version of Deephaven.')
@click.option('--dh_version_exact', default=None, help='The exact version of Deephaven.')
@click.option('--ib_version', default=IB_VERSION_DEFAULT, help='The version of ibapi.')
@click.option('--dh_ib_version', default=None, help='The version of deephaven-ib.')
@click.option('--use_venv', default=True, help='Whether to use a python virtual environment or system python.')
@click.option('--path_venv', default=None, help='The path to the virtual environment.')
@click.option('--create_venv', default=True, help='Whether to create the virtual environment if it does not already exist.')
@click.option('--delete_venv', default=False, help='Whether to delete the virtual environment if it already exists.')
@click.option('--install_dhib', default=True, help='Whether to install deephaven-ib.  If set to false, the resulting venv can be used to develop deephaven-ib in PyCharm or other development environments.')
def dev(
        python: str,
        dh_version: str,
        dh_version_exact: str,
        ib_version: str,
        dh_ib_version: Optional[str],
        use_venv: bool,
        path_venv: Optional[str],
        create_venv: bool,
        delete_venv: bool,
        install_dhib: bool
):
    """Create a development environment."""
    logging.warning(f"Creating development environment: python={python} dh_version={dh_version}, dh_version_exact={dh_version_exact}, ib_version={ib_version}, dh_ib_version={dh_ib_version}, delete_vm_if_exists={delete_venv}")

    python = Path(python).absolute() if python.startswith("./") else python
    assert_python_version(python)

    if dh_version_exact:
        if dh_version != DH_VERSION_DEFAULT:
            raise ValueError(f"Cannot specify both dh_version={dh_version} and dh_version_exact={dh_version_exact}")

        dh_version = dh_version_exact
        dh_version_pip = f"=={dh_version}"
    else:
        dh_version_pip = f"~={dh_version}"

    use_dev = dh_ib_version is None

    if dh_ib_version is None:
        dh_ib_version = "0.0.0.dev0"

    version_assert_format(dh_version)
    version_assert_format(ib_version)
    version_assert_format(dh_ib_version)

    if use_venv:
        if path_venv:
            v_path = Path(path_venv).absolute()
        else:
            v_path = venv_path(False, dh_version, dh_ib_version)

        if create_venv:
            pyenv = new_venv(v_path, python, delete_venv)
        else:
            pyenv = Venv(v_path)
    else:
        logging.warning(f"Using system python: {python}")
        pyenv = Pyenv(python)

    ib_wheel = IbWheel(ib_version)
    ib_wheel.build(pyenv)
    ib_wheel.install(pyenv)

    pyenv.pip_install("deephaven-server", dh_version_pip)

    if install_dhib:
        if use_dev:
            logging.warning(f"Building deephaven-ib from source: {dh_ib_version}")
            dh_ib_wheel = DhIbWheel(dh_ib_version, dh_version, ib_version)
            dh_ib_wheel.build(pyenv)
            dh_ib_wheel.install(pyenv)
        else:
            logging.warning(f"Installing deephaven-ib from PyPI: {dh_ib_version}")
            logging.warning(f"*** INSTALLED deephaven-ib MAY BE INCONSISTENT WITH INSTALLED DEPENDENCIES ***")
            pyenv.pip_install("deephaven-ib", f"=={dh_ib_version}")

    success(pyenv)


@click.command()
@click.option('--python', default="python3", help='The path to the Python executable to use.')
@click.option('--dh_ib_version', default=None, help='The version of deephaven-ib.')
@click.option('--use_venv', default=True, help='Whether to use a python virtual environment or system python.')
@click.option('--path_venv', default=None, help='The path to the virtual environment.')
@click.option('--create_venv', default=True, help='Whether to create the virtual environment if it does not already exist.')
@click.option('--delete_venv', default=False, help='Whether to delete the virtual environment if it already exists.')
def release(
        python: str,
        dh_ib_version: Optional[str],
        use_venv: bool,
        path_venv: Optional[str],
        create_venv: bool,
        delete_venv: bool
):
    """Create a release environment."""
    logging.warning(f"Creating release environment: python={python} dh_ib_version={dh_ib_version}")

    python = Path(python).absolute() if python.startswith("./") else python
    assert_python_version(python)

    wheel = download_wheel(python, "deephaven_ib", dh_ib_version)
    deps = pkg_dependencies(wheel)
    ib_version = deps["ibapi"].replace("==", "")
    dh_version = deps["deephaven-server"].replace("==", "").replace("~=", "").replace(">=", "")

    version_assert_format(dh_version)
    version_assert_format(ib_version)

    if dh_ib_version:
        version_assert_format(dh_ib_version)
        dh_ib_version_pip = f"=={dh_ib_version}"
    else:
        dh_ib_version_pip = ""

    if use_venv:
        if path_venv:
            v_path = Path(path_venv).absolute()
        else:
            v_path = venv_path(True, dh_version, dh_ib_version)

        if create_venv:
            pyenv = new_venv(v_path, python, delete_venv)
        else:
            pyenv = Venv(v_path)
    else:
        logging.warning(f"Using system python: {python}")
        pyenv = Pyenv(python)

    ib_wheel = IbWheel(ib_version)
    ib_wheel.build(pyenv)
    ib_wheel.install(pyenv)

    logging.warning(f"Installing deephaven-ib from PyPI: {dh_ib_version}")
    pyenv.pip_install("deephaven-ib", dh_ib_version_pip)
    success(pyenv)


cli.add_command(ib_wheel)
cli.add_command(dhib_wheel)
cli.add_command(dev)
cli.add_command(release)

if __name__ == '__main__':
    cli()
