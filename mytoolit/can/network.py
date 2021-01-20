# -- Imports ------------------------------------------------------------------

from can.interface import Bus
from pathlib import Path
from sys import path, platform

# Fix imports for script usage
if __name__ == '__main__':
    from pathlib import Path
    from sys import path
    path.append(str(Path(__file__).parent.parent.parent))

from mytoolit.config import settings

# -- Class --------------------------------------------------------------------


class Network:
    """Basic class to communicate with STU and STH devices"""

    def __init__(self):
        """Create a new network from the given arguments

        Examples
        --------

        >>> network = Network()
        >>> network.shutdown()

        """

        configuration = (settings.can.linux
                         if platform == 'linux' else settings.can.windows)
        bus_config = {
            key.lower(): value
            for key, value in configuration.items()
        }
        self.bus = Bus(**bus_config)

    def shutdown(self):
        """Deallocate all resources for this network connection"""

        self.bus.shutdown()


# -- Main ---------------------------------------------------------------------

if __name__ == '__main__':
    from doctest import testmod

    testmod()
