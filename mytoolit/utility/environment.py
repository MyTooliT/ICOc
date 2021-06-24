# -- Imports ------------------------------------------------------------------

from os import environ, pathsep
from sys import platform

from mytoolit.config import settings

# -- Functions ----------------------------------------------------------------


def add_commander_path_to_environment() -> None:
    """Add path to Simplicity Commander (`commander`) to `PATH`

    Example
    -------

    >>> from os import environ
    >>> length_path_before = len(environ['PATH'])
    >>> add_commander_path_to_environment()
    >>> length_path_after = len(environ['PATH'])
    >>> length_path_after > length_path_before
    True

    """

    path = settings.commands.path
    paths = path.linux if platform == 'Linux' else path.windows
    environ['PATH'] += (pathsep + pathsep.join(paths))


# -- Main ---------------------------------------------------------------------

if __name__ == '__main__':
    from doctest import testmod

    testmod()
