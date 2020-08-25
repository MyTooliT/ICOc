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
        """Return the string representation of the current identifier


        Example:

                         V  group   number A E R send. R rec.
        >>> Identifier(0b0_000011_00000000_0_0_0_00001_0_00010)
        [STH1 -> STH2, Group: 3, Command: 0, Acknowledge, Error]
        """

        receiver = self.value & 0x1F
        sender = (self.value >> 6) & 0x1F
        command = (self.value >> 12) & 0xFFFF
        number = command >> 2
        group = number >> 8
        cmd = number & 0xFF
        request = (command >> 1) & 1
        error = not (command & 1)

        return '[' + ', '.join([
            f"{MyToolItNetworkName[sender]} -> " +
            f"{MyToolItNetworkName[receiver]}", f"Group: {group}",
            f"Command: {cmd}", "Request" if request else "Acknowledge",
            "Error" if error else ""
        ]) + ']'


# -- Main ---------------------------------------------------------------------

if __name__ == '__main__':

    from doctest import testmod
    testmod()
