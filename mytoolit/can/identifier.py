# -- Imports ------------------------------------------------------------------

from os.path import abspath, dirname
from sys import path as module_path

# Add path for custom libraries
repository_root = dirname(dirname(dirname(abspath(__file__))))
module_path.append(repository_root)

from MyToolItNetworkNumbers import MyToolItNetworkName

# -- Class --------------------------------------------------------------------


class Identifier:
    """This class represents a CAN identifier of the MyTooliT protocol"""

    def __init__(self, identifier):
        """Create a new identifier from a given integer

        Parameters
        ----------

        identifier:
            A extended CAN identifier (29 bit number)
        """
        self.value = identifier

    def __repr__(self):
        """Return the string representation of the current identifier"""

        receiver = self.value & 0x1F
        sender = (self.value >> 6) & 0x1F
        command = (self.value >> 12) & 0xFFFF
        command_number = (command >> 2)
        request = (command >> 1) & 1
        error = command & 1

        return '[' + ', '.join([
            f"{MyToolItNetworkName[sender]} -> " +
            f"{MyToolItNetworkName[receiver]}", f"Command: {command_number}",
            "Request" if request else "Acknowledge", f"Error: {error}"
        ]) + ']'
