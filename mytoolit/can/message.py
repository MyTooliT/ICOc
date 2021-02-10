# -- Imports ------------------------------------------------------------------

from __future__ import annotations

from typing import List, Optional, Union

from can.interfaces.pcan.basic import PCAN_MESSAGE_EXTENDED, TPCANMsg
from can import Message as CANMessage

# Fix imports for script usage
if __name__ == '__main__':
    from pathlib import Path
    from sys import path
    path.append(str(Path(__file__).parent.parent.parent))

from mytoolit.can.command import Command
from mytoolit.can.identifier import Identifier
from mytoolit.can.node import Node

# -- Class --------------------------------------------------------------------


class Message:
    """Wrapper class for CAN messages"""

    def __init__(
        self,
        *message: Union[TPCANMsg, CANMessage],
        identifier: Optional[Identifier] = None,
        data: Optional[List[int]] = None,
        **keyword_arguments: Union[Command, Node, None, str, int,
                                   bool]) -> None:
        """Create a new message based on the given attributes

        Usually you will either specify the (PCAN or python-can) message
        directly, or provide identifier and data. If, you decide to specify
        both the message and one of the keyword arguments, then the keyword
        arguments will be used to overwrite specific parts of the message
        argument.

        Additional keyword parameters will be used as arguments for the
        identifier. This way you can specify all the arguments for a message
        without creating the identifier class yourself. If you decide to
        specify both an identifier and keyword arguments for the identifier,
        then the keyword arguments will overwrite the specific parts of the
        provided identifier.

        Parameters
        ----------

        message:
            Either
                 - A PCAN message structure as used by the PCAN Basic API
                 - or a python-can message

        identifier:
            A 29 bit CAN identifier

        data:
            An iterable over 8 bit values that stores the payload of the
            message

        Examples
        --------

        Create a message from a given PCAN message

        >>> message = Message(TPCANMsg())

        Create a message from a python-can message

        >>> from can import Message as CANMessage
        >>> message = Message(
        ...     CANMessage(
        ...         is_extended_id=True,
        ...         arbitration_id=0b0_000000_00000001_00_0_01111_0_00001))
        >>> from re import search
        >>> search('# (.*)', repr(message))[1]
        '[SPU 1 → STH 1, Block: System, Command: Reset, Acknowledge]'

        Create a message using identifier and data

        >>> identifier = Identifier(block=0, block_command=1)
        >>> payload = [0xab, 0xcd]
        >>> message = Message(identifier=identifier, data=payload)

        Create a message using keyword arguments handled by the identifier
        class

        >>> message = Message(block='System', block_command='Reset')

        If you provide both identifier and identifier keyword arguments, then
        the specific keyword arguments overwrite the values of the identifier

        >>> identifier = Identifier(block='System')
        >>> message = Message(identifier=identifier, block='Streaming')
        >>> Identifier(message.id()).block_name()
        'Streaming'

        """

        if message:
            message = message[0]
            if isinstance(message, TPCANMsg):
                self.pcan_message = message
            elif isinstance(message, CANMessage):
                self.pcan_message = TPCANMsg()
                self.pcan_message.ID = message.arbitration_id
                for byte, value in enumerate(message.data):
                    self[byte] = value
                self.pcan_message.LEN = len(message.data)
            else:
                raise ValueError(
                    "Unsupported object type for argument message: "
                    f"“{type(message)}”")
        else:
            self.pcan_message = TPCANMsg()

        self.pcan_message.MSGTYPE = PCAN_MESSAGE_EXTENDED

        if identifier:
            self.pcan_message.ID = identifier if isinstance(
                identifier, int) else identifier.value

        if keyword_arguments:
            # Mypy assumes that all keyword arguments have the same type
            self.pcan_message.ID = Identifier(
                self.id(), **keyword_arguments).value  # type: ignore

        if data:
            for byte, value in enumerate(data):
                self[byte] = value
            self.pcan_message.LEN = len(data)

    def __len__(self) -> int:
        """Retrieve the length of the message data

        Returns
        -------

        The number of bytes stored in the message data

        Examples
        -------

        >>> len(Message())
        0
        >>> len(Message(data=[5, 6, 7]))
        3
        >>> len(Message(data=[1, 2]))
        2

        """

        return self.pcan_message.LEN

    def __getitem__(self, index: int) -> int:
        """Access a byte of the message using an integer index

        Parameters
        ----------

        index:
            The number of the byte in the message that should be returned

        Returns
        -------

        The byte of the message data at the specified index

        Example
        -------

        >>> message = Message(data=[1,2,3])
        >>> message[0]
        1

        """

        return self.pcan_message.DATA[index]

    def __setitem__(self, index: int, value: int) -> None:
        """Write a byte of the message using an integer index and an value

        Parameters
        ----------

        index:
            The number of the byte in the message that should be set to the
            given value

        value:
            The byte value that should be stored at the specified index

        Examples
        --------

        >>> message = Message()
        >>> message[1] = 1
        >>> message[2] = 2
        >>> message[7] = 7

        >>> message[1]
        1
        >>> message[3]
        0
        >>> message[7]
        7

        """

        self.pcan_message.DATA[index] = value

    def __repr__(self) -> str:
        """Get a textual representation of the current message

        Returns
        -------

        A text that shows the various attributes of the current message

        Examples
        --------

        >>> pcan_message = TPCANMsg()
        >>> pcan_message.ID = Identifier(block=0, block_command=1,
        ...                             request=True, error=False,
        ...                             sender=1, receiver=14).value
        >>> pcan_message.DATA[0] = 0xfe
        >>> pcan_message.DATA[1] = 0xfe
        >>> pcan_message.LEN = 2
        >>> Message(pcan_message) # doctest:+NORMALIZE_WHITESPACE
        0b00000000000000110000001001110 2 0xfe 0xfe
        # [STH 1 → STH 14, Block: System, Command: Reset, Request]

        >>> from re import search
        >>> representation = repr(
        ...     Message(block='Streaming',
        ...             block_command='Acceleration',
        ...             sender='SPU 1',
        ...             receiver='STH 1',
        ...             request=True))
        >>> search('# (.*)', representation)[1]
        '[SPU 1 → STH 1, Block: Streaming, Command: Acceleration, Request]'

        >>> representation = repr(
        ...     Message(block='System',
        ...             block_command='Bluetooth',
        ...             sender='SPU 1',
        ...             receiver='STU 1',
        ...             request=True,
        ...             data=[1] + [0]*7))
        >>> search('# (.*)', representation)[1] # doctest:+NORMALIZE_WHITESPACE
        '[SPU 1 → STU 1, Block: System, Command: Bluetooth, Request]
         (Activate)'

        """

        identifier = Identifier(self.id())

        data_explanation = None
        if (len(self) >= 1 and identifier.block_name() == 'System'
                and identifier.block_command_name() == 'Bluetooth'):
            subcommand = self[0]
            if subcommand == 1:
                data_explanation = "Activate"
            elif subcommand == 2:
                is_acknowledgment = self.identifier().is_acknowledgment()
                data_explanation = "{} number of available devices".format(
                    "Return" if is_acknowledgment else "Get")
                if is_acknowledgment and len(self) >= 2:
                    number_devices = int(chr(self[2]))
                    data_explanation += f": {number_devices}"

        explanation = (f"{identifier} ({data_explanation})"
                       if data_explanation else repr(identifier))

        data_representation = " ".join(
            [hex(self[byte]) for byte in range(len(self))])
        bit_values = [
            f"0b{identifier.value:029b}",
            str(len(self)), data_representation
        ]
        # Filter empty string, since otherwise there might be an additional
        # space at the end of the representation for empty data
        bit_representation = " ".join(filter(None, bit_values))

        return f"{bit_representation} # {explanation}"

    def acknowledge(self, error: bool = False) -> Message:
        """Returns an acknowledgment message object for this message

        In the acknowledgment message receiver and sender will be swapped and
        the request (acknowledge) bit will be set to 0 (acknowledge). The data
        of the acknowledgment message will be the same as in the original
        message.

        Returns
        -------

        An acknowledgment message for the current message

        Example
        -------

        >>> identifier = Identifier(block=0, block_command=1, sender=5,
        ...                         receiver=10)
        >>> message = Message(identifier=identifier, data=[0xaa])
        >>> message.acknowledge() # doctest:+NORMALIZE_WHITESPACE
        0b00000000000000100001010000101 1 0xaa
        # [STH 10 → STH 5, Block: System, Command: Reset, Acknowledge]

        """

        return Message(identifier=self.identifier().acknowledge(),
                       data=self[:len(self)])

    def id(self) -> int:
        """Retrieve the ID of the message

        Returns
        -------

        The 29 bit CAN identifier of the message


        Example
        -------

        >>> Message(block='Configuration').id(
        ...        ) == 0b0_1010_000000000000000000000000
        True

        """

        return self.pcan_message.ID

    def identifier(self) -> Identifier:
        """Retrieve an identifier object for the ID of the message

        Returns
        -------

        An identifier object representing the ID of the message

        Example
        -------

        >>> Message(block='System', block_command='Reset', request=True,
        ...         sender='SPU 1', receiver='STH 2').identifier()
        [SPU 1 → STH 2, Block: System, Command: Reset, Request]

        """

        return Identifier(self.pcan_message.ID)

    def to_python_can(self) -> CANMessage:
        """Retrieve a python-can message object for this message

        Returns
        -------

        A message object of the python-can API

        Example
        -------

        >>> message = Message(block='EEPROM', sender='SPU 1', data=[1,2,3])
        >>> can_message = message.to_python_can()
        >>> can_message # doctest:+NORMALIZE_WHITESPACE
        can.Message(timestamp=0.0, arbitration_id=0xf4003c0,
                    extended_id=True, dlc=3, data=[0x1, 0x2, 0x3])

        >>> message.id() == can_message.arbitration_id
        True

        """

        return CANMessage(is_extended_id=True,
                          arbitration_id=self.id(),
                          data=[self[byte] for byte in range(len(self))])

    def to_pcan(self) -> TPCANMsg:
        """Retrieve a PCAN message object for this message

        Returns
        -------

        A message object of the PCAN Basic API

        Example
        -------

        >>> message = Message(block='System', block_command='Bluetooth')
        >>> pcan_message = message.to_pcan()
        >>> message.id() == pcan_message.ID
        True

        """

        return self.pcan_message


# -- Main ---------------------------------------------------------------------

if __name__ == '__main__':
    from doctest import testmod
    testmod()
