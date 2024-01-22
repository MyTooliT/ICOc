"""Support for MyTooliT protocol CAN messages

For more information, please take a look here:
- https://mytoolit.github.io/Documentation/#mytoolit-communication-protocol
"""

# -- Imports ------------------------------------------------------------------

from __future__ import annotations

from typing import List, Optional, Union

from can.interfaces.pcan.basic import PCAN_MESSAGE_EXTENDED, TPCANMsg
from can import Message as CANMessage
from netaddr import EUI

from mytoolit.can.calibration import CalibrationMeasurementFormat
from mytoolit.can.command import Command
from mytoolit.can.identifier import Identifier
from mytoolit.can.node import Node
from mytoolit.can.status import State
from mytoolit.can.streaming import StreamingFormat, StreamingFormatVoltage
from mytoolit.utility import convert_bytes_to_text

# -- Class --------------------------------------------------------------------


class Message:
    """Wrapper class for CAN messages"""

    def __init__(
        self,
        *message: Union[TPCANMsg, CANMessage],
        identifier: Optional[Identifier] = None,
        data: Optional[List[int]] = None,
        **keyword_arguments: Union[Command, Node, None, str, int, bool],
    ) -> None:
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
            can_message = message[0]
            if isinstance(can_message, TPCANMsg):
                self.message = CANMessage(
                    is_extended_id=True,
                    arbitration_id=can_message.ID,
                    data=[
                        can_message.DATA[byte]
                        for byte in range(can_message.LEN)
                    ],
                )
            elif isinstance(can_message, CANMessage):
                self.message = can_message
            else:
                raise ValueError(
                    "Unsupported object type for argument message: "
                    f"“{type(can_message)}”"
                )
        else:
            self.message = CANMessage(is_extended_id=True)

        if identifier:
            self.message.arbitration_id = (
                identifier if isinstance(identifier, int) else identifier.value
            )

        if keyword_arguments:
            # mypy assumes that all keyword arguments have the same type
            self.message.arbitration_id = Identifier(
                self.id(), **keyword_arguments  # type: ignore
            ).value

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

    # pylint: disable=too-many-branches, too-many-locals, too-many-statements

    def _data_explanation_system(self) -> str:
        """Retrieve a textual representation of system messages

        Returns
        -------

        A textual description of the data contained in the message

        """

        def mac_address() -> EUI:
            """Convert the message data into a MAC address"""
            return EUI("-".join((f"{byte:0x}" for byte in self.data[7:1:-1])))

        identifier = self.identifier()
        data_explanation = ""

        if identifier.block_command_name() == "Get/Set State":
            if len(self.data) < 1:
                return ""

            data_explanation = repr(State(self.data[0]))

        if identifier.block_command_name() == "Bluetooth":
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
                    number_devices_text = convert_bytes_to_text(self.data[2:])
                    data_explanation += ": "
                    try:
                        number_devices = int(number_devices_text)
                        data_explanation += f"{number_devices}"
                    except ValueError:
                        data_explanation += (
                            "Unable to convert text "
                            f"“{number_devices_text}” to number"
                        )

            elif subcommand in (5, 6):
                part = "first" if subcommand == 5 else "second"
                data_explanation = (
                    f"{verb} {part} part of name of device "
                    f"with device number “{device_number}”"
                )
                if is_acknowledgment and len(self.data) >= 2:
                    name = convert_bytes_to_text(self.data[2:])
                    data_explanation += f": “{name}”"
            elif subcommand == 7:
                info = (
                    "Acknowledge connection request"
                    if is_acknowledgment
                    else "Request connection"
                )
                data_explanation = (
                    f"{info} to device with device number “{device_number}”"
                )
            elif subcommand == 8:
                data_explanation = f"{verb} Bluetooth connection status"
                if is_acknowledgment and len(self.data) >= 3:
                    connected = bool(self.data[2])
                    data_explanation += (
                        f": {'Connected' if connected else 'Not connected'}"
                    )
            elif subcommand == 9:
                verb = "Acknowledge" if is_acknowledgment else "Request"
                data_explanation = f"{verb} Bluetooth deactivation"
            elif subcommand == 10:
                verb = "Return" if is_acknowledgment else "Get"
                data_explanation = f"{verb} Bluetooth send counter"
                if is_acknowledgment and len(self.data) >= 8:
                    counter = int.from_bytes(self.data[2:], byteorder="big")
                    data_explanation += f": {counter}"
            elif subcommand == 12:
                data_explanation = (
                    f"{verb} RSSI of device "
                    f"with device number “{device_number}”"
                )
                if is_acknowledgment and len(self.data) >= 3:
                    rssi = int.from_bytes(
                        self.data[2:3], byteorder="little", signed=True
                    )
                    data_explanation += f": {rssi}"
            elif subcommand == 14:
                data_explanation = "Write energy mode reduced"
                if len(self.data) >= 8:
                    time_normal_to_reduced_ms = int.from_bytes(
                        self.data[2:6], byteorder="little"
                    )
                    advertisement_time_eeprom_to_ms = 0.625
                    advertisement_time = (
                        int.from_bytes(self.data[6:], byteorder="little")
                        * advertisement_time_eeprom_to_ms
                    )
                    data_explanation += ": " + ", ".join([
                        f"⟳ {time_normal_to_reduced_ms} ms",
                        f"📢 {advertisement_time} ms",
                    ])
            elif subcommand == 17:
                data_explanation = (
                    f"{verb} MAC address of device "
                    f"with device number “{device_number}”"
                )
                if is_acknowledgment and len(self.data) >= 8:
                    data_explanation += f": {mac_address()}"
            elif subcommand == 18:
                verb = (
                    "Acknowledge connection request"
                    if is_acknowledgment
                    else "Request connection"
                )
                data_explanation = (
                    f"{verb} to device with MAC address “{mac_address()}”"
                )

        return data_explanation

    # pylint: enable=too-many-branches, too-many-locals, too-many-statements

    def _data_explanation_streaming(self) -> str:
        """Retrieve a textual representation of streaming messages

        Returns
        -------

        A textual description of the data contained in the message

        """

        if len(self.data) < 1:
            return ""

        identifier = self.identifier()
        data_explanation = ""

        block_command = identifier.block_command_name()

        StreamingFormatClass = (
            StreamingFormat
            if block_command == "Data"
            else (
                StreamingFormatVoltage
                if block_command == "Voltage"
                else StreamingFormat
            )
        )
        streaming_format: StreamingFormat = StreamingFormatClass(self.data[0])
        data_explanation += repr(streaming_format)

        if identifier.is_acknowledgment() and len(self.data) >= 2:
            sequence_counter = self.data[1]
            explanations = [f"Sequence Counter: {sequence_counter}"]
            size_value = streaming_format.data_bytes()
            values = [
                int.from_bytes(
                    self.data[start : start + size_value], byteorder="little"
                )
                for start in range(2, len(self.data), size_value)
            ]
            explanations.extend([
                f"{explanation}: {value}"
                for explanation, value in zip(
                    streaming_format.value_explanations, values
                )
            ])
            data_explanation += ", " + ", ".join(explanations)

        return data_explanation

    def _data_explanation_configuration(self) -> str:
        identifier = self.identifier()
        data_explanation = ""

        if (
            identifier.block_command_name() == "Calibration Measurement"
            and len(self.data) >= 4
        ):
            return repr(CalibrationMeasurementFormat(self.data))

        return data_explanation

    def _data_explanation_eeprom(self) -> str:
        """Retrieve a textual representation of EEPROM messages

        Returns
        -------

        A textual description of the data contained in the message

        """

        identifier = self.identifier()
        data_explanation = ""

        if identifier.block_command_name() == "Read Write Request Counter":
            counter = int.from_bytes(self.data[4:], "little")
            data_explanation = f"EEPROM Write Requests: {counter}"
        elif (
            identifier.block_command_name() in {"Read", "Write"}
            and len(self.data) >= 8
        ):
            page = self.data[0]
            offset = self.data[1]
            length = self.data[2]
            data = list(self.data[4 : 4 + min(length, 4)])
            is_acknowledgment = self.identifier().is_acknowledgment()

            info = "Acknowledge request" if is_acknowledgment else "Request"
            verb = identifier.block_command_name().lower()
            data_explanation = (
                f"{info} to {verb} {length} bytes at page {page} "
                f"with offset {offset}"
            )
            read_request = verb == "read" and not is_acknowledgment
            if not read_request:
                data_explanation += f": {data}"

        return data_explanation

    def _data_explanation(self) -> str:
        """Retrieve a textual representation of the message data

        Returns
        -------

        A textual description of the data contained in the message

        """

        if len(self.data) <= 0:
            return ""

        identifier = self.identifier()

        if identifier.block_name() == "System":
            return self._data_explanation_system()

        if identifier.block_name() == "Streaming":
            return self._data_explanation_streaming()

        if identifier.block_name() == "Configuration":
            return self._data_explanation_configuration()

        if identifier.block_name() == "EEPROM":
            return self._data_explanation_eeprom()

        return ""

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
        ...             block_command='Data',
        ...             sender='SPU 1',
        ...             receiver='STH 1',
        ...             request=True))
        >>> search('# (.*)', representation)[1]
        '[SPU 1 → STH 1, Block: Streaming, Command: Data, Request]'

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

        >>> representation = repr(
        ...     Message(block='System',
        ...             block_command='Get/Set State',
        ...             sender='SPU 2',
        ...             receiver='STU 1',
        ...             request=True,
        ...             data=[0b10_0_101]))
        >>> search('# (.*)', representation)[1] # doctest:+NORMALIZE_WHITESPACE
        '[SPU 2 → STU 1, Block: System, Command: Get/Set State, Request]
         (Get State, Location: Application, State: Operating)'

        """

        identifier = self.identifier()
        data_explanation = self._data_explanation()

        explanation = (
            f"{identifier} ({data_explanation})"
            if data_explanation
            else repr(identifier)
        )

        data_representation = " ".join(
            [hex(self.data[byte]) for byte in range(len(self.data))]
        )
        bit_values = [
            f"0b{identifier.value:029b}",
            str(len(self.data)),
            data_representation,
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

        return Message(
            identifier=self.identifier().acknowledge(),
            error=error,
            data=list(self.data),
        )

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
                    is_extended_id=True, dlc=3, data=[0x1, 0x2, 0x3])

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

if __name__ == "__main__":
    from doctest import testmod

    testmod()
