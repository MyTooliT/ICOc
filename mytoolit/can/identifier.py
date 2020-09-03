# -- Imports ------------------------------------------------------------------

from os.path import abspath, dirname
from sys import path as module_path

# Add path for custom libraries
repository_root = dirname(dirname(dirname(abspath(__file__))))
module_path.append(repository_root)

from mytoolit.can.command import Command

from MyToolItCommands import blocknumber_to_commands, MyToolItBlock
from MyToolItNetworkNumbers import MyToolItNetworkName

# -- Class --------------------------------------------------------------------


class Identifier:
    """This class represents a CAN identifier of the MyTooliT protocol"""

    def __init__(
            self,
            *identifier,
            command=None,
            block=None,
            block_command=None,
            error=None,
            request=None,
            sender=None,
            receiver=None,
    ):
        """Create a new identifier from a given integer

        Usually you will either specify the identifier number directly, or
        provide command, sender and receiver. If, you decide to specify both
        the identifier value and one of the keyword arguments, then the
        keyword arguments will be used to overwrite specific parts of the
        identifier.

        Smaller parts (smaller bit width) will overwrite larger parts. For
        example, if you decide to both specify the command and the block
        (which is part of the command), then the block bits will be used to
        overwrite the block bits in the specified command.

        For more information, please take a look at the examples.

        Parameters
        ----------

        identifier:
            A extended CAN identifier (29 bit number)

        command:
            The whole command including group, number, error bit, and
            acknowledgement bit

        block:
            The block of the command (part of the command)

        block_command:
            The block command (part of the command)

        request:
            A boolean value that specifies if the identifier represents an
            request (or an acknowledgement)

        error:
            A boolean value that specifies if the identifier represents an
            error or not (part of the command)

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

        >>> identifier = Identifier(block=4, block_command=1, request=False,
        ...                         error=False, sender=31, receiver=1)
        >>> identifier.block_name()
        'Streaming'
        >>> identifier.block_command_name()
        'Temperature'
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
            # A Command can be both a number or a `Command` object
            command_as_number = command if isinstance(command,
                                                      int) else command.value
            set_part(start=12, width=16, number=command_as_number)
        if list(filter(None, [block, block_command, request, error])):
            set_part(start=12,
                     width=16,
                     number=Command((self.value >> 12) & 0xffff,
                                    block=block,
                                    block_command=block_command,
                                    request=request,
                                    error=error).value)
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
        [STH1 → STH2, Block: System, Command: Verboten, Acknowledge]

                         V  block   number A E R send. R rec.
        >>> Identifier(0b0_000100_00000001_1_1_0_00010_0_00011)
        [STH2 → STH3, Block: Streaming, Command: Temperature, Request, Error]

                         V  block   number A E R send. R rec.
        >>> Identifier(0b0_010101_10000001_1_1_0_00010_0_00011)
        [STH2 → STH3, Block: Unknown, Command: Unknown, Request, Error]
        """

        return (f"[{self.sender_name()} → {self.receiver_name()}, " +
                f"{Command(self.command())}]")

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

    def command_number(self):
        """Get the block and block command part of the identifier

        Returns
        -------

        The command without the error and acknowledge bits

        Example
        -------

                             V  block   number A E R send. R rec.
        >>> bin(Identifier(0b0_100011_11000001_0_1_0_00111_0_00010
        ...    ).command_number())
        '0b10001111000001'
        """

        return Command(self.command()).value >> 2

    def block(self):
        """Get the block

        Returns
        -------

        The block (aka group) number for the current identifier

        Example
        -------

                         V  block   number A E R send. R rec.
        >>> Identifier(0b0_000011_00000000_0_0_0_00111_0_00010).block()
        3
        """

        return Command(self.command()).block()

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

        return Command(self.command()).block_name()

    def block_command(self):
        """Get the block command

        Returns
        -------

        The block number (part of the command number) of the identifier

        Example
        -------

                         V  block   number A E R send. R rec.
        >>> Identifier(0b0_000011_00001000_0_0_0_00111_0_00010).block_command()
        8
        """

        return Command(self.command()).block_command()

    def block_command_name(self):
        """Get the name of the block command

        Returns
        -------

        A short textual description of the command (in the current block)

        Example
        -------

                         V  block   number A E R send. R rec.
        >>> Identifier(0b0_000000_00000000_0_0_0_00101_0_00010
        ...           ).block_command_name()
        'Verboten'
        """

        return Command(self.command()).block_command_name()

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
