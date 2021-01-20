# -- Imports ------------------------------------------------------------------

from can.interfaces.pcan.basic import PCAN_MESSAGE_EXTENDED, TPCANMsg
from can import Message as CANMessage

# Fix imports for script usage
if __name__ == '__main__':
    from pathlib import Path
    from sys import path
    path.append(str(Path(__file__).parent.parent.parent))

from mytoolit.can.identifier import Identifier

# -- Class --------------------------------------------------------------------


class Message:
    """Wrapper class for CAN messages"""

    def __init__(self,
                 *message,
                 identifier=None,
                 data=None,
                 **keyword_arguments):
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
                    self.pcan_message.DATA[byte] = value
                self.pcan_message.LEN = len(message.data)
            else:
                raise ValueError(
                    "Unsupported object type for argument message: "
                    f" “{type(message)}”")
        else:
            self.pcan_message = TPCANMsg()

        self.pcan_message.MSGTYPE = PCAN_MESSAGE_EXTENDED

        if identifier:
            self.pcan_message.ID = identifier if isinstance(
                identifier, int) else identifier.value

        if keyword_arguments:
            self.pcan_message.ID = Identifier(self.id(),
                                              **keyword_arguments).value

        if data:
            for byte, value in enumerate(data):
                self.pcan_message.DATA[byte] = value
            self.pcan_message.LEN = len(data)

    def __repr__(self):
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
        """

        identifier = Identifier(self.id())

        data_representation = " ".join([
            hex(self.pcan_message.DATA[byte])
            for byte in range(self.pcan_message.LEN)
        ])
        bit_values = [
            f"0b{identifier.value:029b}",
            str(self.pcan_message.LEN), data_representation
        ]
        # Filter empty string, since otherwise there might be an additional
        # space at the end of the representation for empty data
        bit_representation = " ".join(filter(None, bit_values))

        return f"{bit_representation} # {identifier}"

    def acknowledge(self, error=False):
        """Returns an acknowledgment message object for this message

        In the acknowledgment message receiver and sender will be swapped and
        the request (acknowledge) bit will be set to 0 (acknowledge). The
        data of the acknowledgment message will be empty.

        Returns
        -------

        An acknowledgment message for the current message

        Example
        -------

        >>> identifier = Identifier(block=0, block_command=1, sender=5,
        ...                         receiver=10)
        >>> message = Message(identifier=identifier, data=[0xaa])
        >>> message.acknowledge() # doctest:+NORMALIZE_WHITESPACE
        0b00000000000000100001010000101 0
        # [STH 10 → STH 5, Block: System, Command: Reset, Acknowledge]
        """

        identifier = Identifier(self.id())
        return Message(identifier=identifier,
                       sender=identifier.receiver(),
                       receiver=identifier.sender(),
                       request=False,
                       error=error,
                       data=[])

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

    def to_python_can(self):
        """Retrieve a python-can message object for this message

        Returns
        -------

        A message object of the python-can API

        Example
        -------

        >>> message = Message(block='EEPROM', sender='SPU 1')
        >>> can_message = message.to_python_can()
        >>> can_message # doctest:+NORMALIZE_WHITESPACE
        can.Message(timestamp=0.0, arbitration_id=0xf4003c0,
                    extended_id=True, dlc=0, data=[])

        >>> message.id() == can_message.arbitration_id
        True

        """

        return CANMessage(
            is_extended_id=True,
            arbitration_id=self.id(),
            data=[value[byte] for byte, value in range(self.pcan_message.LEN)])

    def to_pcan(self):
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
