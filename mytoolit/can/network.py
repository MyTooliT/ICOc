# -- Imports ------------------------------------------------------------------

from can.interface import Bus
from pathlib import Path
from sys import path, platform

# Add path for custom libraries
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

        """

        configuration = (settings.CAN.Linux
                         if platform == 'linux' else settings.CAN.Windows)
        bus_config = {
            key.lower(): value
            for key, value in configuration.items()
        }
        bus = Bus(**bus_config)

        # For now we just shut down the bus connection after the bus
        # initialization
        bus.shutdown()


# -- Main ---------------------------------------------------------------------

if __name__ == '__main__':
    from doctest import testmod

    testmod()
