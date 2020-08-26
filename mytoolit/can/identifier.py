# -- Imports ------------------------------------------------------------------

from os.path import abspath, dirname
from sys import path as module_path

# Add path for custom libraries
repository_root = dirname(dirname(dirname(abspath(__file__))))
module_path.append(repository_root)

from MyToolItCommands import blocknumber_to_commands, MyToolItBlock
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
        [STH1 -> STH2, Block: System, Command: Verboten, Acknowledge, Error]

                         V  block   number A E R send. R rec.
        >>> Identifier(0b0_000100_00000001_1_1_0_00010_0_00011)
        [STH2 -> STH3, Block: Streaming, Command: Temperature, Request]

                         V  block   number A E R send. R rec.
        >>> Identifier(0b0_010101_10000001_1_1_0_00010_0_00011)
        [STH2 -> STH3, Block: Unknown, Command: Unknown, Request]
        """

        receiver = self.value & 0x1F
        command_field = (self.value >> 12) & 0xFFFF

        number = command_field >> 2
        block = self.block()
        command = number & 0xFF

        request = (command_field >> 1) & 1
        error = not (command_field & 1)

        try:
            command_description = blocknumber_to_commands[block].inverse[
                command]
        except KeyError:
            command_description = "Unknown"

        attributes = filter(None, [
            f"{self.sender_description()} -> " +
            f"{MyToolItNetworkName[receiver]}",
            f"Block: {self.block_description()}",
            f"Command: {command_description}",
            "Request" if request else "Acknowledge", "Error" if error else None
        ])

        return '[' + ', '.join(attributes) + ']'

    def block(self):
        """Return the block number

        Example:

                         V  block   number A E R send. R rec.
        >>> Identifier(0b0_000011_00000000_0_0_0_00111_0_00010).block()
        3
        """

        return (self.value >> 22) & 0b111111

    def block_description(self):
        """Return a textual description for the block

        Example:

                         V  block   number A E R send. R rec.
        >>> Identifier(0b0_000011_00000000_0_0_0_00111_0_00010
        ...           ).block_description()
        'Unknown'

                         V  block   number A E R send. R rec.
        >>> Identifier(0b0_000100_00000000_0_0_0_00111_0_00010
        ...           ).block_description()
        'Streaming'
        """

        return MyToolItBlock.inverse.get(self.block(), "Unknown")

    def sender(self):
        """Return the sender of the message

        Example:

                         V  block   number A E R send. R rec.
        >>> Identifier(0b0_000000_00000000_0_0_0_00111_0_00010).sender()
        7
        """

        return self.value >> 6 & 0x1F

    def sender_description(self):
        """Return a textual description of the sender of a message

        Example:

                         V  block   number A E R send. R rec.
        >>> Identifier(0b0_000000_00000000_0_0_0_00101_0_00010
        ...           ).sender_description()
        'STH5'
        """

        return MyToolItNetworkName[self.sender()]


# -- Main ---------------------------------------------------------------------

if __name__ == '__main__':

    from doctest import testmod
    testmod()
