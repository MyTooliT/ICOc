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


        Returns
        -------

        A string that describes the various attributes of the identifier

        Examples
        --------

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

        request = (command_field >> 1) & 1
        error = not (command_field & 1)

        attributes = filter(None, [
            f"{self.sender_description()} -> " +
            f"{MyToolItNetworkName[receiver]}",
            f"Block: {self.block_description()}",
            f"Command: {self.command_description()}",
            "Request" if request else "Acknowledge", "Error" if error else None
        ])

        return '[' + ', '.join(attributes) + ']'

    def block(self):
        """Get the block number

        Returns
        -------

        The block (aka group) number for the current identifier

        Example
        -------

                         V  block   number A E R send. R rec.
        >>> Identifier(0b0_000011_00000000_0_0_0_00111_0_00010).block()
        3
        """

        return (self.value >> 22) & 0b111111

    def block_description(self):
        """Get a textual description of the command block

        Returns
        -------

        A short textual description of the command block of the identifier

        Examples
        --------

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

    def command(self):
        """Get the command number

        Returns
        -------

        The command number (part of the command field) of the identifier

        Example
        -------

                         V  block   number A E R send. R rec.
        >>> Identifier(0b0_000011_00001000_0_0_0_00111_0_00010).command()
        8
        """

        return (self.value >> 14) & 0xff

    def command_description(self):
        """Return a textual description of the command

        Returns
        -------

        A short textual description of the command (in the current command
        group)

        Example
        -------

                         V  block   number A E R send. R rec.
        >>> Identifier(0b0_000000_00000000_0_0_0_00101_0_00010
        ...           ).command_description()
        'Verboten'
        """

        try:
            return blocknumber_to_commands[self.block()].inverse[
                self.command()]
        except KeyError:
            return "Unknown"

    def sender(self):
        """Get the sender of the message

        Returns
        -------

        A number that specifies the sender of the message

        Example
        -------

                         V  block   number A E R send. R rec.
        >>> Identifier(0b0_000000_00000000_0_0_0_00111_0_00010).sender()
        7
        """

        return self.value >> 6 & 0x1F

    def sender_description(self):
        """Get a textual description of the sender of a message

        Returns
        -------

        A text that describes the sender

        Example
        -------

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
