"""Utility functions for working with log data"""

# -- Imports ------------------------------------------------------------------

from logging import FileHandler, Formatter
from platformdirs import user_log_path

from mytoolit.config import ConfigurationUtility

# -- Functions ----------------------------------------------------------------


def get_log_file_handler(filename: str) -> FileHandler:
    """Get file log handler that stores data in users log directory

    Parameters
    ----------

    filename:
        The filename of the log file that should be stored in the user’s log
        directory

    Example
    -------

    Init the logger

    >>> from logging import getLogger
    >>> from re import match
    >>> logger = getLogger("test")
    >>> logger.addHandler(get_log_file_handler("test.log"))

    The log file should not exist until we add something to it

    >>> log_filepath = user_log_path(
    ...     appname=ConfigurationUtility.app_name,
    ...     appauthor=ConfigurationUtility.app_author) / "test.log"
    >>> log_filepath.exists()
    False

    The log file should exist after we add log information

    >>> logger.error("We are all gonna die")
    >>> log_filepath.exists()
    True

    The log file should contain the relevant logging information

    >>> log_content = open(log_filepath, encoding="utf8").readlines()
    >>> len(log_content)
    1
    >>> "We are all gonna die" in log_content[0]
    True

    Remove test log file

    >>> log_filepath.unlink()

    """

    log_filepath = (
        user_log_path(
            appname=ConfigurationUtility.app_name,
            appauthor=ConfigurationUtility.app_author,
        )
        / filename
    )

    # Create log directory, if it does not exist already
    if not log_filepath.parent.exists():
        log_filepath.parent.mkdir(
            exist_ok=True,
            parents=True,
        )

    handler = FileHandler(log_filepath, "w", "utf-8", delay=True)
    handler.setFormatter(Formatter("{asctime} {message}", style="{"))

    return handler


if __name__ == "__main__":
    from doctest import testmod

    testmod()
