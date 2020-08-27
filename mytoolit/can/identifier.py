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

    def __init__(
            self,
            *identifier,
            command=None,
            sender=None,
            receiver=None,
    ):
        """Create a new identifier from a given integer

        Usually you will either specify the identifier number directly, or
        provide command, sender and receiver. If, you decide to specify both
        the identifier value and one of the keyword arguments, then the
        keyword arguments will be used to overwrite specific parts of the
        identifier. For more information, please take a look at the examples.

        Parameters
        ----------

        identifier:
            A extended CAN identifier (29 bit number)

        command:
            The whole command including group, number, error bit, and
            acknowledgement bit

        sender:
            The sender of the message

        receiver:
            The receiver of the message

        Examples
        -------

        >>> Identifier().value
        0

                                      V  block   number A E R send. R rec.
        >>> identifier = Identifier(0b0_000000_00000000_0_0_0_10000_0_00110,
        ...                         command=1337)
        >>> identifier.command()
        1337
        >>> identifier.receiver()
        6
        >>> identifier.sender()
        16

        >>> identifier = Identifier(command=512, sender=1, receiver=2)
        >>> identifier.sender()
        1
        >>> identifier.receiver()
        2
        >>> identifier.command()
        512
        """

        def set_part(start, width, number):
            """Store bit pattern number at bit start of the identifier"""

            identifier_ones = 0b11111_11111111_11111111_11111111
            mask = 2**width - 1

            # Set all bits for targeted part to 0
            self.value &= (mask << start) ^ identifier_ones
            # Make sure we use the correct number of bits for number
            number = number & mask
            # Set command bits to given value
            self.value |= number << start

        self.value = identifier[0] if identifier else 0

        if command:
            set_part(start=12, width=16, number=command)
        if sender:
            set_part(start=6, width=5, number=sender)
        if receiver:
            set_part(start=0, width=5, number=receiver)

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

        command_field = self.command()
        request = (command_field >> 1) & 1
        error = not (command_field & 1)

        attributes = filter(None, [
            f"{self.sender_name()} -> " + f"{self.receiver_name()}",
            f"Block: {self.block_name()}", f"Command: {self.number_name()}",
            "Request" if request else "Acknowledge", "Error" if error else None
        ])

        return '[' + ', '.join(attributes) + ']'

    def command(self):
        """Get the command part of the identifier

        Returns
        -------

        The whole command including

        - group,
        - number,
        - acknowledge bit, and
        - error bit

        for the current identifier

        Example
        -------

                             V  block   number A E R send. R rec.
        >>> bin(Identifier(0b0_000011_00000000_0_1_0_00111_0_00010).command())
        '0b110000000001'
        """

        return (self.value >> 12) & 0xffff

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

    def block_name(self):
        """Get the name of the command block

        Returns
        -------

        A short textual description of the command block of the identifier

        Examples
        --------

                         V  block   number A E R send. R rec.
        >>> Identifier(0b0_000011_00000000_0_0_0_00111_0_00010
        ...           ).block_name()
        'Unknown'

                         V  block   number A E R send. R rec.
        >>> Identifier(0b0_000100_00000000_0_0_0_00111_0_00010
        ...           ).block_name()
        'Streaming'
        """

        return MyToolItBlock.inverse.get(self.block(), "Unknown")

    def number(self):
        """Get the (command) number

        Returns
        -------

        The command number (part of the command field) of the identifier

        Example
        -------

                         V  block   number A E R send. R rec.
        >>> Identifier(0b0_000011_00001000_0_0_0_00111_0_00010).number()
        8
        """

        return (self.value >> 14) & 0xff

    def number_name(self):
        """Get the name of the (command) number

        Returns
        -------

        A short textual description of the command (in the current command
        group)

        Example
        -------

                         V  block   number A E R send. R rec.
        >>> Identifier(0b0_000000_00000000_0_0_0_00101_0_00010
        ...           ).number_name()
        'Verboten'
        """

        try:
            return blocknumber_to_commands[self.block()].inverse[self.number()]
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

    def sender_name(self):
        """Get the name of the sender of a message

        Returns
        -------

        A text that describes the sender

        Example
        -------

                         V  block   number A E R send. R rec.
        >>> Identifier(0b0_000000_00000000_0_0_0_00101_0_00010
        ...           ).sender_name()
        'STH5'
        """

        return MyToolItNetworkName[self.sender()]

    def receiver(self):
        """Get the receiver of the message

        Returns
        -------

        A number that specifies the receiver of the message

        Example
        -------

                         V  block   number A E R send. R rec.
        >>> Identifier(0b0_000000_00000000_0_0_0_00111_0_00010).receiver()
        2
        """

        return self.value & 0x1f

    def receiver_name(self):
        """Get the name of the receiver of a message

        Returns
        -------

        A text that describes the receiver

        Example
        -------

                         V  block   number A E R send. R rec.
        >>> Identifier(0b0_000000_00000000_0_0_0_00101_0_01110
        ...           ).receiver_name()
        'STH14'
        """

        return MyToolItNetworkName[self.receiver()]


# -- Main ---------------------------------------------------------------------

if __name__ == '__main__':

    from doctest import testmod
    testmod()
