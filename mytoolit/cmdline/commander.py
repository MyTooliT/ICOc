# -- Imports ------------------------------------------------------------------

from os import environ, pathsep
from sys import platform

from mytoolit.config import settings

# -- Class --------------------------------------------------------------------


class Commander:
    """Wrapper for the Simplicity Commander commandline tool"""

    def __init__(self):
        """Initialize the Simplicity Commander wrapper"""

        self._add_path_to_environment()

    def _add_path_to_environment(self) -> None:
        """Add path to Simplicity Commander (`commander`) to `PATH`

        After calling this method you should be able to call `commander`
        without its path prefix, if you installed it somewhere in the
        locations specified below `COMMANDS` → `PATH` in the configuration.

        Example
        -------

        >>> Commander()._add_path_to_environment()

        >>> from subprocess import run
        >>> result = run("commander --version".split(), capture_output=True)
        >>> result.returncode == 0
        True

        """

        path = settings.commands.path
        paths = path.linux if platform == 'Linux' else path.windows
        environ['PATH'] += (pathsep + pathsep.join(paths))


# -- Main ---------------------------------------------------------------------

if __name__ == '__main__':
    from doctest import testmod
    testmod()
