"""Support for the (29 bit) CAN identifiers of the MyTooliT protocol

See: https://mytoolit.github.io/Documentation/#identifier

for more information
"""

# -- Imports ------------------------------------------------------------------

from __future__ import annotations

from typing import Optional, Union

from mytoolit.can.command import Command
from mytoolit.can.node import Node

# -- Class --------------------------------------------------------------------


class Identifier:
    """This class represents a CAN identifier of the MyTooliT protocol"""

    def __init__(  # pylint: disable=too-many-arguments
        self,
        *identifier: int,
        command: Union[Command, None, int] = None,
        block: Union[None, str, int] = None,
        block_command: Union[None, str, int] = None,
        error: Optional[bool] = None,
        request: Optional[bool] = None,
        sender: Union[Node, None, str, int] = None,
        receiver: Union[Node, None, str, int] = None,
    ) -> None:
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
            An extended CAN identifier (29 bit number)

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
        --------

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

        >>> identifier = Identifier(command=512, sender='STH 1', receiver=2)
        >>> identifier.sender()
        1
        >>> identifier.receiver()
        2
        >>> identifier.command()
        512

                                      V  block   number A E R send. R rec.
        >>> identifier = Identifier(0b0_000000_00000000_1_0_0_10000_0_00110)
        >>> Identifier(identifier.value, request=False).is_acknowledgment()
        True

        >>> Identifier(receiver='SPU 1').receiver()
        15

        >>> identifier = Identifier(block=4, block_command=1, request=False,
        ...                         error=False, sender=31, receiver=1)
        >>> identifier.block_name()
        'Streaming'
        >>> identifier.block_command_name()
        'Temperature'

        >>> identifier = Identifier(block='EEPROM',
        ...                         block_command='Read')
        >>> identifier.block_name()
        'EEPROM'
        >>> identifier.block_command_name()
        'Read'
        """

        def set_part(start, width, number):
            """Store bit pattern number at bit start of the identifier"""

            identifier_ones = 0b11111_11111111_11111111_11111111
            mask = (1 << width) - 1

            # Set all bits for targeted part to 0
            self.value &= (mask << start) ^ identifier_ones
            # Make sure we use the correct number of bits for number
            number = number & mask
            # Set command bits to given value
            self.value |= number << start

        self.value = identifier[0] if identifier else 0

        if command is not None:
            # A command can be a number or a `Command` object
            command_as_number = (
                command if isinstance(command, int) else command.value
            )
            set_part(start=12, width=16, number=command_as_number)

        set_part(
            start=12,
            width=16,
            number=Command(
                (self.value >> 12) & 0xFFFF,
                block=block,
                block_command=block_command,
                request=request,
                error=error,
            ).value,
        )

        # Sender and receiver can be either an integer or a string like object
        if sender is not None:
            set_part(start=6, width=5, number=Node(sender).value)
        if receiver is not None:
            set_part(start=0, width=5, number=Node(receiver).value)

    def __eq__(self, other: object) -> bool:
        """Compare this identifier to another object

        Parameters
        ----------

        other:
            The other object this identifier should be compared to

        Returns
        -------

        - True, if the given object is an identifier and it has the same
          value as this identifier

        - False, otherwise

        Examples
        --------

        >>> identifier1 = Identifier(block='System', block_command='Reset')
        >>> identifier2 = Identifier(block='System', block_command='Reset',
        ...                          receiver='STH 1')

        >>> identifier1 == identifier2
        False

        >>> identifier1 == Identifier(identifier2.value, receiver=0)
        True

        """

        if isinstance(other, Identifier):
            return self.value == other.value

        return False

    def __repr__(self) -> str:
        """Return the string representation of the current identifier

        Returns
        -------

        A string that describes the various attributes of the identifier

        Examples
        --------

                         V  block   number A E R send. R rec.
        >>> Identifier(0b0_000000_00000000_0_0_0_00001_0_00010)
        [STH 1 → STH 2, Block: System, Command: Verboten, Acknowledge]

                         V  block   number A E R send. R rec.
        >>> Identifier(0b0_000100_00000001_1_1_0_00010_0_00011)
        [STH 2 → STH 3, Block: Streaming, Command: Temperature, Request, Error]

                         V  block   number A E R send. R rec.
        >>> Identifier(0b0_010101_10000001_1_1_0_00010_0_00011)
        [STH 2 → STH 3, Block: Unknown, Command: Unknown, Request, Error]
        """

        return (
            f"[{self.sender_name()} → {self.receiver_name()}, "
            f"{Command(self.command())}]"
        )

    def acknowledge(self, error: bool = False) -> Identifier:
        """Returns an acknowledgement identifier for this identifier

        In the acknowledgment identifier receiver and sender will be swapped
        and the request (acknowledge) bit will be set to 0 (acknowledge).

        Returns
        -------

        An acknowledgment message for the current message

        Example
        -------

        >>> identifier = Identifier(block='System', block_command='Reset',
        ...                         sender='SPU 1', receiver='STH 1')

        >>> acknowledgement_identifier = identifier.acknowledge()
        >>> acknowledgement_identifier.receiver_name()
        'SPU 1'
        >>> acknowledgement_identifier.is_error()
        False

        >>> error_identifier = identifier.acknowledge(error=True)
        >>> error_identifier.sender_name()
        'STH 1'
        >>> error_identifier.is_error()
        True

        """

        return Identifier(
            self.value,
            sender=self.receiver(),
            receiver=self.sender(),
            request=False,
            error=error,
        )

    def command(self) -> int:
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

        return (self.value >> 12) & 0xFFFF

    def command_number(self) -> int:
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

    def block(self) -> int:
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

    def block_name(self) -> str:
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

    def block_command(self) -> int:
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

    def block_command_name(self) -> str:
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

    def is_acknowledgment(self) -> bool:
        """Checks if the identifier represents an acknowledgment

        Returns
        -------

        True if the identifier is for an acknowledgement, or false otherwise

        Example
        -------

                         V  block   number A E R send. R rec.
        >>> Identifier(0b0_000000_00000000_1_0_0_00101_0_00010
        ...           ).is_acknowledgment()
        False
        """

        return Command(self.command()).is_acknowledgment()

    def is_error(self) -> bool:
        """Checks if the identifier represents an error

        Returns
        -------

        True if the identifier indicates an error message, or false otherwise

        Example
        -------

                         V  block   number A E R send. R rec.
        >>> Identifier(0b0_000000_00000000_1_1_0_00101_0_00010
        ...           ).is_error()
        True

        """

        return Command(self.command()).is_error()

    def set_acknowledgment(self, value: bool = True) -> Identifier:
        """Set the acknowledgment bit to the given value

        Parameters
        ----------

        value:
            A boolean that specifies if this identifier should represent an
            acknowledgment or not

        Examples
        --------

                                      V  block   number A E R send. R rec.
        >>> identifier = Identifier(0b0_000011_00001000_0_0_0_00111_0_00010)
        >>> identifier.is_acknowledgment()
        True
        >>> identifier.set_acknowledgment(False).is_acknowledgment()
        False

        >>> identifier.set_acknowledgment(True).is_acknowledgment()
        True

        Returns
        -------

        The modified identifier object
        """

        command = Command(self.command()).set_acknowledgment(value)
        self.value = Identifier(self.value, command=command).value
        return self

    def set_error(self, error: bool = True) -> Identifier:
        """Set the error bit to the given value

        Parameters
        ----------

        error:
            A boolean that specifies if this identifier should indicate an
            error or not

        Examples
        --------

                                      V  block   number A E R send. R rec.
        >>> identifier = Identifier(0b0_000011_00001000_0_1_0_00111_0_00010)
        >>> identifier.is_error()
        True

        >>> identifier.set_error(False).is_error()
        False

        >>> identifier.set_error().is_error()
        True

        Returns
        -------

        The modified identifier object

        """

        command = Command(self.command()).set_error(error)
        self.value = Identifier(self.value, command=command).value
        return self

    def sender(self) -> int:
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

    def sender_name(self) -> str:
        """Get the name of the sender of a message

        Returns
        -------

        A text that describes the sender

        Example
        -------

                         V  block   number A E R send. R rec.
        >>> Identifier(0b0_000000_00000000_0_0_0_00101_0_00010
        ...           ).sender_name()
        'STH 5'
        """

        return repr(Node(self.sender()))

    def receiver(self) -> int:
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

        return self.value & 0x1F

    def receiver_name(self) -> str:
        """Get the name of the receiver of a message

        Returns
        -------

        A text that describes the receiver

        Example
        -------

                         V  block   number A E R send. R rec.
        >>> Identifier(0b0_000000_00000000_0_0_0_00101_0_01110
        ...           ).receiver_name()
        'STH 14'
        """

        return repr(Node(self.receiver()))


# -- Main ---------------------------------------------------------------------

if __name__ == "__main__":
    from doctest import testmod

    testmod()
