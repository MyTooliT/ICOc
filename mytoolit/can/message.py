# -- Imports ------------------------------------------------------------------

from __future__ import annotations

from typing import List, Optional, Union

from can.interfaces.pcan.basic import PCAN_MESSAGE_EXTENDED, TPCANMsg
from can import Message as CANMessage
from netaddr import EUI

# Fix imports for script usage
if __name__ == '__main__':
    from pathlib import Path
    from sys import path
    path.append(str(Path(__file__).parent.parent.parent))

from mytoolit.can.command import Command
from mytoolit.can.identifier import Identifier
from mytoolit.can.node import Node
from mytoolit.utility import bytearray_to_text

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
                self.message = CANMessage(
                    is_extended_id=True,
                    arbitration_id=message.ID,
                    data=[message.DATA[byte] for byte in range(message.LEN)])
            elif isinstance(message, CANMessage):
                self.message = message
            else:
                raise ValueError(
                    "Unsupported object type for argument message: "
                    f"“{type(message)}”")
        else:
            self.message = CANMessage(is_extended_id=True)

        if identifier:
            self.message.arbitration_id = identifier if isinstance(
                identifier, int) else identifier.value

        if keyword_arguments:
            # Mypy assumes that all keyword arguments have the same type
            self.message.arbitration_id = Identifier(
                self.id(), **keyword_arguments).value  # type: ignore

        if data:
            self.message.data = bytearray(data)
            self.message.dlc = len(data)

    @property
    def data(self) -> bytearray:
        """Retrieve the message data

        Returns
        -------

        A bytearray containing the data of the message

        Examples
        --------

        >>> len(Message().data)
        0
        >>> len(Message(data=[5, 6, 7]).data)
        3
        >>> len(Message(data=[1, 2]).data)
        2

        """

        return self.message.data

    @data.setter
    def data(self, data: Union[List[int], bytearray]) -> None:
        """Set the message data to a new value

        Parameters
        ----------

        data:
            The data that should be stored in the message

        Examples
        --------

        >>> message = Message(data=[1])
        >>> message.data[0] = 42
        >>> message.data[0]
        42

        >>> message = Message(data = bytearray([0] * 8))
        >>> message.data[1] = 1
        >>> message.data[2] = 2
        >>> message.data[7] = 7

        >>> message.data[1]
        1
        >>> message.data[3]
        0
        >>> message.data[7]
        7

        """

        self.message.data = bytearray(data)
        self.message.dlc = len(self.data)

    def _data_explanation(self) -> str:
        """Retrieve a textual representation of the message data

        Returns
        -------

        A textual description of the data contained in the message

        """

        if len(self.data) <= 0:
            return ""

        identifier = self.identifier()
        data_explanation = ""
        if (identifier.block_name() == 'System'
                and identifier.block_command_name() == 'Bluetooth'):

            subcommand = self.data[0]
            device_number = self.data[1]
            is_acknowledgment = self.identifier().is_acknowledgment()
            verb = "Return" if is_acknowledgment else "Get"

            if subcommand == 1:
                verb = "Acknowledge" if is_acknowledgment else "Request"
                data_explanation = f"{verb} Bluetooth activation"
            elif subcommand == 2:
                data_explanation = f"{verb} number of available devices"
                if is_acknowledgment:
                    number_devices = int(chr(self.data[2]))
                    data_explanation += f": {number_devices}"

            elif subcommand == 5 or subcommand == 6:
                part = "first" if subcommand == 5 else "second"
                data_explanation = (f"{verb} {part} part of name of device "
                                    f"with device number “{device_number}”")
                if is_acknowledgment and len(self.data) >= 2:
                    name = bytearray_to_text(self.data[2:])
                    data_explanation += f": “{name}”"
            elif subcommand == 7:
                info = ("Acknowledge connection request to"
                        if is_acknowledgment else "Request connection for")
                data_explanation = (f"{info} device "
                                    f"with device number “{device_number}”")
            elif subcommand == 8:
                data_explanation = f"{verb} Bluetooth connection status"
                if is_acknowledgment and len(self.data) >= 3:
                    connected = bool(self.data[2])
                    data_explanation += ": {}".format(
                        "Connected" if connected else "Not connected")
            elif subcommand == 9:
                verb = "Acknowledge" if is_acknowledgment else "Request"
                data_explanation = f"{verb} Bluetooth deactivation"
            elif subcommand == 12:
                data_explanation = (f"{verb} RSSI of device "
                                    f"with device number “{device_number}”")
                if is_acknowledgment and len(self.data) >= 3:
                    rssi = int.from_bytes(self.data[2:3],
                                          byteorder='little',
                                          signed=True)
                    data_explanation += f": {rssi}"
            elif subcommand == 17:
                data_explanation = (f"{verb} MAC address of device "
                                    f"with device number “{device_number}”")
                if is_acknowledgment and len(self.data) >= 8:
                    mac_address = EUI("-".join(
                        (f"{byte:0x}" for byte in self.data[7:1:-1])))
                    data_explanation += f": {mac_address}"

        if identifier.block_name() == 'EEPROM':
            page = self.data[0]
            offset = self.data[1]
            length = self.data[2]
            data = list(self.data[4:4 + min(length, 4)])
            is_acknowledgment = self.identifier().is_acknowledgment()

            info = ("Acknowledge request" if is_acknowledgment else "Request")
            verb = identifier.block_command_name().lower()
            data_explanation = (
                f"{info} to {verb} {length} bytes at page {page} "
                f"with offset {offset}")
            read_request = verb == "read" and not is_acknowledgment
            if not read_request:
                data_explanation += f": {data}"

        return data_explanation

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
         (Request Bluetooth activation)'

        """

        identifier = self.identifier()
        data_explanation = self._data_explanation()

        explanation = (f"{identifier} ({data_explanation})"
                       if data_explanation else repr(identifier))

        data_representation = " ".join(
            [hex(self.data[byte]) for byte in range(len(self.data))])
        bit_values = [
            f"0b{identifier.value:029b}",
            str(len(self.data)), data_representation
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

        Parameters
        ----------

        error:
            Specifies if the acknowledgment message is an error acknowledgment
            or not

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
                       data=list(self.data))

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

        return self.message.arbitration_id

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

        return Identifier(self.id())

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

        return self.message

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

        message = TPCANMsg()
        message.ID = self.message.arbitration_id
        for byte, value in enumerate(self.message.data):
            message.DATA[byte] = value
        message.LEN = len(self.data)
        message.MSGTYPE = PCAN_MESSAGE_EXTENDED

        return message


# -- Main ---------------------------------------------------------------------

if __name__ == '__main__':
    from doctest import testmod
    testmod()
