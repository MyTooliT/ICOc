# -- Imports ------------------------------------------------------------------

from pathlib import Path
from platform import system
from subprocess import CalledProcessError, run
from typing import Union

# -- Classes ------------------------------------------------------------------


class UnableToOpenError(Exception):
    """Exception for errors that occur when opening a file in default app"""


# -- Functions ----------------------------------------------------------------


def open_file_windows(filepath: Union[Path, str]) -> None:
    """Open the given file in the default application on Windows

    Arguments
    ---------

    filepath:
        Location of the file that should be opened

    Raises
    ------

    An `UnableToOpenError` if opening the file failed

    """

    from os import startfile  # type: ignore[attr-defined]

    try:
        startfile(filepath)
    except FileNotFoundError as error:
        raise UnableToOpenError(f"File “{filepath}” does not exist") from error


def open_file_other(filepath: Union[Path, str]) -> None:
    """Open the given file in the default application on a non-Windows OS

    Arguments
    ---------

    filepath:
        Location of the file that should be opened

    Raises
    ------

    An `UnableToOpenError` if opening the file failed

    """

    try:
        command = "/usr/bin/open" if system() == "Darwin" else "xdg-open"
        run([command, filepath], capture_output=True, check=True, text=True)

    except CalledProcessError as error:
        raise UnableToOpenError(f"{error.stderr}") from error
    except FileNotFoundError as error:
        raise UnableToOpenError(
            f"Command “{command}” does not exist"
        ) from error


def open_file(filepath: Union[Path, str]) -> None:
    """Open the given file in the default application

    Arguments
    ---------

    filepath:
        Location of the file that should be opened

    Raises
    ------

    An `UnableToOpenError` if opening the file failed

    Examples
    --------

    Open (hopefully) non-existing file

    >>> try:
    ...     open_file("does-not-exist.txt")
    ... except UnableToOpenError:
    ...     print("UnableToOpenError")
    UnableToOpenError

    Open existing file

    >>> from importlib.resources import as_file, files
    >>> with as_file(
    ...     files("mytoolit.config").joinpath("config.yaml")
    ... ) as repo_config_file:
    ...      open_file(repo_config_file)

    """

    if system() == "Windows":
        open_file_windows(filepath)
    else:
        open_file_other(filepath)

