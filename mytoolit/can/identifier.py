# -- Imports ------------------------------------------------------------------

from os.path import abspath, dirname
from sys import path as module_path

# Add path for custom libraries
repository_root = dirname(dirname(dirname(abspath(__file__))))
module_path.append(repository_root)

from MyToolItCommands import MyToolItBlock
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


        Examples:

                         V  block   number A E R send. R rec.
        >>> Identifier(0b0_000000_00000000_0_0_0_00001_0_00010)
        [STH1 -> STH2, Block: System, Command: 0, Acknowledge, Error]

                         V  block   number A E R send. R rec.
        >>> Identifier(0b0_000100_00000010_1_1_0_00010_0_00011)
        [STH2 -> STH3, Block: Streaming, Command: 2, Request]
        """

        receiver = self.value & 0x1F
        command = (self.value >> 12) & 0xFFFF
        number = command >> 2
        group = number >> 8
        cmd = number & 0xFF
        request = (command >> 1) & 1
        error = not (command & 1)

        attributes = filter(None, [
            f"{MyToolItNetworkName[self.sender()]} -> " +
            f"{MyToolItNetworkName[receiver]}",
            f"Block: {MyToolItBlock.inverse[group]}", f"Command: {cmd}",
            "Request" if request else "Acknowledge", "Error" if error else None
        ])

        return '[' + ', '.join(attributes) + ']'

    def sender(self):
        """Return the sender of the message"""

        return self.value >> 6 & 0x1F


# -- Main ---------------------------------------------------------------------

if __name__ == '__main__':

    from doctest import testmod
    testmod()
