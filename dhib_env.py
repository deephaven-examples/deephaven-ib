#!/usr/bin/env python3

""" A script to build a virtual environment for Deephaven-IB development or release."""

import atexit
import logging
import os
import shutil
from pathlib import Path
from types import ModuleType
from typing import Optional, Dict, Union
import click
import pkginfo
import requests

IB_VERSION_DEFAULT="10.19.04"
DH_VERSION_DEFAULT="0.33.3"

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


class Venv:
    """A virtual environment."""

    def __init__(self, is_release: bool, python: str, dh_version: str, ib_version: str, dh_ib_version: str,
                 delete_if_exists: bool):
        """Create a virtual environment.

        Args:
            is_release: Whether the virtual environment is for a release.
            python: The path to the Python executable to use.
            dh_version: The version of Deephaven.
            ib_version: The version of ibapi.
            dh_ib_version: The version of deephaven-ib.
            delete_if_exists: Whether to delete the virtual environment if it already exists.
        """
        if is_release:
            self.path = Path(f"venv-release-dhib={dh_version}").absolute()
        else:
            self.path = Path(f"venv-dev-dhib={dh_ib_version}-dh={dh_version}-ib={ib_version}").absolute()

        logging.warning(f"Building new virtual environment: {self.path}")

        if delete_if_exists and self.path.exists():
            logging.warning(f"Deleting existing virtual environment: {self.path}")
            shutil.rmtree(self.path)

        if self.path.exists():
            logging.error(f"Virtual environment already exists.  Please remove it before running this script. venv={self.path}")
            raise FileExistsError(
                f"Virtual environment already exists.  Please remove it before running this script. venv={self.path}")

        logging.warning(f"Creating virtual environment: {self.path}")
        shell_exec(f"{python} -m venv {self.path}")

        logging.warning(f"Updating virtual environment: {self.path}")
        shell_exec(f"{self.python} -m pip install --upgrade pip")
        shell_exec(f"{self.python} -m pip install --upgrade build")

    @property
    def python(self) -> str:
        """The path to the Python executable in the virtual environment."""
        return os.path.join(self.path, "bin", "python")

    def pip_install(self, package: Union[str, Path], version: Optional[str] = None) -> None:
        """Install a package into the virtual environment.

        Args:
            package: The name of the package to install.
            version: The version of the package to install. If None, the latest version will be installed.
        """
        logging.warning(f"Installing package in venv: {package}, version: {version}, venv: {self.path}")

        if isinstance(package, Path):
            package = package.absolute()

        ver = f"=={version}" if version else ""
        cmd = f"""{self.python} -m pip install {package}{ver}"""
        shell_exec(cmd)


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

    def build(self, v: Venv) -> None:
        """Build the IB wheel.

        Interactive Brokers does not make their Python wheels available via PyPI,
        and the wheels are not redistributable.
        As a result, we need to build the IB wheel locally.

        Args:
            v: The virtual environment to build the wheel in.
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
        shell_exec(f"cd build/ib/IBJts/source/pythonclient && {v.python} -m build --wheel")
        shell_exec("cp build/ib/IBJts/source/pythonclient/dist/* dist/ib/")

    def install(self, v: Venv) -> None:
        """Install the IB wheel into a virtual environment.

        Args:
            v: The virtual environment to install the wheel into.
        """
        logging.warning(f"Installing IB wheel in venv: {self.version} {v.path}")
        ver_narrow = version_str(self.version, False)
        v.pip_install(Path(f"dist/ib/ibapi-{ver_narrow}-py3-none-any.whl").absolute())


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

    def build(self, v: Venv) -> None:
        """Build the deephaven-ib wheel."""
        logging.warning(f"Building deephaven-ib: {self.version}")
        shell_exec(f"DH_IB_VERSION={self.version} DH_VERSION={self.dh_version} IB_VERSION={self.ib_version} {v.python} -m build --wheel")

    def install(self, v: Venv) -> None:
        """Install the deephaven-ib wheel into a virtual environment."""
        logging.warning(f"Installing deephaven-ib in venv: {self.version} {v.path}")
        v.pip_install(Path(f"dist/deephaven_ib-{self.version}-py3-none-any.whl").absolute())


########################################################################################################################
# Messages
########################################################################################################################

def success(v: Venv) -> None:
    """Print a success message.

    Args:
        v: The virtual environment.
    """
    logging.warning(f"Success!  Virtual environment created: {v.path}")
    logging.warning(f"Activate the virtual environment with: source {v.path}/bin/activate")
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
@click.option('--dh_version', default=DH_VERSION_DEFAULT, help='The version of Deephaven.')
@click.option('--ib_version', default=IB_VERSION_DEFAULT, help='The version of ibapi.')
@click.option('--dh_ib_version', default=None, help='The version of deephaven-ib.')
@click.option('--delete_venv', default=False, help='Whether to delete the virtual environment if it already exists.')
def dev(python: str, dh_version: str, ib_version: str, dh_ib_version: Optional[str], delete_venv: bool):
    """Create a development environment."""
    logging.warning(f"Creating development environment: python={python} dh_version={dh_version}, ib_version={ib_version}, dh_ib_version={dh_ib_version}, delete_vm_if_exists={delete_venv}")

    use_dev = dh_ib_version is None

    if dh_ib_version is None:
        dh_ib_version = "0.0.0.dev0"

    v = Venv(False, python, dh_version, ib_version, dh_ib_version, delete_venv)

    ib_wheel = IbWheel(ib_version)
    ib_wheel.build(v)
    ib_wheel.install(v)

    v.pip_install("deephaven-server", dh_version)

    if use_dev:
        logging.warning(f"Building deephaven-ib from source: {dh_ib_version}")
        dh_ib_wheel = DhIbWheel(dh_ib_version, dh_version, ib_version)
        dh_ib_wheel.build(v)
        dh_ib_wheel.install(v)
    else:
        logging.warning(f"Installing deephaven-ib from PyPI: {dh_ib_version}")
        logging.warning(f"*** INSTALLED deephaven-ib MAY BE INCONSISTENT WITH INSTALLED DEPENDENCIES ***")
        v.pip_install("deephaven-ib", dh_ib_version)

    success(v)


@click.command()
@click.option('--python', default="python3", help='The path to the Python executable to use.')
@click.option('--dh_ib_version', default=None, help='The version of deephaven-ib.')
@click.option('--delete_venv', default=False, help='Whether to delete the virtual environment if it already exists.')
def release(python: str, dh_ib_version: Optional[str], delete_venv: bool):
    """Create a release environment."""
    logging.warning(f"Creating release environment: python={python} dh_ib_version={dh_ib_version}")

    wheel = download_wheel(python, "deephaven_ib", dh_ib_version)
    deps = pkg_dependencies(wheel)
    ib_version = deps["ibapi"].replace("==", "")
    dh_version = deps["deephaven-server"].replace("==", "")

    v = Venv(True, python, dh_version, ib_version, dh_ib_version, delete_venv)

    ib_wheel = IbWheel(ib_version)
    ib_wheel.build(v)
    ib_wheel.install(v)

    logging.warning(f"Installing deephaven-ib from PyPI: {dh_ib_version}")
    v.pip_install("deephaven-ib", dh_ib_version)
    success(v)


cli.add_command(dev)
cli.add_command(release)

if __name__ == '__main__':
    cli()
