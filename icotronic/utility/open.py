"""Support for opening (text) files in default application"""

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

    # fmt: off
    # pylint: disable=no-name-in-module, import-outside-toplevel
    from os import startfile  # type: ignore[attr-defined]
    # pylint: enable=no-name-in-module, import-outside-toplevel
    # fmt: on

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
    >>> from platform import system
    >>> from os import environ
    >>> def test():
    ...     with as_file(
    ...         files("icotronic.config").joinpath("config.yaml")
    ...     ) as repo_config_file:
    ...         open_file(repo_config_file)

    We only run the test in a graphical environments on Linux, since
    otherwise `xdg-open` will block while opening a CLI util to open the
    YAML config file.

    >>> if system() != "Linux" or environ.get("DISPLAY"):
    ...     test()

    """

    # Some tool (e.g. `xdg-open` in WSL) do not fail, even when we try to open
    # a non-existent file. We add this check to work around this behavior.
    if not Path(filepath).exists():
        raise UnableToOpenError(f"File “{filepath}” does not exist")

    if system() == "Windows":
        open_file_windows(filepath)
    else:
        open_file_other(filepath)


# -- Main ---------------------------------------------------------------------

if __name__ == "__main__":
    from doctest import testmod

    testmod()
