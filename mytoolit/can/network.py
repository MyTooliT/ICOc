"""Support for working with the ICOtronic system

To communicate with the ICOtronic system, create a new `Network` object and
use its various coroutines. Unfortunately we do not offer an official API
documentation yet. For now we recommend you take a look at the
doctests of the `Network` class or the code for the `icon` command line tool
(mytoolit.scripts.icon).
"""

# pylint: disable=too-many-lines

# -- Imports ------------------------------------------------------------------

from __future__ import annotations

from asyncio import get_running_loop, CancelledError, Queue, sleep, wait_for
from datetime import date
from logging import getLogger
from struct import pack, unpack
from sys import platform
from time import time
from types import TracebackType
from typing import List, NamedTuple, Optional, Sequence, Type, Union

from can import Bus, Listener, Message as CANMessage, Notifier
from can.interfaces.pcan.pcan import PcanError
from semantic_version import Version
from netaddr import EUI

from mytoolit.eeprom import EEPROMStatus
from mytoolit.config import settings
from mytoolit.measurement import ADC_MAX_VALUE
from mytoolit.can.adc import ADCConfiguration
from mytoolit.can.calibration import CalibrationMeasurementFormat
from mytoolit.can.error import UnsupportedFeatureException
from mytoolit.can.message import Message
from mytoolit.can.node import Node
from mytoolit.can.streaming import (
    AsyncStreamBuffer,
    StreamingConfiguration,
    StreamingData,
    StreamingFormat,
    StreamingFormatVoltage,
)
from mytoolit.can.status import State
from mytoolit.measurement import convert_raw_to_supply_voltage
from mytoolit.measurement.sensor import SensorConfiguration
from mytoolit.utility import convert_bytes_to_text
from mytoolit.utility.log import get_log_file_handler

# -- Classes ------------------------------------------------------------------


class NetworkError(Exception):
    """Exception for errors in the MyTooliT network"""


class CANInitError(NetworkError):
    """Exception for CAN initialization problems"""


class ErrorResponseError(NetworkError):
    """Exception for erroneous response messages"""


class NoResponseError(NetworkError):
    """Thrown if no response message for a request was received"""


class Response(NamedTuple):
    """Used to store a response (message)"""

    message: CANMessage  # The response message
    is_error: bool  # States if the response was an error or a normal response
    error_message: str  # Optional explanation for the error reason


class Times(NamedTuple):
    """Advertisement time and time until deeper sleep mode"""

    advertisement: float
    sleep: int

    def __repr__(self) -> str:
        """Return a string representation of the object

        Returns
        -------

        A string that contains the advertisement time and sleep time values

        """

        return ", ".join([
            f"Advertisement Time: {self.advertisement} ms",
            f"Sleep Time: {self.sleep} ms",
        ])


class STHDeviceInfo(NamedTuple):
    """Used to store information about a (disconnected) STH"""

    name: str  # The (Bluetooth advertisement) name of the STH
    device_number: int  # The device number of the STH
    mac_address: EUI  # The (Bluetooth) MAC address of the STH
    rssi: int  # The RSSI of the STH

    def __repr__(self) -> str:
        """Return the string representation of an STH"""

        attributes = ", ".join([
            f"Name: {self.name}",
            f"Device Number: {self.device_number}",
            f"MAC address: {self.mac_address}",
            f"RSSI: {self.rssi}",
        ])
        return f"🤖 {attributes}"


class Logger(Listener):
    """Log ICOtronic CAN messages in a machine and human readable format"""

    def __init__(self):
        """Initialize the logger"""

        logger = getLogger("network.can")
        # We use `Logger` in the code below, since the `.logger` attribute
        # stores internal DynaConf data
        logger.setLevel(settings.Logger.can.level)
        logger.addHandler(get_log_file_handler("can.log"))

    def on_message_received(self, msg: CANMessage) -> None:
        """React to a received message on the bus

        Parameters
        ----------

        msg:
            The received CAN message the notifier should react to

        """

        getLogger("network.can").debug("%s", Message(msg))

    def on_error(self, exc: Exception) -> None:
        """Handle any exception in the receive thread.

        Parameters
        ----------

        exc:
            The exception causing the thread to stop

        """

        getLogger("network.can").error(
            "Error while monitoring CAN bus data: %s", exc
        )

    def stop(self) -> None:
        """Stop handling new messages"""


class ResponseListener(Listener):
    """A listener that reacts to messages containing a certain id"""

    def __init__(
        self,
        message: Message,
        expected_data: Union[bytearray, Sequence[Optional[int]], None],
    ) -> None:
        """Initialize the listener using the given identifier

        Parameters
        ----------

        message:
            The sent message this listener should react to

        expected_data:
           This optional field specifies the expected acknowledgment data.
           You can either specify to:
               - not check the message data (`None`),
               - check the first bytes by providing a bytearray,
               - check the first bytes by providing a heterogenous list
                 of numbers (data byte will be checked for equality) and
                 `None` (data byte will not be checked).

        """

        self.queue: Queue[Response] = Queue()
        identifier = message.identifier()
        self.acknowledgment_identifier = identifier.acknowledge()
        self.error_identifier = identifier.acknowledge(error=True)
        self.expected_data = expected_data

    def on_message_received(self, msg: CANMessage) -> None:
        """React to a received msg on the bus

        Parameters
        ----------

        msg:
            The received CAN message the notifier should react to

        """

        identifier = msg.arbitration_id
        error_response = identifier == self.error_identifier.value
        normal_response = identifier == self.acknowledgment_identifier.value

        # We only store CAN messages that contain the expected (error) response
        # message identifier

        # Also set an error response, if the retrieved message data does not
        # match the expected data
        expected_data = self.expected_data
        error_reason = ""
        if normal_response and expected_data is not None:
            error_response |= any(
                expected != data
                for expected, data in zip(expected_data, msg.data)
                if expected is not None
            )
            error_reason = (
                "Unexpected response message data:\n"
                f"Expected: {list(expected_data)}\n"
                f"Received: {list(msg.data)}"
            )
        elif error_response:
            error_reason = "Received error response"

        if error_response or normal_response:
            self.queue.put_nowait(
                Response(
                    message=msg,
                    is_error=error_response,
                    error_message=error_reason,
                )
            )

    async def on_message(self) -> Optional[Response]:
        """Return answer messages for the specified message identifier


        Returns
        -------

        A response containing

        - the response message for the message with the identifier given at
          object creation, and
        - the error status of the response message

        """

        return await self.queue.get()

    def on_error(self, exc: Exception) -> None:
        """Handle any exception in the receive thread.

        Parameters
        ----------

        exc:
            The exception causing the thread to stop

        """

        getLogger().error("Error while monitoring CAN bus data: %s", exc)

    def stop(self) -> None:
        """Stop handling new messages"""


class DataStreamContextManager:
    """Open and close a data stream from a sensor device"""

    def __init__(
        self,
        network: Network,
        channels: StreamingConfiguration,
        timeout: float,
    ) -> None:
        """Create a new stream context manager for the given Network

        Parameters
        ----------

        network:
            The CAN network class for which this context manager handles
            sensor device stream data

        channels:
            A streaming configuration that specifies which of the three
            streaming channels should be enabled or not

        timeout
            The amount of seconds between two consecutive messages, before
            a TimeoutError will be raised

        """

        self.network = network
        self.reader = AsyncStreamBuffer(channels, timeout)
        self.channels = channels

    async def __aenter__(self) -> AsyncStreamBuffer:
        """Open the stream of measurement data

        Returns
        -------

        The stream buffer for the measurement stream

        """

        reader = self.reader
        # Raise exception if there if there is more than one second worth
        # of buffered data
        max_buffer_size = (
            await self.network.read_adc_configuration()
        ).sample_rate()
        self.reader.max_buffer_size = max_buffer_size
        await self.network.start_streaming_data(self.channels)
        self.network.notifier.add_listener(reader)
        return reader

    async def __aexit__(
        self,
        exception_type: Optional[Type[BaseException]],
        exception_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        """Clean up the resources used by the stream

        Parameters
        ----------

        exception_type:
            The type of the exception in case of an exception

        exception_value:
            The value of the exception in case of an exception

        traceback:
            The traceback in case of an exception

        """
        logger = getLogger(__name__)

        self.reader.stop()
        self.network.notifier.remove_listener(self.reader)

        if exception_type is None or isinstance(
            exception_type, type(CancelledError)
        ):
            logger.info("Stopping stream")
            await self.network.stop_streaming_data()
        else:
            # If there was an error while streaming data, then stoping the
            # stream will usually also fail. Because of this we only try once
            # and ignore any errors.
            #
            # If we did not do that, then the user of the API would be notified
            # about the error to disable the stream, but not about the original
            # error. It would also take considerably more time until the
            # computer would report an error, since the code would usually try
            # to stop the stream (and fail) multiple times beforehand.
            logger.info("Stopping stream after error (%s)", exception_type)
            await self.network.stop_streaming_data(
                retries=1, ignore_errors=True
            )


# pylint: disable=too-many-public-methods


class Network:
    """Basic class to communicate with STU and sensor devices"""

    # Stores the conversion rate for the EEPROM advertisement times:
    # - https://mytoolit.github.io/Documentation/#page-system-configuration
    ADVERTISEMENT_TIME_EEPROM_TO_MS = 0.625

    def __init__(self) -> None:
        """Create a new network from the given arguments

        Please note, that you have to clean up used resources after you use
        this class using the method `shutdown`. Since this class implements
        the context manager interface we recommend you use a with statement to
        handle the cleanup phase automatically.

        Examples
        --------

        >>> from asyncio import run

        Create and shutdown the network explicitly

        >>> async def create_and_shutdown_network():
        ...     network = Network()
        ...     await network.shutdown()
        >>> run(create_and_shutdown_network())

        Use a context manager to handle the cleanup process automatically

        >>> async def create_and_shutdown_network():
        ...     async with Network() as network:
        ...         pass
        >>> run(create_and_shutdown_network())

        """

        configuration = (
            settings.can.linux
            if platform == "linux"
            else (
                settings.can.mac
                if platform == "darwin"
                else settings.can.windows
            )
        )
        try:
            self.bus = Bus(  # pylint: disable=abstract-class-instantiated
                channel=configuration.get("channel"),
                interface=configuration.get("interface"),
                bitrate=configuration.get("bitrate"),
            )  # type: ignore[abstract]
        except (PcanError, OSError) as error:
            raise CANInitError(
                f"Unable to initialize CAN connection: {error}\n\n"
                "Possible reason:\n\n"
                "• CAN adapter is not connected to the computer"
            ) from error

        # We create the notifier when we need it for the first time, since
        # there might not be an active loop when you create the network object
        self._notifier: Optional[Notifier] = None
        self.sender = Node("SPU 1")

    async def __aenter__(self) -> Network:
        """Initialize the network

        Returns
        -------

        An initialized network object

        """

        self.bus.__enter__()

        return self

    async def __aexit__(
        self,
        exception_type: Optional[Type[BaseException]],
        exception_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        """Disconnect from the network

        Parameters
        ----------

        exception_type:
            The type of the exception in case of an exception

        exception_value:
            The value of the exception in case of an exception

        traceback:
            The traceback in case of an exception

        """

        await self.shutdown()

    async def shutdown(self) -> None:
        """Cleanup resources"""

        # Deactivating Bluetooth might fail if there were connection problems
        # before. We ignore this error to make sure, that the cleanup code
        # below is executed in this error scenario.
        try:
            await self.deactivate_bluetooth("STU 1")
        except NoResponseError:
            pass

        if self._notifier is not None:
            self._notifier.stop()

        self.bus.shutdown()

    @property
    def notifier(self) -> Notifier:
        """Access the CAN notifier

        Returns
        -------

        The notifier object of this CAN class

        """

        # If there is no notifier yet, create it
        if self._notifier is None:
            # We explicitly specify the event loop, since not doing so slows
            # down the execution considerably (adding multiple seconds of
            # delay)
            self._notifier = Notifier(
                self.bus, listeners=[Logger()], loop=get_running_loop()
            )

        assert self._notifier is not None

        return self._notifier

    # pylint: disable=too-many-arguments

    async def _request(
        self,
        message: Message,
        description: str,
        response_data: Union[bytearray, List[Union[int, None]], None] = None,
        minimum_timeout: float = 0,
        retries: int = 10,
    ) -> CANMessage:
        """Send a request message and wait for the response

        Parameters
        ----------

        message:
            The message containing the request

        description:
            A description of the request used in error messages

        response_data:
           Specifies the expected data in the acknowledgment message

        minimum_timeout:
           Minimum time before attempting additional connection attempt
           in seconds

        retries:
           The number of times the message is sent again, if no response was
           sent back in a certain amount of time

        Returns
        -------

        The response message for the given request

        Raises
        ------

        NoResponseError:
            If the receiver did not respond to the message after retries
            amount of messages sent

        ErrorResponseError:
            If the receiver answered with an error message

        """

        for attempt in range(retries):
            listener = ResponseListener(message, response_data)
            self.notifier.add_listener(listener)
            getLogger("network.can").debug("%s", message)
            self.bus.send(message.to_python_can())

            try:
                # We increase the timeout after the first and second try.
                # This way we reduce the chance of the warning:
                #
                # - “Bus error: an error counter reached the 'heavy'/'warning'
                #   limit”
                #
                # happening. This warning might show up after
                #
                # - we flashed the STU,
                # - sent a reset command to the STU, and then
                # - wait for the response of the STU.
                timeout = max(min(attempt * 0.1 + 0.5, 2), minimum_timeout)
                response = await wait_for(
                    listener.on_message(), timeout=timeout
                )
                assert response is not None
            except TimeoutError:
                continue
            finally:
                listener.stop()
                self.notifier.remove_listener(listener)

            if response.is_error:
                raise ErrorResponseError(
                    "Received unexpected response for request to "
                    f"{description}:\n\n{response.error_message}\n"
                    f"Response Message: {Message(response.message)}"
                )

            return response.message

        raise NoResponseError(f"Unable to {description}")

    async def _request_bluetooth(
        self,
        node: Union[str, Node],
        subcommand: int,
        description: str,
        device_number: Optional[int] = None,
        data: Optional[List[int]] = None,
        response_data: Optional[List[Optional[int]]] = None,
    ) -> CANMessage:
        """Send a request for a certain Bluetooth command

        Parameters
        ----------

        node:
            The node on which the Bluetooth command should be executed

        subcommand:
            The number of the Bluetooth subcommand

        device_number:
            The device number of the Bluetooth device

        description:
            A description of the request used in error messages

        data:
            An optional list of bytes that should be included in the request

        response_data:
            An optional list of expected data bytes in the response message

        Returns
        -------

        The response message for the given request

        """

        device_number = 0 if device_number is None else device_number
        data = [0] * 6 if data is None else data
        message = Message(
            block="System",
            block_command="Bluetooth",
            sender=self.sender,
            receiver=node,
            request=True,
            data=[subcommand, device_number] + data,
        )

        # The Bluetooth subcommand and device number should be the same in the
        # response message.
        #
        # Unfortunately the device number is currently not the same for:
        #
        # - the subcommand that sets the second part of the name, and
        # - the subcommand that retrieves the MAC address
        # - the subcommand that writes the time values for the reduced energy
        #   mode
        #
        # The subcommand number in the response message for the commands to
        # set the time values for
        #
        # - the reduced energy mode and
        # - the lowest energy mode
        #
        # are unfortunately also not correct.
        set_second_part_name = 4
        set_times_reduced_energy = 14
        set_times_reduced_lowest = 16
        get_mac_address = 17
        expected_data: List[Optional[int]]
        if subcommand in {get_mac_address, set_second_part_name}:
            expected_data = [subcommand, None]
        elif subcommand in {
            set_times_reduced_energy,
            set_times_reduced_lowest,
        }:
            expected_data = [None, None]
        else:
            expected_data = [subcommand, device_number]

        if response_data is not None:
            expected_data.extend(response_data)

        return await self._request(
            message, description=description, response_data=expected_data
        )

    # pylint: enable=too-many-arguments

    async def _request_product_data(
        self,
        block_command: Union[str, int],
        description: str,
        node: Union[str, Node],
    ) -> CANMessage:
        """Send a request for product data

        Parameters
        ----------

        node:
            The node on which the block command should be executed

        block_command:
            The name or number of the block command

        description:
            A description of the request used in error messages

        Returns
        -------

        The response message for the given request

        """

        message = Message(
            block="Product Data",
            block_command=block_command,
            sender=self.sender,
            receiver=node,
            request=True,
            data=[0] * 8,
        )

        return await self._request(message, description=description)

    # ==========
    # = System =
    # ==========

    async def reset_node(self, node: Union[str, Node]) -> None:
        """Reset the specified node

        Parameters
        ----------

        node:
            The node to reset

        Examples
        --------

        >>> from asyncio import run

        Reset connected node

        >>> async def reset():
        ...     async with Network() as network:
        ...         await network.reset_node('STU 1')
        >>> run(reset())

        Reset node, which is not connected

        >>> async def reset():
        ...     async with Network() as network:
        ...         await network.reset_node('STH 1')
        >>> run(reset()) # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
            ...
        NoResponseError: Unable to reset node “STH 1”

        """

        message = Message(
            block="System",
            block_command="Reset",
            sender=self.sender,
            receiver=node,
            request=True,
        )
        await self._request(
            message,
            description=f"reset node “{node}”",
            response_data=message.data,
            minimum_timeout=1,
        )

    # -----------------
    # - Get/Set State -
    # -----------------

    async def get_state(self, node: Union[str, Node] = "STU 1") -> State:
        """Get the current state of the specified node

        Parameters
        ----------

        node:
            The node which should return its state

        Example
        -------

        >>> from asyncio import run

        Get state of STU 1

        >>> async def get_state():
        ...     async with Network() as network:
        ...         return await network.get_state('STU 1')
        >>> run(get_state())
        Get State, Location: Application, State: Operating

        """

        message = Message(
            block="System",
            block_command="Get/Set State",
            sender=self.sender,
            receiver=node,
            request=True,
            data=[(State(mode="Get")).value],
        )

        response = await self._request(
            message, description=f"get state of node “{node}”"
        )

        return State(response.data[0])

    # -------------
    # - Bluetooth -
    # -------------

    async def activate_bluetooth(self, node: Union[str, Node] = "STU 1"):
        """Activate Bluetooth on the specified node

        Parameters
        ----------

        node:
            The node on which Bluetooth should be activated

        Example
        -------

        >>> from asyncio import run

        Activate Bluetooth on STU 1

        >>> async def activate():
        ...     async with Network() as network:
        ...         await network.activate_bluetooth('STU 1')
        >>> run(activate())

        """

        await self._request_bluetooth(
            node=node,
            subcommand=1,
            description=f"activate Bluetooth of node “{node}”",
            response_data=6 * [0],  # type: ignore[arg-type]
        )

    async def deactivate_bluetooth(
        self, node: Union[str, Node] = "STU 1"
    ) -> None:
        """Deactivate Bluetooth on a node

        Parameters
        ----------

        node:
            The node where Bluetooth should be deactivated

        Example
        -------

        >>> from asyncio import run, sleep

        Deactivate Bluetooth on STU 1

        >>> async def deactivate_bluetooth():
        ...     async with Network() as network:
        ...         # Deactivate Bluetooth connection
        ...         await network.deactivate_bluetooth('STU 1')
        >>> run(deactivate_bluetooth())

        """

        await self._request_bluetooth(
            node=node,
            subcommand=9,
            description=f"deactivate Bluetooth on “{node}”",
            response_data=6 * [0],  # type: ignore[arg-type]
        )

    async def get_available_devices(
        self, node: Union[str, Node] = "STU 1"
    ) -> int:
        """Retrieve the number of available Bluetooth devices at a node

        Parameters
        ----------

        node:
            The node which should retrieve the number of available Bluetooth
            devices

        Returns
        -------

        The number of available Bluetooth devices

        Example
        -------

        >>> from asyncio import run, sleep

        Get the number of available Bluetooth devices at STU 1

        >>> async def get_number_bluetooth_devices():
        ...     async with Network() as network:
        ...         await network.activate_bluetooth('STU 1')
        ...
        ...         # We assume at least one STH is available
        ...         number_sths = 0
        ...         while number_sths <= 0:
        ...             number_sths = await (
        ...                 network.get_available_devices('STU 1'))
        ...             await sleep(0.1)
        ...
        ...         return number_sths
        >>> run(get_number_bluetooth_devices()) >= 0
        1

        """

        answer = await self._request_bluetooth(
            node=node,
            subcommand=2,
            description=f"get available Bluetooth devices of node “{node}”",
        )

        available_devices = int(convert_bytes_to_text(answer.data[2:]))

        return available_devices

    async def get_name(
        self, node: Union[str, Node] = "STU 1", device_number: int = 0xFF
    ) -> str:
        """Retrieve the name of a Bluetooth device

        You can use this method to name of both

        1. disconnected and
        2. connected

        devices.

        1. For disconnected devices (STHs) you will usually use the STU (e.g.
           `STU 1`) and the device number at the STU (in the range `0` up to
           the number of devices - 1) to retrieve the name.

        2. For connected devices you will use the device name and the special
           “self addressing” device number (`0xff`) to ask a device about its
           own name. **Note**: A connected STH will return its own name,
           regardless of the value of the device number.

        Parameters
        ----------

        node:
            The node which has access to the Bluetooth device

        device_number:
            The number of the Bluetooth device (0 up to the number of
            available devices - 1; 0xff for self addressing).

        Returns
        -------

        The (Bluetooth broadcast) name of the device

        Example
        -------

        >>> from asyncio import run, sleep
        >>> from platform import system

        Get Bluetooth advertisement name of device “0” from STU 1

        >>> if system() == 'Linux':
        ...    async def reset():
        ...        async with Network() as network:
        ...            await network.reset_node('STU 1')
        ...    run(reset())
        >>> async def get_bluetooth_device_name():
        ...     async with Network() as network:
        ...         await network.activate_bluetooth('STU 1')
        ...         # Wait for device scan in node STU 1 to take place
        ...         await sleep(2)
        ...         # We assume that at least one STH is available
        ...         return await network.get_name('STU 1', device_number=0)
        >>> sth_name = run(get_bluetooth_device_name())
        >>> isinstance(sth_name, str)
        True
        >>> 0 <= len(sth_name) <= 8
        True

        """

        description = f"name of device “{device_number}” from “{node}”"

        answer = await self._request_bluetooth(
            node=node,
            subcommand=5,
            device_number=device_number,
            description=f"get first part of {description}",
        )

        first_part = convert_bytes_to_text(answer.data[2:])

        answer = await self._request_bluetooth(
            node=node,
            device_number=device_number,
            subcommand=6,
            description=f"get second part of {description}",
        )

        second_part = convert_bytes_to_text(answer.data[2:])

        return first_part + second_part

    async def set_name(
        self, name: str, node: Union[str, Node] = "STU 1"
    ) -> None:
        """Set the name of a node

        Parameters
        ----------

        name:
            The new name for the device

        node:
            The node which should be renamed

        Example
        -------

        >>> from asyncio import run

        Set name of STU 1 to the (default name) “Valerie”

        >>> async def set_name(name):
        ...     async with Network() as network:
        ...         await network.set_name(name=name, node='STU 1')
        >>> run(set_name("Valerie"))

        """

        if not isinstance(name, str):
            raise TypeError("Name must be str, not type(identifier).__name__")

        bytes_name = list(name.encode("utf-8"))
        length_name = len(bytes_name)
        if length_name > 8:
            raise ValueError(
                f"Name is too long ({length_name} bytes). "
                "Please use a name between 0 and 8 bytes."
            )

        # Use 0 bytes at end of names that are shorter than 8 bytes
        bytes_name.extend([0] * (8 - length_name))
        description = f"name of “{node}”"
        self_addressing = 0xFF

        await self._request_bluetooth(
            node=node,
            subcommand=3,
            device_number=self_addressing,
            data=bytes_name[:6],
            description=f"set first part of {description}",
        )

        await self._request_bluetooth(
            node=node,
            subcommand=4,
            device_number=self_addressing,
            data=bytes_name[6:] + [0] * 4,
            description=f"set second part of {description}",
        )

    async def connect_with_device_number(
        self, device_number: int = 0, node: Union[str, Node] = "STU 1"
    ) -> bool:
        """Connect to a Bluetooth device using a device number

        Parameters
        ----------

        device_number:
            The number of the Bluetooth device (0 up to the number of
            available devices - 1; 0x00 for self addressing).

        node:
            The node which should connect to the Bluetooth device

        Returns
        -------

        - True, if
          1. in search mode,
          2. at least single device was found,
          3. no legacy mode,
          4. and scanning mode active
        - False, otherwise

        Example
        -------

        >>> from asyncio import run, sleep

        Connect to device “0” of STU 1

        >>> async def connect_bluetooth_device_number():
        ...     async with Network() as network:
        ...         await network.activate_bluetooth('STU 1')
        ...         # We assume that at least one STH is available
        ...         status = False
        ...         while not status:
        ...             status = await network.connect_with_device_number(
        ...                         device_number=0, node='STU 1')
        ...
        ...         # Return status of Bluetooth device connect response
        ...         return status
        >>> run(connect_bluetooth_device_number())
        True

        """

        response = await self._request_bluetooth(
            node=node,
            subcommand=7,
            device_number=device_number,
            description=f"connect to “{device_number}” from “{node}”",
        )

        return bool(response.data[2])

    async def is_connected(self, node: Union[str, Node] = "STU 1") -> bool:
        """Check if the node is connected to a Bluetooth device

        Parameters
        ----------

        node:
            The node which should check if it is connected to a Bluetooth
            device

        Returns
        -------

        - True, if a Bluetooth device is connected to the node
        - False, otherwise

        Example
        -------

        >>> from asyncio import run, sleep

        Check connection of device “0” to STU 1

        >>> async def check_bluetooth_connection():
        ...     async with Network() as network:
        ...         await network.activate_bluetooth('STU 1')
        ...         await sleep(0.1)
        ...         connected_start = await network.is_connected('STU 1')
        ...
        ...         # We assume that at least one STH is available
        ...         await network.connect_with_device_number(0)
        ...         # Wait for device connection
        ...         connected_between = False
        ...         while not connected_between:
        ...             connected_between = await network.is_connected()
        ...             await sleep(0.1)
        ...             await network.connect_with_device_number(0)
        ...
        ...         # Deactivate Bluetooth connection
        ...         await network.deactivate_bluetooth('STU 1')
        ...         # Wait until device is disconnected
        ...         await sleep(0.1)
        ...         connected_after = await network.is_connected('STU 1')
        ...
        ...         return connected_start, connected_between, connected_after
        >>> run(check_bluetooth_connection())
        (False, True, False)

        """

        response = await self._request_bluetooth(
            node=node,
            subcommand=8,
            response_data=[None, *(5 * [0])],
            description=(
                f"check if “{node}” is connected to a Bluetooth device"
            ),
        )

        return bool(response.data[2])

    async def get_rssi(
        self, node: Union[str, Node] = "STH 1", device_number: int = 0xFF
    ):
        """Retrieve the RSSI (Received Signal Strength Indication) of a device

        You can use this method to retrieve the RSSI of both

        1. disconnected and
        2. connected

        devices.

        1. For disconnected devices (STHs) you will usually use the STU (e.g.
           `STU 1`) and the device number at the STU (in the range `0` up to
           the number of devices - 1) to retrieve the RSSI.

        2. For connected devices you will use the device name and the special
           “self addressing” device number (`0xff`) to ask a device about its
           own RSSI.

        Parameters
        ----------

        node:
            The node which should retrieve the RSSI

        device_number:
            The number of the Bluetooth device (0 up to the number of
            available devices - 1; 0xff for self addressing).

        Returns
        -------

        The RSSI of the device specified via node and device number

        Example
        -------

        >>> from asyncio import run, sleep

        Retrieve the RSSI of a disconnected STH

        >>> async def get_bluetooth_rssi():
        ...     async with Network() as network:
        ...         await network.activate_bluetooth('STU 1')
        ...
        ...         # We assume that at least one STH is available
        ...         # Get the RSSI of device “0”
        ...         return await network.get_rssi('STU 1', 0)
        >>> rssi = run(get_bluetooth_rssi())
        >>> -70 < rssi < 0
        True

        """

        response = await self._request_bluetooth(
            node=node,
            device_number=device_number,
            subcommand=12,
            description=f"get RSSI of “{device_number}” from “{node}”",
        )

        return int.from_bytes(
            response.data[2:3], byteorder="little", signed=True
        )

    async def read_energy_mode_reduced(self) -> Times:
        """Read the reduced energy mode (mode 1) sensor device time values

        To read the time values of the sensor device you need to connect to it
        first.

        See also:

        - https://mytoolit.github.io/Documentation/#sleep-advertisement-times

        Returns
        -------

        A tuple containing the advertisement time in the reduced energy mode
        in milliseconds and the time until the device will switch from the
        disconnected state to the low energy mode (mode 1) – if there is no
        activity – in milliseconds

        Example
        -------

        >>> from asyncio import run, sleep
        >>> from platform import system

        Retrieve the reduced energy time values of a sensor device

        >>> if system() == 'Linux':
        ...    async def reset():
        ...        async with Network() as network:
        ...            await network.reset_node('STU 1')
        ...    run(reset())
        >>> async def read_energy_mode_reduced():
        ...     async with Network() as network:
        ...         # We assume that at least one sensor device is available
        ...         await network.connect_sensor_device(0)
        ...         return await network.read_energy_mode_reduced()
        >>> times = run(read_energy_mode_reduced())
        >>> round(times.advertisement)
        1250
        >>> times.sleep
        300000

        """

        self_addressing = 0xFF
        response = await self._request_bluetooth(
            node="STH 1",
            device_number=self_addressing,
            subcommand=13,
            description="read reduced energy time values of sensor device",
        )

        wait_time = int.from_bytes(response.data[2:6], byteorder="little")
        advertisement_time = (
            int.from_bytes(response.data[6:], byteorder="little")
            * type(self).ADVERTISEMENT_TIME_EEPROM_TO_MS
        )

        return Times(sleep=wait_time, advertisement=advertisement_time)

    async def write_energy_mode_reduced(
        self, times: Optional[Times] = None
    ) -> None:
        """Writes the time values for the reduced energy mode (mode 1)

        To change the time values of the sensor device you need to connect to
        it first.

        See also:

        - https://mytoolit.github.io/Documentation/#sleep-advertisement-times

        Parameters
        ----------

        times:
            The values for the advertisement time in the reduced energy mode
            in milliseconds and the time until the device will go into the low
            energy mode (mode 1) from the disconnected state – if there is no
            activity – in milliseconds.

            If you do not specify these values then the default values from
            the configuration will be used

        Example
        -------

        >>> from asyncio import run, sleep
        >>> from platform import system

        Read and write the reduced energy time values of a sensor device

        >>> if system() == 'Linux':
        ...    async def reset():
        ...        async with Network() as network:
        ...            await network.reset_node('STU 1')
        ...    run(reset())
        >>> async def read_write_energy_mode_reduced(sleep, advertisement):
        ...     async with Network() as network:
        ...         # We assume that at least one sensor device is available
        ...         await network.connect_sensor_device(0)
        ...
        ...         await network.write_energy_mode_reduced(
        ...             Times(sleep=sleep, advertisement=advertisement))
        ...         times = await network.read_energy_mode_reduced()
        ...
        ...         # Overwrite changed values with default config values
        ...         await network.write_energy_mode_reduced()
        ...
        ...         return times
        >>> times = run(read_write_energy_mode_reduced(200_000, 2000))
        >>> times.sleep
        200000
        >>> round(times.advertisement)
        2000

        """

        if times is None:
            time_settings = settings.sensory_device.bluetooth
            times = Times(
                sleep=time_settings.sleep_time_1,
                advertisement=time_settings.advertisement_time_1,
            )

        sleep_time = times.sleep
        advertisement_time = round(
            times.advertisement / type(self).ADVERTISEMENT_TIME_EEPROM_TO_MS
        )

        data = list(
            sleep_time.to_bytes(4, "little")
            + advertisement_time.to_bytes(2, "little")
        )

        self_addressing = 0xFF
        await self._request_bluetooth(
            node="STH 1",
            device_number=self_addressing,
            subcommand=14,
            data=data,
            response_data=list(data),
            description="write reduced energy time values of sensor device",
        )

    async def read_energy_mode_lowest(self) -> Times:
        """Read the reduced lowest energy mode (mode 2) time values

        To read the time values of the sensor device you need to connect to it
        first.

        See also:

        - https://mytoolit.github.io/Documentation/#sleep-advertisement-times

        Returns
        -------

        A tuple containing the advertisement time in the lowest energy mode in
        milliseconds and the time until the device will switch from the
        reduced energy mode (mode 1) to the lowest energy mode (mode 2) – if
        there is no activity – in milliseconds

        Example
        -------

        >>> from asyncio import run, sleep

        Retrieve the reduced energy time values of a sensor device

        >>> async def read_energy_mode_lowest():
        ...     async with Network() as network:
        ...         # We assume that at least one sensor device is available
        ...         await network.connect_sensor_device(0)
        ...         return await network.read_energy_mode_lowest()
        >>> times = run(read_energy_mode_lowest())
        >>> round(times.advertisement)
        2500
        >>> times.sleep
        259200000

        """

        self_addressing = 0xFF
        response = await self._request_bluetooth(
            node="STH 1",
            device_number=self_addressing,
            subcommand=15,
            description="read lowest energy mode time values of sensor device",
        )

        wait_time = int.from_bytes(response.data[2:6], byteorder="little")
        advertisement_time = (
            int.from_bytes(response.data[6:], byteorder="little")
            * type(self).ADVERTISEMENT_TIME_EEPROM_TO_MS
        )

        return Times(sleep=wait_time, advertisement=advertisement_time)

    async def write_energy_mode_lowest(
        self, times: Optional[Times] = None
    ) -> None:
        """Writes the time values for the lowest energy mode (mode 2)

        To change the time values of the sensor device you need to connect to
        it first.

        See also:

        - https://mytoolit.github.io/Documentation/#sleep-advertisement-times

        Parameters
        ----------

        times:
            The values for the advertisement time in the reduced energy mode
            in milliseconds and the time until the device will go into the
            lowest energy mode (mode 2) from the reduced energy mode (mode 1)
            – if there is no activity – in milliseconds.

            If you do not specify these values then the default values from
            the configuration will be used

        Example
        -------

        >>> from asyncio import run, sleep

        Read and write the reduced energy time values of a sensor device

        >>> async def read_write_energy_mode_lowest(sleep, advertisement):
        ...     async with Network() as network:
        ...         # We assume that at least one sensor device is available
        ...         await network.connect_sensor_device(0)
        ...
        ...         await network.write_energy_mode_lowest(
        ...             Times(sleep=sleep, advertisement=advertisement))
        ...         times = await network.read_energy_mode_lowest()
        ...
        ...         # Overwrite changed values with default config values
        ...         await network.write_energy_mode_lowest()
        ...
        ...         return times
        >>> times = run(read_write_energy_mode_lowest(200_000, 2000))
        >>> times.sleep
        200000
        >>> round(times.advertisement)
        2000

        """

        if times is None:
            time_settings = settings.sensory_device.bluetooth
            times = Times(
                sleep=time_settings.sleep_time_2,
                advertisement=time_settings.advertisement_time_2,
            )

        sleep_time = times.sleep
        advertisement_time = round(
            times.advertisement / type(self).ADVERTISEMENT_TIME_EEPROM_TO_MS
        )

        data = list(
            sleep_time.to_bytes(4, "little")
            + advertisement_time.to_bytes(2, "little")
        )

        self_addressing = 0xFF
        await self._request_bluetooth(
            node="STH 1",
            device_number=self_addressing,
            subcommand=16,
            data=data,
            response_data=list(data),
            description="write reduced energy time values of sensor device",
        )

    async def get_mac_address(
        self, node: Union[str, Node] = "STH 1", device_number: int = 0xFF
    ) -> EUI:
        """Retrieve the Bluetooth MAC address of a device

        You can use this method to retrieve the address of both

        1. disconnected and
        2. connected

        devices.

        1. For disconnected devices (STHs) you will usually use the STU (e.g.
           `STU 1`) and the device number at the STU (in the range `0` up to
           the number of devices - 1) to retrieve the MAC address.

        2. For connected devices you will use the device name and the special
           “self addressing” device number (`0xff`) to ask a device about its
           own device number. **Note**: A connected STH will return its own
           MAC address, regardless of the value of the device number.

        Parameters
        ----------

        node:
            The node which should retrieve the MAC address

        device_number:
            The number of the Bluetooth device (0 up to the number of
            available devices - 1; 0xff for self addressing).

        Returns
        -------

        The MAC address of the device specified via node and device number

        Example
        -------

        >>> from asyncio import run, sleep

        Retrieve the MAC address of STH 1

        >>> async def get_bluetooth_mac():
        ...     async with Network() as network:
        ...         # We assume that at least one STH is available
        ...         await network.connect_sensor_device(0)
        ...         return await network.get_mac_address('STH 1')
        >>> mac_address = run(get_bluetooth_mac())
        >>> isinstance(mac_address, EUI)
        True

        """

        response = await self._request_bluetooth(
            node=node,
            device_number=device_number,
            subcommand=17,
            description=f"get MAC address of “{device_number}” from “{node}”",
        )

        return EUI(":".join(f"{byte:02x}" for byte in response.data[:1:-1]))

    async def connect_with_mac_address(
        self, mac_address: EUI, node: Union[str, Node] = "STU 1"
    ) -> None:
        """Connect to a Bluetooth device using its MAC address

        Parameters
        ----------

        mac_address:
            The MAC address of the Bluetooth device

        node:
            The node which should connect to the Bluetooth device

        """

        mac_address_bytes_reversed = list(reversed(mac_address.packed))

        await self._request_bluetooth(
            node=node,
            subcommand=18,
            data=mac_address_bytes_reversed,
            response_data=mac_address_bytes_reversed,
            description=f"connect to device “{mac_address}” from “{node}”",
        )

    async def get_sensor_devices(
        self, node: Union[str, Node] = "STU 1"
    ) -> List[STHDeviceInfo]:
        """Retrieve a list of available sensor devices

        Parameters
        ----------

        node:
            The node which should retrieve the list of available Bluetooth
            devices

        Returns
        -------

        A list of available devices including:

        - device number,
        - name,
        - MAC address and
        - RSSI

        for each device

        Example
        -------

        >>> from asyncio import run, sleep
        >>> from netaddr import EUI

        Retrieve the list of Bluetooth devices at STU 1

        >>> async def get_sensor_devices():
        ...     async with Network() as network:
        ...
        ...         # We assume that at least one sensor device is available
        ...         devices = []
        ...         while not devices:
        ...             devices = await network.get_sensor_devices()
        ...             await sleep(0.1)
        ...
        ...         return devices
        >>> devices = run(get_sensor_devices())
        >>> len(devices) >= 1
        True
        >>> device = devices[0]

        >>> device.device_number
        0

        >>> isinstance(device.name, str)
        True
        >>> 0 <= len(device.name) <= 8
        True

        >>> -80 < device.rssi < 0
        True

        >>> isinstance(device.mac_address, EUI)
        True

        """

        await self.activate_bluetooth(node)
        available_devices = await self.get_available_devices(node)
        devices = []
        for device in range(available_devices):
            mac_address = await self.get_mac_address(node, device)
            rssi = await self.get_rssi(node, device)
            name = await self.get_name(node, device)

            devices.append(
                STHDeviceInfo(
                    device_number=device,
                    mac_address=mac_address,
                    name=name,
                    rssi=rssi,
                )
            )

        return devices

    async def connect_sensor_device(
        self, identifier: Union[int, str, EUI]
    ) -> None:
        """Connect to a sensor device (e.g. SHA, SMH or STH)

        Parameters
        ----------

        identifier:
            The

            - MAC address (`EUI`),
            - name (`str`), or
            - device number (`int`)

            of the sensor device we want to connect to

        Example
        -------

        >>> from asyncio import run

        Connect to the sensor device with device number `0`

        >>> async def connect_sensor_device():
        ...     async with Network() as network:
        ...         await network.connect_sensor_device(0)
        ...         return await network.is_connected()
        >>> run(connect_sensor_device())
        True

        """

        def get_sensor_device(
            devices: List[STHDeviceInfo], identifier: Union[int, str, EUI]
        ) -> Optional[STHDeviceInfo]:
            """Get the MAC address of a sensor device"""

            for device in devices:
                if (
                    isinstance(identifier, str)
                    and device.name == identifier
                    or isinstance(identifier, int)
                    and device.device_number == identifier
                    or device.mac_address == identifier
                ):
                    return device

            return None

        if not isinstance(identifier, (EUI, int, str)):
            raise TypeError(
                "Identifier must be int, str or EUI, not "
                f"{type(identifier).__name__}"
            )

        await self.activate_bluetooth("STU 1")

        # We wait for a certain amount of time for the connection to the
        # device to take place
        timeout_in_s = 20
        end_time = time() + timeout_in_s

        sensor_device = None
        sensor_devices: List[STHDeviceInfo] = []
        while sensor_device is None:
            if time() > end_time:
                sensor_devices_representation = "\n".join(
                    [repr(device) for device in sensor_devices]
                )
                device_info = (
                    "Found the following sensor devices:\n"
                    f"{sensor_devices_representation}"
                    if len(sensor_devices) > 0
                    else "No sensor devices found"
                )

                identifier_description = (
                    "MAC address"
                    if isinstance(identifier, EUI)
                    else (
                        "device_number"
                        if isinstance(identifier, int)
                        else "name"
                    )
                )
                raise TimeoutError(
                    "Unable to find sensor device with "
                    f"{identifier_description} “{identifier}” in "
                    f"{timeout_in_s} seconds\n\n{device_info}"
                )

            sensor_devices = await self.get_sensor_devices()
            sensor_device = get_sensor_device(sensor_devices, identifier)
            if sensor_device is None:
                await sleep(0.1)

        connection_attempt_time = time()
        while True:
            await self.connect_with_device_number(sensor_device.device_number)
            retry_time_s = 3
            end_time_retry = time() + retry_time_s
            while time() < end_time_retry:
                if time() > end_time:
                    connection_time = time() - connection_attempt_time
                    raise TimeoutError(
                        "Unable to connect to sensor device"
                        f" “{sensor_device}” in"
                        f" {connection_time:.3f} seconds"
                    )

                if await self.is_connected("STU 1"):
                    return

                await sleep(0.1)

    # =============
    # = Streaming =
    # =============

    # --------
    # - Data -
    # --------

    async def read_streaming_data_single(self) -> StreamingData:
        """Read a single set of raw ADC values from a connected sensor device

        Returns
        -------

        The latest three ADC values measured by the sensor device

        Examples
        --------

        >>> from asyncio import run
        >>> from platform import system

        >>> if system() == 'Linux':
        ...    async def reset():
        ...        async with Network() as network:
        ...            await network.reset_node('STU 1')
        ...    run(reset())
        >>> async def read_sensor_values():
        ...     async with Network() as network:
        ...         await network.connect_sensor_device(0)
        ...         return await network.read_streaming_data_single()
        >>> data = run(read_sensor_values())
        >>> all([0 <= value <= 0xffff for value in data.values])
        True

        """

        streaming_format = StreamingFormat(
            channels=StreamingConfiguration(
                first=True, second=True, third=True
            ),
            sets=1,
        )

        node = "STH 1"

        message = Message(
            block="Streaming",
            block_command="Data",
            sender=self.sender,
            receiver=node,
            request=True,
            data=[streaming_format.value],
        )

        response = await self._request(
            message,
            description=f"read single set of streaming values from “{node}”",
        )
        values = [
            int.from_bytes(word, byteorder="little")
            for word in (
                response.data[2:4],
                response.data[4:6],
                response.data[6:8],
            )
        ]
        assert len(values) == 2 or len(values) == 3

        data = StreamingData(
            values=values,
            timestamp=response.timestamp,
            counter=response.data[1],
        )

        return data

    async def start_streaming_data(
        self, channels: StreamingConfiguration
    ) -> None:
        """Start streaming data

        Parameters
        ----------

        channels:
            Specifies which of the three measurement channels should be
            enabled or disabled

        The CAN identifier that this coroutine returns can be used
        to filter CAN messages that contain the expected streaming data

        """

        streaming_format = StreamingFormat(
            channels=channels,
            streaming=True,
            sets=3 if channels.enabled_channels() <= 1 else 1,
        )
        node = "STH 1"
        message = Message(
            block="Streaming",
            block_command="Data",
            sender=self.sender,
            receiver=node,
            request=True,
            data=[streaming_format.value],
        )

        measurement_channels = [
            channel
            for channel in (
                "first" if channels.first else "",
                "second" if channels.second else "",
                "third" if channels.third else "",
            )
            if channel
        ]
        channels_text = "".join(
            (f"{channel}, " for channel in measurement_channels[:-2])
        ) + " and ".join(measurement_channels[-2:])

        await self._request(
            message,
            description=(
                f"enable streaming of {channels_text} measurement "
                f"channel of “{node}”"
            ),
        )

    async def stop_streaming_data(
        self, retries: int = 10, ignore_errors=False
    ) -> None:
        """Stop streaming data

        Parameters
        ----------

        retries:
            The number of times the message is sent again, if no response was
            sent back in a certain amount of time

        ignore_errors:
            Specifies, if this coroutine should ignore, if there were any
            problems while stopping the stream.

        """

        streaming_format = StreamingFormat(streaming=True, sets=0)
        node = "STH 1"
        message = Message(
            block="Streaming",
            block_command="Data",
            sender=self.sender,
            receiver=node,
            request=True,
            data=[streaming_format.value],
        )

        try:
            await self._request(
                message,
                description=f"disable data streaming of “{node}”",
                retries=retries,
            )
        except (NoResponseError, ErrorResponseError) as error:
            if not ignore_errors:
                raise error

    def open_data_stream(
        self,
        channels: StreamingConfiguration,
        timeout: float = 5,
    ) -> DataStreamContextManager:
        """Open measurement data stream

        Parameters
        ----------

        channels:
            Specifies which measurement channels should be enabled

        timeout:
            The amount of seconds between two consecutive messages, before
            a TimeoutError will be raised

        Returns
        -------

        A context manager object for managing stream data

        Examples
        --------

        >>> from asyncio import run

        >>> async def read_streaming_data():
        ...     async with Network() as network:
        ...         await network.connect_sensor_device(0)
        ...         channels = StreamingConfiguration(first=True, third=True)
        ...         async with network.open_data_stream(channels) as stream:
        ...             first = []
        ...             third = []
        ...             messages = 0
        ...             async for data, _ in stream:
        ...                 first.append(data.values[0])
        ...                 third.append(data.values[1])
        ...                 messages += 1
        ...                 if messages >= 3:
        ...                     break
        ...             return first, third
        >>> first, third = run(read_streaming_data())
        >>> len(first)
        3
        >>> len(third)
        3

        """

        return DataStreamContextManager(self, channels, timeout)

    # -----------
    # - Voltage -
    # -----------

    async def read_supply_voltage(self) -> float:
        """Read the current supply voltage of a connected STH

        Returns
        -------

        The supply voltage of the STH

        Example
        -------

        >>> from asyncio import run
        >>> from platform import system

        Read the supply voltage of STH 1

        >>> if system() == 'Linux':
        ...    async def reset():
        ...        async with Network() as network:
        ...            await network.reset_node('STU 1')
        ...    run(reset())
        >>> async def read_supply_voltage():
        ...     async with Network() as network:
        ...         await network.connect_sensor_device(0)
        ...         return await network.read_supply_voltage()
        >>> supply_voltage = run(read_supply_voltage())
        >>> 3 <= supply_voltage <= 4.2
        True

        """

        streaming_format = StreamingFormatVoltage(
            channels=StreamingConfiguration(first=True), sets=1
        )
        node = "STH 1"
        message = Message(
            block="Streaming",
            block_command="Voltage",
            sender=self.sender,
            receiver=node,
            request=True,
            data=[streaming_format.value],
        )

        response = await self._request(
            message, description=f"read supply voltage of “{node}”"
        )

        voltage_bytes = response.data[2:4]
        voltage_raw = int.from_bytes(voltage_bytes, "little")

        adc_configuration = await self.read_adc_configuration()

        return convert_raw_to_supply_voltage(
            voltage_raw,
            reference_voltage=adc_configuration.reference_voltage(),
        )

    # =================
    # = Configuration =
    # =================

    # -----------------------------
    # - Get/Set ADC Configuration -
    # -----------------------------

    async def read_adc_configuration(self) -> ADCConfiguration:
        """Read the current ADC configuration of a connected sensor node

        Returns
        -------

        The ADC configuration of the sensor node

        Examples
        --------

        >>> from asyncio import run

        Read ADC sensor config from device

        >>> async def read_adc_config():
        ...     async with Network() as network:
        ...         await network.connect_sensor_device(0)
        ...         return await network.read_adc_configuration()
        >>> run(read_adc_config()) # doctest:+NORMALIZE_WHITESPACE
        Get, Prescaler: 2, Acquisition Time: 8, Oversampling Rate: 64,
        Reference Voltage: 3.3 V

        """

        node = "STH 1"

        message = Message(
            block="Configuration",
            block_command="Get/Set ADC Configuration",
            sender=self.sender,
            receiver=node,
            request=True,
            data=[0] * 8,
        )

        response = await self._request(
            message, description=f"Read ADC configuration of “{node}”"
        )

        return ADCConfiguration(response.data[0:5])

    async def write_adc_configuration(
        self,
        reference_voltage: float = 3.3,
        prescaler: int = 2,
        acquisition_time: int = 8,
        oversampling_rate: int = 64,
    ) -> None:
        """Change the ADC configuration of a connected sensor device

        Parameters
        ----------

        reference_voltage:
            The ADC reference voltage in Volt
            (1.25, 1.65, 1.8, 2.1, 2.2, 2.5, 2.7, 3.3, 5, 6.6)

        prescaler:
            The ADC prescaler value (1 – 127)

        acquisition_time:
            The ADC acquisition time in number of cycles
            (1, 2, 3, 4, 8, 16, 32, … , 256)

        oversampling_rate:
            The ADC oversampling rate (1, 2, 4, 8, … , 4096)

        Examples
        --------

        >>> from asyncio import run

        Read and write ADC sensor config

        >>> async def write_read_adc_config():
        ...     async with Network() as network:
        ...         await network.connect_sensor_device(0)
        ...
        ...         await network.write_adc_configuration(3.3, 8, 8, 64)
        ...         modified_config1 = await network.read_adc_configuration()
        ...
        ...         adc_config = ADCConfiguration(reference_voltage=5.0,
        ...                                       prescaler=16,
        ...                                       acquisition_time=8,
        ...                                       oversampling_rate=128)
        ...         await network.write_adc_configuration(**adc_config)
        ...         modified_config2 = await network.read_adc_configuration()
        ...
        ...         # Write back default config values
        ...         await network.write_adc_configuration(3.3, 2, 8, 64)
        ...         return modified_config1, modified_config2
        >>> config1, config2 = run(write_read_adc_config())
        >>> config1 # doctest:+NORMALIZE_WHITESPACE
        Get, Prescaler: 8, Acquisition Time: 8, Oversampling Rate: 64,
        Reference Voltage: 3.3 V
        >>> config2 # doctest:+NORMALIZE_WHITESPACE
        Get, Prescaler: 16, Acquisition Time: 8, Oversampling Rate: 128,
        Reference Voltage: 5.0 V

        """

        node = "STH 1"
        adc_configuration = ADCConfiguration(
            set=True,
            prescaler=prescaler,
            acquisition_time=acquisition_time,
            oversampling_rate=oversampling_rate,
            reference_voltage=reference_voltage,
        )

        message = Message(
            block="Configuration",
            block_command="Get/Set ADC Configuration",
            sender=self.sender,
            receiver=node,
            request=True,
            data=adc_configuration.data,
        )

        await self._request(
            message, description=f"write ADC configuration of “{node}”"
        )

    # --------------------------------
    # - Get/Set Sensor Configuration -
    # --------------------------------

    async def read_sensor_configuration(self) -> SensorConfiguration:
        """Read the current sensor configuration

        Raises
        ------

        A `UnsupportedFeatureException` in case the sensor node replies with
        an error message

        Returns
        -------

        The sensor number for the different axes

        Examples
        --------

        >>> from asyncio import run

        Reading sensor config from device without sensor config support fails

        >>> async def read_sensor_config():
        ...     async with Network() as network:
        ...         await network.connect_sensor_device(0)
        ...         return await network.read_sensor_configuration()
        >>> config = run(
        ...     read_sensor_config()) #doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
           ...
        UnsupportedFeatureException: Reading sensor configuration is not
        supported

        """

        message = Message(
            block="Configuration",
            block_command=0x01,
            sender="SPU 1",
            receiver="STH 1",
            request=True,
            data=[0] * 8,
        )

        node = "STH 1"

        try:
            response = await self._request(
                message, description=f"read sensor configuration of “{node}”"
            )
        except ErrorResponseError as error:
            raise UnsupportedFeatureException(
                "Reading sensor configuration not supported"
            ) from error

        channels = response.data[1:4]

        return SensorConfiguration(*channels)

    async def write_sensor_configuration(
        self, sensors: SensorConfiguration
    ) -> None:
        """Change the sensor numbers for the different measurement channels

        If you use the sensor number `0` for one of the different measurement
        channels, then the sensor (number) for that channel will stay the same.

        Parameters
        ----------

        sensors:
            The sensor numbers of the different measurement channels

        """

        node = "STH 1"

        data = [
            0b1000_0000,
            sensors.first,
            sensors.second,
            sensors.third,
            *(4 * [0]),
        ]
        message = Message(
            block="Configuration",
            block_command=0x01,
            sender="SPU 1",
            receiver=node,
            request=True,
            data=data,
        )

        try:
            await self._request(
                message, description=f"set sensor configuration of “{node}”"
            )
        except ErrorResponseError as error:
            raise UnsupportedFeatureException(
                "Writing sensor configuration not supported"
            ) from error

    # ---------------------------
    # - Calibration Measurement -
    # ---------------------------

    async def _acceleration_self_test(
        self, activate: bool = True, dimension: str = "x"
    ) -> None:
        """Activate/Deactivate the accelerometer self test

        Parameters
        ----------

        activate:
            Either `True` to activate the self test or `False` to
            deactivate the self test

        dimension:
            The dimension (x=1, y=2, z=3) for which the self test should be
            activated/deactivated.

        """
        node = "STH 1"
        method = "Activate" if activate else "Deactivate"

        try:
            dimension_number = "xyz".index(dimension) + 1
        except ValueError as error:
            raise ValueError(
                f"Invalid dimension value: “{dimension}”"
            ) from error

        message = Message(
            block="Configuration",
            block_command="Calibration Measurement",
            sender=self.sender,
            receiver=node,
            request=True,
            data=CalibrationMeasurementFormat(
                set=True,
                element="Data",
                method=method,
                dimension=dimension_number,
            ).data,
        )

        await self._request(
            message,
            description=(
                f"{method.lower()} self test of {dimension}-axis of “{node}”"
            ),
        )

    async def activate_acceleration_self_test(
        self, dimension: str = "x"
    ) -> None:
        """Activate self test of STH accelerometer

        Parameters
        ----------

        dimension:
            The dimension (`x`, `y` or `z`) for which the self test should
            be activated.

        """

        await self._acceleration_self_test(activate=True, dimension=dimension)

    async def deactivate_acceleration_self_test(
        self, dimension: str = "x"
    ) -> None:
        """Deactivate self test of STH accelerometer

        Parameters
        ----------

        dimension:
            The dimension (`x`, `y` or `z`) for which the self test should
            be deactivated.

        """

        await self._acceleration_self_test(activate=False, dimension=dimension)

    async def read_acceleration_voltage(
        self, dimension: str = "x", reference_voltage: float = 3.3
    ) -> float:
        """Retrieve the current voltage in Volt

        Parameters
        ----------

        dimension:
            The dimension (x=1, y=2, z=3) for which the acceleration voltage
            should be measured

        reference_voltage:
            The reference voltage for the ADC in Volt

        Returns
        -------

        The voltage of the acceleration sensor in Volt

        Example
        -------

        >>> from asyncio import run
        >>> from platform import system

        Read the acceleration voltage of STH 1

        >>> if system() == 'Linux':
        ...    async def reset():
        ...        async with Network() as network:
        ...            await network.reset_node('STU 1')
        ...    run(reset())
        >>> async def read_acceleration_voltage():
        ...     async with Network() as network:
        ...         await network.connect_sensor_device(0)
        ...
        ...         before = await network.read_acceleration_voltage()
        ...         await network.activate_acceleration_self_test()
        ...         between = await network.read_acceleration_voltage()
        ...         await network.deactivate_acceleration_self_test()
        ...         after = await network.read_acceleration_voltage()
        ...
        ...         return (before, between, after)
        >>> before, between, after = run(read_acceleration_voltage())
        >>> before < between and after < between
        True

        """

        try:
            dimension_number = "xyz".index(dimension) + 1
        except ValueError as error:
            raise ValueError(
                f"Invalid dimension value: “{dimension}”"
            ) from error

        node = "STH 1"
        message = Message(
            block="Configuration",
            block_command="Calibration Measurement",
            sender=self.sender,
            receiver=node,
            request=True,
            data=CalibrationMeasurementFormat(
                set=True,
                element="Data",
                method="Measure",
                reference_voltage=reference_voltage,
                dimension=dimension_number,
            ).data,
        )

        response = await self._request(
            message, description=f"retrieve acceleration voltage of “{node}”"
        )

        adc_value = int.from_bytes(response.data[4:], "little")
        return adc_value / ADC_MAX_VALUE * reference_voltage

    # ==========
    # = EEPROM =
    # ==========

    async def read_eeprom(
        self,
        address: int,
        offset: int,
        length: int,
        node: Union[str, Node] = "STU 1",
    ) -> List[int]:
        """Read EEPROM data

        Parameters
        ----------

        address:
            The page number in the EEPROM

        offset:
            The offset to the base address in the specified page

        length:
            This value specifies how many bytes you want to read

        node:
            The node from which the EEPROM data should be retrieved

        Returns
        -------

        A list containing the EEPROM data at the specified location

        Example
        -------

        >>> from asyncio import run

        Read EEPROM data from STU 1

        >>> async def read_eeprom():
        ...     async with Network() as network:
        ...         return await network.read_eeprom(address=0, offset=1,
        ...                                          length=8, node='STU 1')
        >>> data = run(read_eeprom())
        >>> len(data)
        8
        >>> all((0 <= byte <= 255 for byte in data))
        True

        """

        read_data: List[int] = []
        reserved = [0] * 5
        data_start = 4  # Start index of data in response message

        while length > 0:
            # Read at most 4 bytes of data at once
            read_length = 4 if length > 4 else length
            message = Message(
                block="EEPROM",
                block_command="Read",
                sender=self.sender,
                receiver=Node(node),
                request=True,
                data=[address, offset, read_length, *reserved],
            )
            response = await self._request(
                message, description=f"read EEPROM data from “{node}”"
            )

            data_end = data_start + read_length
            read_data.extend(response.data[data_start:data_end])
            length -= read_length
            offset += read_length

        return read_data

    async def read_eeprom_float(
        self, address: int, offset: int, node: Union[str, Node] = "STU 1"
    ) -> float:
        """Read EEPROM data in float format

        Parameters
        ----------

        address:
            The page number in the EEPROM

        offset:
            The offset to the base address in the specified page

        node:
            The node from which the EEPROM data should be retrieved

        Returns
        -------

        The float number at the specified location of the EEPROM

        Example
        -------

        >>> from asyncio import run
        >>> from platform import system

        Read slope of acceleration for x-axis of STH 1

        >>> if system() == 'Linux':
        ...    async def reset():
        ...        async with Network() as network:
        ...            await network.reset_node('STU 1')
        ...    run(reset())
        >>> async def read_slope():
        ...     async with Network() as network:
        ...         await network.connect_sensor_device(0)
        ...         return await network.read_eeprom_float(
        ...             address=8, offset=0, node='STH 1')
        >>> slope = run(read_slope())
        >>> isinstance(slope, float)
        True

        """

        data = await self.read_eeprom(address, offset, length=4, node=node)
        return unpack("<f", bytearray(data))[0]

    # pylint: disable=too-many-arguments

    async def read_eeprom_int(
        self,
        address: int,
        offset: int,
        length: int,
        signed: bool = False,
        node: Union[str, Node] = "STU 1",
    ) -> int:
        """Read an integer value from the EEPROM

        Parameters
        ----------

        address:
            The page number in the EEPROM

        offset:
            The offset to the base address in the specified page

        length:
            This value specifies how long the number is in bytes

        signed:
            Specifies if `value` is a signed number (`True`) or an
            unsigned number (`False`)

        node:
            The node from which the EEPROM data should be retrieved

        Returns
        -------

        The number at the specified location of the EEPROM

        Example
        -------

        >>> from asyncio import run

        Read the operating time (in seconds) of STU 1

        >>> async def read_operating_time():
        ...     async with Network() as network:
        ...         return await network.read_eeprom_int(
        ...             address=5, offset=8, length=4, node='STU 1')
        >>> operating_time = run(read_operating_time())
        >>> operating_time >= 0
        True

        """

        return int.from_bytes(
            await self.read_eeprom(address, offset, length, node),
            "little",
            signed=signed,
        )

    # pylint: enable=too-many-arguments

    async def read_eeprom_text(
        self,
        address: int,
        offset: int,
        length: int,
        node: Union[str, Node] = "STU 1",
    ) -> str:
        """Read EEPROM data in ASCII format

        Please note, that this function will only return the characters up
        to the first null byte.

        Parameters
        ----------

        address:
            The page number in the EEPROM

        offset:
            The offset to the base address in the specified page

        length:
            This value specifies how many characters you want to read

        node:
            The node from which the EEPROM data should be retrieved

        Returns
        -------

        A string that contains the text at the specified location

        Example
        -------

        >>> from asyncio import run

        Read name of STU 1

        >>> async def read_name_eeprom():
        ...     async with Network() as network:
        ...         return await network.read_eeprom_text(
        ...             address=0, offset=1, length=8, node='STU 1')
        >>> name = run(read_name_eeprom())
        >>> 0 <= len(name) <= 8
        True
        >>> isinstance(name, str)
        True

        """

        data = await self.read_eeprom(address, offset, length, node)
        return convert_bytes_to_text(data, until_null=True)

    # pylint: disable=too-many-arguments

    async def write_eeprom(
        self,
        address: int,
        offset: int,
        data: List[int],
        length: Optional[int] = None,
        node: Union[str, Node] = "STU 1",
    ) -> None:
        """Write EEPROM data at the specified address

        Parameters
        ----------

        address:
            The page number in the EEPROM

        offset:
            The offset to the base address in the specified page

        data:
            A list of byte value that should be stored at the specified EEPROM
            location

        length:
            This optional parameter specifies how many of the bytes in `data`
            should be stored in the EEPROM. If you specify a length that is
            greater, than the size of the data list, then the remainder of
            the EEPROM data will be filled with null bytes.

        node:
            The node where the EEPROM data should be stored

        Example
        -------

        >>> from asyncio import run

        Write data to and read (same) data from EEPROM of STU 1

        >>> async def write_and_read_eeprom(data):
        ...     async with Network() as network:
        ...         await network.write_eeprom(
        ...             address=10, offset=3, data=data, node='STU 1')
        ...         return await network.read_eeprom(
        ...             address=10, offset=3, length=len(data), node='STU 1')
        >>> data = [1, 3, 3, 7]
        >>> read_data = run(write_and_read_eeprom(data))
        >>> data == read_data
        True

        """

        # Change data, if
        # - only a subset, or
        # - additional data
        # should be written to the EEPROM.
        if length is not None:
            # Cut off additional data bytes
            data = data[:length]
            # Fill up additional data bytes
            data.extend([0] * (length - len(data)))

        while data:
            write_data = data[:4]  # Maximum of 4 bytes per message
            write_length = len(write_data)
            # Use zeroes to fill up missing data bytes
            write_data.extend([0] * (4 - write_length))

            reserved = [0] * 1
            message = Message(
                block="EEPROM",
                block_command="Write",
                sender=self.sender,
                receiver=Node(node),
                request=True,
                data=[address, offset, write_length, *reserved, *write_data],
            )
            await self._request(
                message, description=f"write EEPROM data in “{node}”"
            )

            data = data[4:]
            offset += write_length

    # pylint: enable=too-many-arguments

    async def write_eeprom_float(
        self,
        address: int,
        offset: int,
        value: float,
        node: Union[str, Node] = "STU 1",
    ) -> None:
        """Write a float value at the specified EEPROM address

        Parameters
        ----------

        address:
            The page number in the EEPROM

        offset:
            The offset to the base address in the specified page

        value:
            The float value that should be stored at the specified location

        node:
            The node where the EEPROM data should be stored

        Example
        -------

        >>> from asyncio import run

        Write float value to and read (same) float value from EEPROM of STU 1

        >>> async def write_and_read_float(value):
        ...     async with Network() as network:
        ...         await network.write_eeprom_float(
        ...             address=10, offset=0, value=value, node='STU 1')
        ...         return await network.read_eeprom_float(
        ...             address=10, offset=0, node='STU 1')
        >>> value = 42.5
        >>> read_value = run(write_and_read_float(value))
        >>> value == read_value
        True

        """

        data = list(pack("f", value))
        await self.write_eeprom(address, offset, data, node=node)

    # pylint: disable=too-many-arguments

    async def write_eeprom_int(
        self,
        address: int,
        offset: int,
        value: int,
        length: int,
        signed: bool = False,
        node: Union[str, Node] = "STU 1",
    ) -> None:
        """Write an integer number at the specified EEPROM address

        Parameters
        ----------

        address:
            The page number in the EEPROM

        offset:
            The offset to the base address in the specified page

        value:
            The number that should be stored at the specified location

        length:
            This value specifies how long the number is in bytes

        signed:
            Specifies if `value` is a signed number (`True`) or an
            unsigned number (`False`)

        node:
            The node where the EEPROM data should be stored

        Example
        -------

        >>> from asyncio import run

        Write int value to and read (same) int value from EEPROM of STU 1

        >>> async def write_and_read_int(value):
        ...     async with Network() as network:
        ...         await network.write_eeprom_int(address=10, offset=0,
        ...                 value=value, length=8, signed=True, node='STU 1')
        ...         return await network.read_eeprom_int(address=10, offset=0,
        ...                 length=8, signed=True, node='STU 1')
        >>> value = -1337
        >>> read_value = run(write_and_read_int(value))
        >>> value == read_value
        True

        """

        data = list(value.to_bytes(length, byteorder="little", signed=signed))
        await self.write_eeprom(address, offset, data, node=node)

    # pylint: enable=too-many-arguments

    # pylint: disable=too-many-arguments

    async def write_eeprom_text(
        self,
        address: int,
        offset: int,
        text: str,
        length: int,
        node: Union[str, Node] = "STU 1",
    ) -> None:
        """Write a string at the specified EEPROM address

        Parameters
        ----------

        address:
            The page number in the EEPROM

        offset:
            The offset to the base address in the specified page

        text:
            An ASCII string that should be written to the specified location

        length:
            This optional parameter specifies how many of the character in
            `text` should be stored in the EEPROM. If you specify a length
            that is greater than the size of the data list, then the
            remainder of the EEPROM data will be filled with null bytes.

        node:
            The node where the EEPROM data should be stored

        Example
        -------

        >>> from asyncio import run

        Write text to and read (same) text from EEPROM of STU 1

        >>> async def write_and_read_text(text):
        ...     async with Network() as network:
        ...         await network.write_eeprom_text(address=10, offset=11,
        ...                 text=text, length=len(text), node='STU 1')
        ...         return await network.read_eeprom_text(
        ...             address=10, offset=11, length=len(text), node='STU 1')
        >>> run(write_and_read_text("something"))
        'something'

        """

        data = list(map(ord, list(text)))
        await self.write_eeprom(address, offset, data, length, node)

    # pylint: enable=too-many-arguments

    # ========================
    # = System Configuration =
    # ========================

    async def read_eeprom_status(
        self, node: Union[str, Node] = "STU 1"
    ) -> EEPROMStatus:
        """Retrieve EEPROM status byte

        Returns
        -------

        An EEPROM status object for the current status byte value

        Parameters
        ----------

        node:
            The node from which the EEPROM status byte should be retrieved

        Example
        -------

        >>> from asyncio import run

        Read the status byte of STU 1

        >>> async def read_status_byte():
        ...     async with Network() as network:
        ...         return await network.read_eeprom_status(node='STU 1')
        >>> isinstance(run(read_status_byte()), EEPROMStatus)
        True

        """

        return EEPROMStatus(
            (
                await self.read_eeprom(
                    address=0, offset=0, length=1, node=node
                )
            ).pop()
        )

    async def write_eeprom_status(
        self, value: Union[int, EEPROMStatus], node: Union[str, Node] = "STU 1"
    ) -> None:
        """Change the value of the EEPROM status byte

        Parameters
        ----------

        value:
            The new value for the status byte

        node:
            The node where the EEPROM status byte should be updated

        Example
        -------

        >>> from asyncio import run

        Write and read the status byte of STU 1

        >>> async def write_read_status_byte():
        ...     async with Network() as network:
        ...         await network.write_eeprom_status(
        ...             EEPROMStatus('Initialized'), node='STU 1')
        ...         return await network.read_eeprom_status(node='STU 1')
        >>> status = run(write_read_status_byte())
        >>> status.is_initialized()
        True

        """

        await self.write_eeprom_int(
            address=0,
            offset=0,
            length=1,
            value=EEPROMStatus(value).value,
            node=node,
        )

    async def read_eeprom_name(self, node: Union[str, Node] = "STU 1") -> str:
        """Retrieve the name of the node from the EEPROM

        Parameters
        ----------

        node:
            The node from which the name should be retrieved

        Returns
        -------

        The name of the node

        Example
        -------

        >>> from asyncio import run

        Read the name STU 1

        >>> async def read_name():
        ...     async with Network() as network:
        ...         return await network.read_eeprom_name(node='STU 1')
        >>> isinstance(run(read_name()), str)
        True

        """

        return await self.read_eeprom_text(
            address=0, offset=1, length=8, node=node
        )

    async def write_eeprom_name(
        self, name: str, node: Union[str, Node] = "STU 1"
    ) -> None:
        """Write the name of the node into the EEPROM

        Parameters
        ----------

        name:
            The new (Bluetooth advertisement) name of the node

        node:
            The node where the name should be updated

        Example
        -------

        >>> from asyncio import run

        Write and read the name of STU 1

        >>> async def write_read_name(name):
        ...     async with Network() as network:
        ...         await network.write_eeprom_name(name, node='STU 1')
        ...         return await network.read_eeprom_name(node='STU 1')
        >>> run(write_read_name('Valerie'))
        'Valerie'

        """

        await self.write_eeprom_text(
            address=0, offset=1, text=name, length=8, node=node
        )

    async def read_eeprom_sleep_time_1(self) -> int:
        """Retrieve sleep time 1 from the EEPROM

        Returns
        -------

        The current value of sleep time 1 in milliseconds

        Example
        -------

        >>> from asyncio import run

        Read sleep time 1 of STH 1

        >>> async def read_sleep_time_1():
        ...     async with Network() as network:
        ...         await network.connect_sensor_device(0)
        ...         return await network.read_eeprom_sleep_time_1()
        >>> sleep_time = run(read_sleep_time_1())
        >>> isinstance(sleep_time, int)
        True

        """

        return await self.read_eeprom_int(
            address=0, offset=9, length=4, node="STH 1"
        )

    async def write_eeprom_sleep_time_1(self, milliseconds: int) -> None:
        """Write the value of sleep time 1 to the EEPROM

        Parameters
        ----------

        milliseconds:
            The value for sleep time 1 in milliseconds

        Example
        -------

        >>> from asyncio import run

        Write and read sleep time 1 of STH 1

        >>> async def write_read_sleep_time_1(milliseconds):
        ...     async with Network() as network:
        ...         await network.connect_sensor_device(0)
        ...         await network.write_eeprom_sleep_time_1(milliseconds)
        ...         return await network.read_eeprom_sleep_time_1()
        >>> run(write_read_sleep_time_1(300_000))
        300000

        """

        await self.write_eeprom_int(
            address=0, offset=9, value=milliseconds, length=4, node="STH 1"
        )

    async def read_eeprom_advertisement_time_1(self) -> float:
        """Retrieve advertisement time 1 from the EEPROM

        Returns
        -------

        The current value of advertisement time 1 in milliseconds

        Example
        -------

        >>> from asyncio import run
        >>> from platform import system

        Read advertisement time 1 of STH 1

        >>> if system() == 'Linux':
        ...    async def reset():
        ...        async with Network() as network:
        ...            await network.reset_node('STU 1')
        ...    run(reset())
        >>> async def read_advertisement_time_1():
        ...     async with Network() as network:
        ...         await network.connect_sensor_device(0)
        ...         return await network.read_eeprom_advertisement_time_1()
        >>> advertisement_time = run(read_advertisement_time_1())
        >>> isinstance(advertisement_time, float)
        True
        >>> advertisement_time > 0
        True

        """

        advertisement_time_eeprom = await self.read_eeprom_int(
            address=0, offset=13, length=2, node="STH 1"
        )
        return (
            advertisement_time_eeprom
            * type(self).ADVERTISEMENT_TIME_EEPROM_TO_MS
        )

    async def write_eeprom_advertisement_time_1(self, milliseconds: int):
        """Write the value of advertisement time 1 to the EEPROM

        Parameters
        ----------

        milliseconds:
            The value for advertisement time 1 in milliseconds

        Example
        -------

        >>> from asyncio import run
        >>> from platform import system

        Write and read advertisement time 1 of STH 1

        >>> if system() == 'Linux':
        ...    async def reset():
        ...        async with Network() as network:
        ...            await network.reset_node('STU 1')
        ...    run(reset())
        >>> async def write_read_advertisement_time_1(milliseconds):
        ...     async with Network() as network:
        ...         await network.connect_sensor_device(0)
        ...         await network.write_eeprom_advertisement_time_1(
        ...                 milliseconds)
        ...         return await network.read_eeprom_advertisement_time_1()
        >>> run(write_read_advertisement_time_1(1250))
        1250.0

        """

        advertisement_time_eeprom = round(
            milliseconds / type(self).ADVERTISEMENT_TIME_EEPROM_TO_MS
        )

        await self.write_eeprom_int(
            address=0,
            offset=13,
            value=advertisement_time_eeprom,
            length=2,
            node="STH 1",
        )

    async def read_eeprom_sleep_time_2(self) -> int:
        """Retrieve sleep time 2 from the EEPROM

        Returns
        -------

        The current value of sleep time 2 in milliseconds

        Example
        -------

        >>> from asyncio import run
        >>> from platform import system

        Read sleep time 2 of STH 1

        >>> if system() == 'Linux':
        ...    async def reset():
        ...        async with Network() as network:
        ...            await network.reset_node('STU 1')
        ...    run(reset())
        >>> async def read_sleep_time_2():
        ...     async with Network() as network:
        ...         await network.connect_sensor_device(0)
        ...         return await network.read_eeprom_sleep_time_2()
        >>> sleep_time = run(read_sleep_time_2())
        >>> isinstance(sleep_time, int)
        True

        """

        return await self.read_eeprom_int(
            address=0, offset=15, length=4, node="STH 1"
        )

    async def write_eeprom_sleep_time_2(self, milliseconds: int) -> None:
        """Write the value of sleep time 2 to the EEPROM

        Parameters
        ----------

        milliseconds:
            The value for sleep time 2 in milliseconds

        Example
        -------

        >>> from asyncio import run

        Write and read sleep time 2 of STH 1

        >>> async def write_read_sleep_time_2(milliseconds):
        ...     async with Network() as network:
        ...         await network.connect_sensor_device(0)
        ...         await network.write_eeprom_sleep_time_2(milliseconds)
        ...         return await network.read_eeprom_sleep_time_2()
        >>> run(write_read_sleep_time_2(259_200_000))
        259200000

        """

        await self.write_eeprom_int(
            address=0, offset=15, value=milliseconds, length=4, node="STH 1"
        )

    async def read_eeprom_advertisement_time_2(self) -> float:
        """Retrieve advertisement time 2 from the EEPROM

        Returns
        -------

        The current value of advertisement time 2 in milliseconds

        Example
        -------

        >>> from asyncio import run
        >>> from platform import system

        Read advertisement time 2 of STH 1

        >>> if system() == 'Linux':
        ...    async def reset():
        ...        async with Network() as network:
        ...            await network.reset_node('STU 1')
        ...    run(reset())
        >>> async def read_advertisement_time_2():
        ...     async with Network() as network:
        ...         await network.connect_sensor_device(0)
        ...         return await network.read_eeprom_advertisement_time_2()
        >>> advertisement_time = run(read_advertisement_time_2())
        >>> isinstance(advertisement_time, float)
        True

        """

        advertisement_time_eeprom = await self.read_eeprom_int(
            address=0, offset=19, length=2, node="STH 1"
        )

        return (
            advertisement_time_eeprom
            * type(self).ADVERTISEMENT_TIME_EEPROM_TO_MS
        )

    async def write_eeprom_advertisement_time_2(self, milliseconds: int):
        """Write the value of advertisement time 2 to the EEPROM

        Parameters
        ----------

        milliseconds:
            The value for advertisement time 2 in milliseconds

        Example
        -------

        >>> from asyncio import run

        Write and read advertisement time 2 of STH 1

        >>> async def write_read_advertisement_time_2(milliseconds):
        ...     async with Network() as network:
        ...         await network.connect_sensor_device(0)
        ...         await network.write_eeprom_advertisement_time_2(
        ...                 milliseconds)
        ...         return await network.read_eeprom_advertisement_time_2()
        >>> run(write_read_advertisement_time_2(2500))
        2500.0

        """

        advertisement_time_eeprom = round(
            milliseconds / type(self).ADVERTISEMENT_TIME_EEPROM_TO_MS
        )

        await self.write_eeprom_int(
            address=0,
            offset=19,
            value=advertisement_time_eeprom,
            length=2,
            node="STH 1",
        )

    # ================
    # = Product Data =
    # ================

    async def read_eeprom_gtin(self, node: Union[str, Node] = "STU 1") -> int:
        """Read the global trade identifier number (GTIN) from the EEPROM

        Parameters
        ----------

        node:
            The node for which you want to retrieve the GTIN

        Returns
        -------

        The GTIN of the specified node

        Example
        -------

        >>> from asyncio import run

        Read the GTIN of STU 1

        >>> async def read_gtin():
        ...     async with Network() as network:
        ...         return await network.read_eeprom_gtin('STU 1')
        >>> gtin = run(read_gtin())
        >>> isinstance(gtin, int)
        True

        """

        return await self.read_eeprom_int(
            address=4, offset=0, length=8, node=node
        )

    async def write_eeprom_gtin(
        self, gtin: int, node: Union[str, Node] = "STU 1"
    ) -> None:
        """Write the global trade identifier number (GTIN) to the EEPROM

        Parameters
        ----------

        gtin:
            The new GTIN of the specified receiver

        node:
            The node where you want to change the GTIN

        Example
        -------

        >>> from asyncio import run

        Write and read the GTIN of STU 1

        >>> async def write_read_gtin(gtin):
        ...     async with Network() as network:
        ...         await network.write_eeprom_gtin(gtin=gtin, node='STU 1')
        ...         return await network.read_eeprom_gtin(node='STU 1')
        >>> run(write_read_gtin(0))
        0

        """

        await self.write_eeprom_int(
            address=4, offset=0, length=8, value=gtin, node=node
        )

    async def read_eeprom_hardware_version(
        self, node: Union[str, Node] = "STU 1"
    ) -> Version:
        """Read the current hardware version from the EEPROM

        Parameters
        ----------

        node:
            The node from which you want to retrieve the hardware version

        Returns
        -------

        The hardware version of the specified node

        Example
        -------

        >>> from asyncio import run

        Read the hardware version of STU 1

        >>> async def read_hardware_version():
        ...     async with Network() as network:
        ...         return (await
        ...                 network.read_eeprom_hardware_version(node='STU 1'))
        >>> hardware_version = run(read_hardware_version())
        >>> hardware_version.major >= 1
        True

        """

        major, minor, patch = await self.read_eeprom(
            address=4, offset=13, length=3, node=node
        )
        return Version(major=major, minor=minor, patch=patch)

    async def write_eeprom_hardware_version(
        self, version: Union[str, Version], node: Union[str, Node] = "STU 1"
    ):
        """Write hardware version to the EEPROM

        Parameters
        ----------

        version:
            The new hardware version of the specified receiver

        node:
            The node where you want to change the hardware version

        Example
        -------

        >>> from asyncio import run

        Write and read the hardware version of STU 1

        >>> async def write_read_hardware_version(version):
        ...     async with Network() as network:
        ...         await network.write_eeprom_hardware_version(
        ...                 version=version, node='STU 1')
        ...         return (await
        ...                 network.read_eeprom_hardware_version(node='STU 1'))
        >>> hardware_version = run(write_read_hardware_version('1.3.2'))
        >>> hardware_version.patch == 2
        True

        """

        if isinstance(version, str):
            version = Version(version)

        await self.write_eeprom(
            address=4,
            offset=13,
            length=3,
            data=[version.major, version.minor, version.patch],
            node=node,
        )

    async def read_eeprom_firmware_version(
        self, node: Union[str, Node] = "STU 1"
    ) -> Version:
        """Retrieve the current firmware version from the EEPROM

        Parameters
        ----------

        node:
            The node from which you want to retrieve the firmware version

        Returns
        -------

        The firmware version of the specified node

        Example
        -------

        >>> from asyncio import run

        Read the firmware version of STU 1

        >>> async def read_firmware_version():
        ...     async with Network() as network:
        ...         return (await
        ...                 network.read_eeprom_firmware_version(node='STU 1'))
        >>> firmware_version = run(read_firmware_version())
        >>> firmware_version.major >= 2
        True

        """

        major, minor, patch = await self.read_eeprom(
            address=4, offset=21, length=3, node=node
        )
        return Version(major=major, minor=minor, patch=patch)

    async def write_eeprom_firmware_version(
        self, version: Union[str, Version], node: Union[str, Node] = "STU 1"
    ) -> None:
        """Write firmware version to the EEPROM

        Parameters
        ----------

        version:
            The new firmware version

        node:
            The node where you want to change the firmware version

        Example
        -------

        >>> from asyncio import run

        Write and read the firmware version of STU 1

        >>> async def write_read_firmware_version(version):
        ...     async with Network() as network:
        ...         await network.write_eeprom_firmware_version(
        ...                 version=version, node='STU 1')
        ...         return (await
        ...                 network.read_eeprom_firmware_version(node='STU 1'))
        >>> version = '2.1.10'
        >>> firmware_version = run(write_read_firmware_version(version))
        >>> firmware_version == Version(version)
        True

        """

        if isinstance(version, str):
            version = Version(version)

        await self.write_eeprom(
            address=4,
            offset=21,
            length=3,
            data=[version.major, version.minor, version.patch],
            node=node,
        )

    async def read_eeprom_release_name(
        self, node: Union[str, Node] = "STU 1"
    ) -> str:
        """Retrieve the current release name from the EEPROM

        Parameters
        ----------

        node:
            The node from which you want to retrieve the release name

        Returns
        -------

        The firmware release name of the specified node

        Example
        -------

        >>> from asyncio import run

        Read the release name of STU 1

        >>> async def read_release_name():
        ...     async with Network() as network:
        ...         return await network.read_eeprom_release_name(node='STU 1')
        >>> run(read_release_name())
        'Valerie'

        """

        return await self.read_eeprom_text(
            address=4, offset=24, length=8, node=node
        )

    async def write_eeprom_release_name(
        self, name: str, node: Union[str, Node] = "STU 1"
    ):
        """Write the release name to the EEPROM

        Parameters
        ----------

        name:
            The new name of the release

        node:
            The node where you want to change the release name

        Example
        -------

        >>> from asyncio import run

        Write and read the release name of STU 1

        >>> async def write_read_release_name(name):
        ...     async with Network() as network:
        ...         await network.write_eeprom_release_name(name=name,
        ...                                                 node='STU 1')
        ...         return (await
        ...                 network.read_eeprom_release_name(node='STU 1'))
        >>> run(write_read_release_name('Valerie'))
        'Valerie'

        """

        await self.write_eeprom_text(
            address=4, offset=24, length=8, text=name, node=node
        )

    async def read_eeprom_serial_number(
        self, node: Union[str, Node] = "STU 1"
    ) -> str:
        """Retrieve the serial number from the EEPROM

        Parameters
        ----------

        node:
            The node from which you want to retrieve the serial number

        Returns
        -------

        The serial number of the specified node

        Example
        -------

        >>> from asyncio import run

        Read the serial number of STU 1

        >>> async def read_serial_number():
        ...     async with Network() as network:
        ...         return await network.read_eeprom_serial_number(
        ...                 node='STU 1')
        >>> serial_number = run(read_serial_number())
        >>> isinstance(serial_number, str)
        True

        """

        return await self.read_eeprom_text(
            address=4, offset=32, length=32, node=node
        )

    async def write_eeprom_serial_number(
        self, serial_number: str, node: Union[str, Node] = "STU 1"
    ):
        """Write the serial number to the EEPROM

        Parameters
        ----------

        serial_number:
            The serial number of the specified receiver

        node:
            The node where you want to change the release name

        Example
        -------

        >>> from asyncio import run

        Write and read the serial number of STU 1

        >>> async def write_read_serial_number(serial):
        ...     async with Network() as network:
        ...         await network.write_eeprom_serial_number(serial,
        ...                                                  node='STU 1')
        ...         return (await
        ...                 network.read_eeprom_serial_number(node='STU 1'))
        >>> run(write_read_serial_number('0'))
        '0'

        """

        await self.write_eeprom_text(
            address=4, offset=32, length=32, text=serial_number, node=node
        )

    async def read_eeprom_product_name(
        self, node: Union[str, Node] = "STU 1"
    ) -> str:
        """Retrieve the product name from the EEPROM

        Parameters
        ----------

        node:
            The node from which you want to retrieve the product name

        Returns
        -------

        The product name of the specified node

        Example
        -------

        >>> from asyncio import run

        Read the product name of STU 1

        >>> async def read_product_name():
        ...     async with Network() as network:
        ...         return await network.read_eeprom_product_name(node='STU 1')
        >>> product_name = run(read_product_name())
        >>> isinstance(product_name, str)
        True

        """

        return await self.read_eeprom_text(
            address=4, offset=64, length=128, node=node
        )

    async def write_eeprom_product_name(
        self, name: str, node: Union[str, Node] = "STU 1"
    ):
        """Write the product name to the EEPROM

        Parameters
        ----------

        name:
            The new product name of the specified receiver

        node:
            The node where you want to change the product name

        Example
        -------

        >>> from asyncio import run

        Write and read the product name of STU 1

        >>> async def write_read_product_name(name):
        ...     async with Network() as network:
        ...         await network.write_eeprom_product_name(name, node='STU 1')
        ...         return await network.read_eeprom_product_name(node='STU 1')
        >>> run(write_read_product_name('0'))
        '0'

        """

        await self.write_eeprom_text(
            address=4, offset=64, length=128, text=name, node=node
        )

    async def read_eeprom_oem_data(
        self, node: Union[str, Node] = "STU 1"
    ) -> List[int]:
        """Retrieve the OEM data from the EEPROM

        Parameters
        ----------

        node:
            The node from which you want to retrieve the OEM data

        Returns
        -------

        The OEM data of the specified node

        Example
        -------

        >>> from asyncio import run

        Read the OEM data of STU 1

        >>> async def read_oem_data():
        ...     async with Network() as network:
        ...         return await network.read_eeprom_oem_data(node='STU 1')
        >>> oem_data = run(read_oem_data())
        >>> len(oem_data) == 64
        True

        """

        return await self.read_eeprom(
            address=4, offset=192, length=64, node=node
        )

    async def write_eeprom_oem_data(
        self, data: List[int], node: Union[str, Node] = "STU 1"
    ):
        """Write OEM data to the EEPROM

        Parameters
        ----------

        data:
            The OEM data that should be stored in the EEPROM

        node:
            The node where you want to store the OEM data

        Example
        -------

        >>> from asyncio import run

        Write and read the OEM data of STU 1

        >>> async def write_read_oem_data(data):
        ...     async with Network() as network:
        ...         await network.write_eeprom_oem_data(data, node='STU 1')
        ...         return await network.read_eeprom_oem_data(node='STU 1')
        >>> data = [0] * 64
        >>> run(write_read_oem_data(data)) == data
        True

        """

        await self.write_eeprom(
            address=4, offset=192, length=64, data=data, node=node
        )

    # ==============
    # = Statistics =
    # ==============

    async def read_eeprom_power_on_cycles(
        self, node: Union[str, Node] = "STU 1"
    ) -> int:
        """Retrieve the number of power on cycles from the EEPROM

        Parameters
        ----------

        node:
            The node from which you want to retrieve number of power on cycles

        Returns
        -------

        The number of power on cycles of the specified node

        Example
        -------

        >>> from asyncio import run

        Read the number of power on cycles of STU 1

        >>> async def read_power_on_cycles():
        ...     async with Network() as network:
        ...         return await network.read_eeprom_power_on_cycles('STU 1')
        >>> power_on_cycles = run(read_power_on_cycles())
        >>> power_on_cycles >= 0
        True

        """

        return await self.read_eeprom_int(
            address=5, offset=0, length=4, node=node
        )

    async def write_eeprom_power_on_cycles(
        self, times: int, node: Union[str, Node] = "STU 1"
    ):
        """Write the number of power on cycles to the EEPROM

        Parameters
        ----------

        times:
            The number of power on cycles that should be stored in the EEPROM

        node:
            The node where you want to change the number of power on cycles

        Example
        -------

        >>> from asyncio import run

        Write and read the number of power on cycles of STU 1

        >>> async def write_read_power_on_cycles(times):
        ...     async with Network() as network:
        ...         await network.write_eeprom_power_on_cycles(times, 'STU 1')
        ...         return await network.read_eeprom_power_on_cycles('STU 1')
        >>> run(write_read_power_on_cycles(0))
        0

        """

        await self.write_eeprom_int(
            address=5, offset=0, length=4, value=times, node=node
        )

    async def read_eeprom_power_off_cycles(
        self, node: Union[str, Node] = "STU 1"
    ) -> int:
        """Retrieve the number of power off cycles from the EEPROM

        Parameters
        ----------

        node:
            The node from which you want to retrieve number of power off cycles

        Returns
        -------

        The number of power off cycles of the specified node

        Example
        -------

        >>> from asyncio import run

        Read the number of power off cycles of STU 1

        >>> async def read_power_off_cycles():
        ...     async with Network() as network:
        ...         return await network.read_eeprom_power_off_cycles('STU 1')
        >>> power_off_cycles = run(read_power_off_cycles())
        >>> power_off_cycles >= 0
        True

        """

        return await self.read_eeprom_int(
            address=5, offset=4, length=4, node=node
        )

    async def write_eeprom_power_off_cycles(
        self, times: int, node: Union[str, Node] = "STU 1"
    ):
        """Write the number of power off cycles to the EEPROM

        Parameters
        ----------

        times:
            The number of power off cycles that should be stored in the EEPROM

        node:
            The node where you want to change the number of power off cycles

        Example
        -------

        >>> from asyncio import run

        Write and read the number of power off cycles of STU 1

        >>> async def write_read_power_off_cycles(times):
        ...     async with Network() as network:
        ...         await network.write_eeprom_power_off_cycles(times, 'STU 1')
        ...         return await network.read_eeprom_power_off_cycles('STU 1')
        >>> run(write_read_power_off_cycles(0))
        0

        """

        await self.write_eeprom_int(
            address=5, offset=4, length=4, value=times, node=node
        )

    async def read_eeprom_operating_time(
        self, node: Union[str, Node] = "STU 1"
    ) -> int:
        """Retrieve the operating time from the EEPROM

        Parameters
        ----------

        node:
            The node for which you want to retrieve the operating time

        Returns
        -------

        The operating time of the specified node in seconds

        Example
        -------

        >>> from asyncio import run

        Read the operating time of STU 1

        >>> async def read_operating_time():
        ...     async with Network() as network:
        ...         return await network.read_eeprom_operating_time('STU 1')
        >>> operating_time = run(read_operating_time())
        >>> operating_time >= 0
        True

        """

        return await self.read_eeprom_int(
            address=5, offset=8, length=4, node=node
        )

    async def write_eeprom_operating_time(
        self, seconds: int, node: Union[str, Node] = "STU 1"
    ):
        """Write operating time to the EEPROM

        Parameters
        ----------

        seconds:
            The operating time in seconds that should be stored in the EEPROM

        node:
            The node for which you want to change the operating time

        Example
        -------

        >>> from asyncio import run

        Write and read the operating time of STU 1

        >>> async def write_read_operating_time(seconds):
        ...     async with Network() as network:
        ...         await network.write_eeprom_operating_time(seconds, 'STU 1')
        ...         return await network.read_eeprom_operating_time('STU 1')
        >>> operating_time = run(write_read_operating_time(10))
        >>> 10 <= operating_time <= 11
        True

        """

        await self.write_eeprom_int(
            address=5, offset=8, length=4, value=seconds, node=node
        )

    async def read_eeprom_under_voltage_counter(
        self, node: Union[str, Node] = "STU 1"
    ) -> int:
        """Retrieve the under voltage counter value from the EEPROM

        Parameters
        ----------

        node:
            The node for which you want to retrieve the under voltage counter

        Returns
        -------

        The number of times the voltage was too low for the specified node

        Example
        -------

        >>> from asyncio import run

        Read the under voltage counter of STU 1

        >>> async def read_under_voltage_counter():
        ...     async with Network() as network:
        ...         return await network.read_eeprom_under_voltage_counter(
        ...             node='STU 1')
        >>> under_voltage_counter = run(read_under_voltage_counter())
        >>> under_voltage_counter >= 0
        True

        """

        return await self.read_eeprom_int(
            address=5, offset=12, length=4, node=node
        )

    async def write_eeprom_under_voltage_counter(
        self, times: int, node: Union[str, Node] = "STU 1"
    ):
        """Write the under voltage counter value to the EEPROM

        Parameters
        ----------

        times:
            The number of times the voltage was too low

        node:
            The node for which you want to change the under voltage counter

        Example
        -------

        >>> from asyncio import run

        Write and read the under voltage counter of STU 1

        >>> async def write_read_under_voltage_counter(times):
        ...     async with Network() as network:
        ...         await network.write_eeprom_under_voltage_counter(
        ...                 times=times, node='STU 1')
        ...         return await network.read_eeprom_under_voltage_counter(
        ...                 node='STU 1')
        >>> run(write_read_under_voltage_counter(0))
        0

        """

        await self.write_eeprom_int(
            address=5, offset=12, length=4, value=times, node=node
        )

    async def read_eeprom_watchdog_reset_counter(
        self, node: Union[str, Node] = "STU 1"
    ) -> int:
        """Retrieve the watchdog reset counter value from the EEPROM

        Parameters
        ----------

        node:
            The node for which you want to retrieve the watchdog reset counter

        Returns
        -------

        The watchdog reset counter value of the specified node

        Example
        -------

        >>> from asyncio import run

        Read the watchdog reset counter of STU 1

        >>> async def read_watchdog_reset_counter():
        ...     async with Network() as network:
        ...         return await network.read_eeprom_watchdog_reset_counter(
        ...             node='STU 1')
        >>> watchdog_reset_counter = run(read_watchdog_reset_counter())
        >>> watchdog_reset_counter >= 0
        True

        """

        return await self.read_eeprom_int(
            address=5, offset=16, length=4, node=node
        )

    async def write_eeprom_watchdog_reset_counter(
        self, times: int, node: Union[str, Node] = "STU 1"
    ) -> None:
        """Write the watchdog reset counter value to the EEPROM

        Parameters
        ----------

        times:
            The value of the watchdog reset counter for the specified node

        node:
            The node for which you want to change the watchdog reset counter

        Example
        -------

        >>> from asyncio import run

        Write and read the watchdog reset counter of STU 1

        >>> async def write_read_watchdog_reset_counter(times):
        ...     async with Network() as network:
        ...         await network.write_eeprom_watchdog_reset_counter(
        ...                 times=times, node='STU 1')
        ...         return await network.read_eeprom_watchdog_reset_counter(
        ...                 node='STU 1')
        >>> run(write_read_watchdog_reset_counter(0))
        0

        """

        await self.write_eeprom_int(
            address=5, offset=16, length=4, value=times, node=node
        )

    async def read_eeprom_production_date(
        self, node: Union[str, Node] = "STU 1"
    ) -> date:
        """Retrieve the production date from the EEPROM

        Parameters
        ----------

        node:
            The node for which you want to read the production date

        Returns
        -------

        The production date of the specified node

        Example
        -------

        >>> from asyncio import run

        Read the production date of STU 1

        >>> async def read_production_date():
        ...     async with Network() as network:
        ...         return await network.read_eeprom_production_date('STU 1')
        >>> production_date = run(read_production_date())
        >>> isinstance(production_date, date)
        True

        """

        date_values = await self.read_eeprom_text(
            address=5, offset=20, length=8, node=node
        )
        return date(
            year=int(date_values[0:4]),
            month=int(date_values[4:6]),
            day=int(date_values[6:8]),
        )

    # pylint: disable=redefined-outer-name

    async def write_eeprom_production_date(
        self, date: Union[date, str], node: Union[str, Node] = "STU 1"
    ) -> None:
        """Write the production date to the EEPROM

        Parameters
        ----------

        date:
            The production date of the specified node

        node:
            The node for which you want to change the production date

        Example
        -------

        >>> from asyncio import run

        Write and read the production date of STU 1

        >>> async def write_read_production_date(date):
        ...     async with Network() as network:
        ...         await network.write_eeprom_production_date(
        ...                 date=date, node='STU 1')
        ...         return await network.read_eeprom_production_date(
        ...                 node='STU 1')

        >>> production_date = date(year=2020, month=10, day=5)
        >>> str(run(write_read_production_date(production_date)))
        '2020-10-05'

        >>> production_date = '2000-01-05'
        >>> str(run(write_read_production_date(production_date)))
        '2000-01-05'

        """

        if isinstance(date, str):
            # The identifier `date` refers to the variable `date` in the
            # current scope
            import datetime  # pylint: disable=import-outside-toplevel

            try:
                date = datetime.date.fromisoformat(date)
            except ValueError as error:
                raise ValueError(
                    f"Invalid value for date argument: “{date}”"
                ) from error

        await self.write_eeprom_text(
            address=5,
            offset=20,
            length=8,
            text=str(date).replace("-", ""),
            node=node,
        )

    # pylint: enable=redefined-outer-name

    async def read_eeprom_batch_number(
        self, node: Union[str, Node] = "STU 1"
    ) -> int:
        """Retrieve the batch number from the EEPROM

        Parameters
        ----------

        node:
            The node for which you want to read the batch number

        Returns
        -------

        The batch number of the specified node

        Example
        -------

        >>> from asyncio import run

        Read the batch number of STU 1

        >>> async def read_batch_number():
        ...     async with Network() as network:
        ...         return await network.read_eeprom_batch_number('STU 1')
        >>> batch_number = run(read_batch_number())
        >>> isinstance(batch_number, int)
        True

        """

        return await self.read_eeprom_int(
            address=5, offset=28, length=4, node=node
        )

    async def write_eeprom_batch_number(
        self, number: int, node: Union[str, Node] = "STU 1"
    ) -> None:
        """Write the batch number to the EEPROM

        Parameters
        ----------

        number:
            The batch number of the specified node

        node:
            The node for which you want to change the batch number

        Example
        -------

        >>> from asyncio import run

        Write and read the batch number of STU 1

        >>> async def write_read_batch_number(number):
        ...     async with Network() as network:
        ...         await network.write_eeprom_batch_number(number, 'STU 1')
        ...         return await network.read_eeprom_batch_number('STU 1')
        >>> run(write_read_batch_number(1337))
        1337

        """

        await self.write_eeprom_int(
            address=5, offset=28, length=4, value=number, node=node
        )

    # ===============
    # = Calibration =
    # ===============

    async def read_eeprom_x_axis_acceleration_slope(self) -> float:
        """Retrieve the acceleration slope of the x-axis from the EEPROM

        Returns
        -------

        The x-axis acceleration slope of STH 1

        Example
        -------

        >>> from asyncio import run
        >>> from platform import system

        Read the acceleration slope of STH 1

        >>> if system() == 'Linux':
        ...    async def reset():
        ...        async with Network() as network:
        ...            await network.reset_node('STU 1')
        ...    run(reset())
        >>> async def read_x_axis_acceleration_slope():
        ...     async with Network() as network:
        ...         await network.connect_sensor_device(0)
        ...         return (await
        ...                 network.read_eeprom_x_axis_acceleration_slope())
        >>> x_axis_acceleration_slope = run(read_x_axis_acceleration_slope())
        >>> isinstance(x_axis_acceleration_slope, float)
        True

        """

        return await self.read_eeprom_float(address=8, offset=0, node="STH 1")

    async def write_eeprom_x_axis_acceleration_slope(
        self, slope: float
    ) -> None:
        """Write the acceleration slope of the x-axis to the EEPROM

        Parameters
        ----------

        slope:
            The addition to the acceleration value for one step of the ADC in
            multiples of g₀

        Example
        -------

        >>> from asyncio import run
        >>> from math import isclose

        Write and read the acceleration slope of STH 1

        >>> async def write_read_x_axis_acceleration_slope(slope):
        ...     async with Network() as network:
        ...         await network.connect_sensor_device(0)
        ...         await network.write_eeprom_x_axis_acceleration_slope(slope)
        ...         return (await
        ...                 network.read_eeprom_x_axis_acceleration_slope())
        >>> adc_max = 0xffff
        >>> acceleration_difference_max = 200
        >>> slope = acceleration_difference_max / adc_max
        >>> slope_read = run(write_read_x_axis_acceleration_slope(slope))
        >>> isclose(slope, slope_read)
        True

        """

        await self.write_eeprom_float(
            address=8, offset=0, value=slope, node="STH 1"
        )

    async def read_eeprom_x_axis_acceleration_offset(self) -> float:
        """Retrieve the acceleration offset of the x-axis from the EEPROM

        Returns
        -------

        The acceleration offset of the x-axis of STH 1

        Example
        -------

        >>> from asyncio import run
        >>> from platform import system

        Read the acceleration offset of STH 1

        >>> if system() == 'Linux':
        ...    async def reset():
        ...        async with Network() as network:
        ...            await network.reset_node('STU 1')
        ...    run(reset())
        >>> async def read_x_axis_acceleration_offset():
        ...     async with Network() as network:
        ...         await network.connect_sensor_device(0)
        ...         return (await
        ...                 network.read_eeprom_x_axis_acceleration_offset())
        >>> x_axis_acceleration_offset = run(read_x_axis_acceleration_offset())
        >>> isinstance(x_axis_acceleration_offset, float)
        True

        """

        return await self.read_eeprom_float(address=8, offset=4, node="STH 1")

    async def write_eeprom_x_axis_acceleration_offset(
        self, offset: int
    ) -> None:
        """Write the acceleration offset of the x-axis to the EEPROM

        Parameters
        ----------

        offset:
            The (negative) offset of the acceleration value in multiples of g₀

        Example
        -------

        >>> from asyncio import run
        >>> from math import isclose
        >>> from platform import system

        Write and read the acceleration offset of STH 1

        >>> if system() == 'Linux':
        ...    async def reset():
        ...        async with Network() as network:
        ...            await network.reset_node('STU 1')
        ...    run(reset())
        >>> async def write_read_x_axis_acceleration_offset(offset):
        ...     async with Network() as network:
        ...         await network.connect_sensor_device(0)
        ...         await network.write_eeprom_x_axis_acceleration_offset(
        ...                 offset)
        ...         return (await
        ...                 network.read_eeprom_x_axis_acceleration_offset())
        >>> acceleration_difference_max = 200
        >>> offset = -(acceleration_difference_max/2)
        >>> offset_read = run(write_read_x_axis_acceleration_offset(offset))
        >>> isclose(offset, offset_read)
        True

        """

        await self.write_eeprom_float(
            address=8, offset=4, value=offset, node="STH 1"
        )

    async def read_eeprom_y_axis_acceleration_slope(self) -> float:
        """Retrieve the acceleration slope of the y-axis from the EEPROM

        Returns
        -------

        The y-axis acceleration slope of STH 1

        Example
        -------

        >>> from asyncio import run
        >>> from platform import system

        Read the acceleration slope in the y direction of STH 1

        >>> if system() == 'Linux':
        ...    async def reset():
        ...        async with Network() as network:
        ...            await network.reset_node('STU 1')
        ...    run(reset())
        >>> async def read_y_axis_acceleration_slope():
        ...     async with Network() as network:
        ...         await network.connect_sensor_device(0)
        ...         return (await
        ...                 network.read_eeprom_y_axis_acceleration_slope())
        >>> y_axis_acceleration_slope = run(read_y_axis_acceleration_slope())
        >>> isinstance(y_axis_acceleration_slope, float)
        True

        """

        return await self.read_eeprom_float(address=8, offset=8, node="STH 1")

    async def write_eeprom_y_axis_acceleration_slope(
        self, slope: float
    ) -> None:
        """Write the acceleration slope of the y-axis to the EEPROM

        Parameters
        ----------

        slope:
            The addition to the acceleration value for one step of the ADC in
            multiples of g₀

        Example
        -------

        >>> from asyncio import run
        >>> from math import isclose
        >>> from platform import system

        Write and read the acceleration slope of STH 1

        >>> if system() == 'Linux':
        ...    async def reset():
        ...        async with Network() as network:
        ...            await network.reset_node('STU 1')
        ...    run(reset())
        >>> async def write_read_y_axis_acceleration_slope(slope):
        ...     async with Network() as network:
        ...         await network.connect_sensor_device(0)
        ...         await network.write_eeprom_y_axis_acceleration_slope(slope)
        ...         return (await
        ...                 network.read_eeprom_y_axis_acceleration_slope())
        >>> adc_max = 0xffff
        >>> acceleration_difference_max = 200
        >>> slope = acceleration_difference_max / adc_max
        >>> slope_read = run(write_read_y_axis_acceleration_slope(slope))
        >>> isclose(slope, slope_read)
        True

        """

        await self.write_eeprom_float(
            address=8, offset=8, value=slope, node="STH 1"
        )

    async def read_eeprom_y_axis_acceleration_offset(self) -> float:
        """Retrieve the acceleration offset of the y-axis from the EEPROM

        Returns
        -------

        The acceleration offset of the y-axis of STH 1

        Example
        -------

        >>> from asyncio import run

        Read the acceleration offset of STH 1

        >>> async def read_y_axis_acceleration_offset():
        ...     async with Network() as network:
        ...         await network.connect_sensor_device(0)
        ...         return (await
        ...                 network.read_eeprom_y_axis_acceleration_offset())
        >>> y_axis_acceleration_offset = run(read_y_axis_acceleration_offset())
        >>> isinstance(y_axis_acceleration_offset, float)
        True

        """

        return await self.read_eeprom_float(address=8, offset=12, node="STH 1")

    async def write_eeprom_y_axis_acceleration_offset(
        self, offset: int
    ) -> None:
        """Write the acceleration offset of the y-axis to the EEPROM

        Parameters
        ----------

        offset:
            The (negative) offset of the acceleration value in multiples of g₀

        Example
        -------

        >>> from asyncio import run
        >>> from math import isclose
        >>> from platform import system

        Write and read the acceleration offset of STH 1

        >>> if system() == 'Linux':
        ...    async def reset():
        ...        async with Network() as network:
        ...            await network.reset_node('STU 1')
        ...    run(reset())
        >>> async def write_read_y_axis_acceleration_offset(offset):
        ...     async with Network() as network:
        ...         await network.connect_sensor_device(0)
        ...         await network.write_eeprom_y_axis_acceleration_offset(
        ...                 offset)
        ...         return (await
        ...                 network.read_eeprom_y_axis_acceleration_offset())
        >>> acceleration_difference_max = 200
        >>> offset = -(acceleration_difference_max/2)
        >>> offset_read = run(write_read_y_axis_acceleration_offset(offset))
        >>> isclose(offset, offset_read)
        True

        """

        await self.write_eeprom_float(
            address=8, offset=12, value=offset, node="STH 1"
        )

    async def read_eeprom_z_axis_acceleration_slope(self) -> float:
        """Retrieve the acceleration slope of the z-axis from the EEPROM

        Returns
        -------

        The z-axis acceleration slope of STH 1

        Example
        -------

        >>> from asyncio import run
        >>> from platform import system

        Read the acceleration slope in the z direction of STH 1

        >>> if system() == 'Linux':
        ...    async def reset():
        ...        async with Network() as network:
        ...            await network.reset_node('STU 1')
        ...    run(reset())
        >>> async def read_z_axis_acceleration_slope():
        ...     async with Network() as network:
        ...         await network.connect_sensor_device(0)
        ...         return (await
        ...                 network.read_eeprom_z_axis_acceleration_slope())
        >>> z_axis_acceleration_slope = run(read_z_axis_acceleration_slope())
        >>> isinstance(z_axis_acceleration_slope, float)
        True

        """

        return await self.read_eeprom_float(address=8, offset=16, node="STH 1")

    async def write_eeprom_z_axis_acceleration_slope(
        self, slope: float
    ) -> None:
        """Write the acceleration slope of the z-axis to the EEPROM

        Parameters
        ----------

        slope:
            The addition to the acceleration value for one step of the ADC in
            multiples of g₀

        Example
        -------

        >>> from asyncio import run
        >>> from math import isclose
        >>> from platform import system

        Write and read the acceleration slope of STH 1

        >>> if system() == 'Linux':
        ...    async def reset():
        ...        async with Network() as network:
        ...            await network.reset_node('STU 1')
        ...    run(reset())
        >>> async def write_read_z_axis_acceleration_slope(slope):
        ...     async with Network() as network:
        ...         await network.connect_sensor_device(0)
        ...         await network.write_eeprom_z_axis_acceleration_slope(slope)
        ...         return (await
        ...                 network.read_eeprom_z_axis_acceleration_slope())
        >>> adc_max = 0xffff
        >>> acceleration_difference_max = 200
        >>> slope = acceleration_difference_max / adc_max
        >>> slope_read = run(write_read_z_axis_acceleration_slope(slope))
        >>> isclose(slope, slope_read)
        True

        """

        await self.write_eeprom_float(
            address=8, offset=16, value=slope, node="STH 1"
        )

    async def read_eeprom_z_axis_acceleration_offset(self) -> float:
        """Retrieve the acceleration offset of the z-axis from the EEPROM

        Returns
        -------

        The acceleration offset of the z-axis of STH 1

        Example
        -------

        >>> from asyncio import run

        Read the acceleration offset of STH 1

        >>> async def read_z_axis_acceleration_offset():
        ...     async with Network() as network:
        ...         await network.connect_sensor_device(0)
        ...         return (await
        ...                 network.read_eeprom_z_axis_acceleration_offset())
        >>> z_axis_acceleration_offset = run(read_z_axis_acceleration_offset())
        >>> isinstance(z_axis_acceleration_offset, float)
        True

        """

        return await self.read_eeprom_float(address=8, offset=20, node="STH 1")

    async def write_eeprom_z_axis_acceleration_offset(
        self, offset: int
    ) -> None:
        """Write the acceleration offset of the z-axis to the EEPROM

        Parameters
        ----------

        offset:
            The (negative) offset of the acceleration value in multiples of g₀

        Example
        -------

        >>> from asyncio import run
        >>> from math import isclose

        Write and read the acceleration offset of STH 1

        >>> async def write_read_z_axis_acceleration_offset(offset):
        ...     async with Network() as network:
        ...         await network.connect_sensor_device(0)
        ...         await network.write_eeprom_z_axis_acceleration_offset(
        ...                 offset)
        ...         return (await
        ...                 network.read_eeprom_z_axis_acceleration_offset())
        >>> acceleration_difference_max = 200
        >>> offset = -(acceleration_difference_max/2)
        >>> offset_read = run(write_read_z_axis_acceleration_offset(offset))
        >>> isclose(offset, offset_read)
        True

        """

        await self.write_eeprom_float(
            address=8, offset=20, value=offset, node="STH 1"
        )

    async def read_acceleration_sensor_range_in_g(self) -> int:
        """Retrieve the maximum acceleration sensor range in multiples of g₀

        - For a ±100 g₀ sensor this method returns 200 (100 + |-100|).
        - For a ±50 g₀ sensor this method returns 100 (50 + |-50|).

        For this to work correctly:

        - STH 1 has to be connected via Bluetooth to the STU and
        - the EEPROM value of the [x-axis acceleration offset][offset] has to
          be set.

        [offset]: https://mytoolit.github.io/Documentation/\
        #value:acceleration-x-offset

        Returns
        -------

        Range of current acceleration sensor in multiples of earth’s
        gravitation

        """

        return round(
            abs(await self.read_eeprom_x_axis_acceleration_offset()) * 2
        )

    # ================
    # = Product Data =
    # ================

    async def get_gtin(self, node: Union[str, Node]) -> int:
        """Retrieve the GTIN (Global Trade Identification Number) of a node

        Parameters
        ----------

        node:
            The node which should return its GTIN

        Returns
        -------

        The Global Trade Identification Number of the specified node

        Example
        -------

        >>> from asyncio import run

        Read the GTIN of STU 1

        >>> async def read_gtin():
        ...     async with Network() as network:
        ...         return await network.get_gtin('STU 1')
        >>> gtin = run(read_gtin())
        >>> isinstance(gtin, int)
        True

        """

        response = await self._request_product_data(
            node=node,
            description=f"read GTIN of node “{node}”",
            block_command="GTIN",
        )

        return int.from_bytes(response.data, byteorder="little")

    async def get_hardware_version(self, node: Union[str, Node]) -> Version:
        """Retrieve the hardware version of a node

        Parameters
        ----------

        node:
            The node which should return its hardware version

        Returns
        -------

        The hardware version of the specified node

        Example
        -------

        >>> from asyncio import run

        Read the hardware version of STU 1

        >>> async def read_hardware_version():
        ...     async with Network() as network:
        ...         return await network.get_hardware_version('STU 1')
        >>> hardware_version = run(read_hardware_version())
        >>> hardware_version.major
        1

        """

        response = await self._request_product_data(
            node=node,
            description=f"read hardware version of node “{node}”",
            block_command="Hardware Version",
        )

        major, minor, patch = response.data[-3:]
        return Version(major=major, minor=minor, patch=patch)

    async def get_firmware_version(self, node: Union[str, Node]) -> Version:
        """Retrieve the firmware version of a node

        Parameters
        ----------

        node:
            The node which should return its firmware version

        Returns
        -------

        The firmware version of the specified node

        Example
        -------

        >>> from asyncio import run

        Read the firmware version of STU 1

        >>> async def read_firmware_version():
        ...     async with Network() as network:
        ...         return await network.get_firmware_version('STU 1')
        >>> firmware_version = run(read_firmware_version())
        >>> firmware_version.major
        2

        """

        response = await self._request_product_data(
            node=node,
            description=f"read firmware version of node “{node}”",
            block_command="Firmware Version",
        )

        major, minor, patch = response.data[-3:]
        return Version(major=major, minor=minor, patch=patch)

    async def get_firmware_release_name(self, node: Union[str, Node]) -> str:
        """Retrieve the firmware release name of a node

        Parameters
        ----------

        node:
            The node which should return its firmware release name

        Returns
        -------

        The firmware release name of the specified node

        Example
        -------

        >>> from asyncio import run

        Read the firmware release name of STU 1

        >>> async def read_release_name():
        ...     async with Network() as network:
        ...         return await network.get_firmware_release_name('STU 1')
        >>> run(read_release_name())
        'Valerie'

        """

        response = await self._request_product_data(
            node=node,
            description=f"read firmware release name of node “{node}”",
            block_command="Release Name",
        )

        release_name = convert_bytes_to_text(response.data, until_null=True)
        return release_name

    async def get_serial_number(self, node: Union[str, Node]) -> str:
        """Retrieve the serial number of a node

        Parameters
        ----------

        node:
            The node which should return its serial number

        Returns
        -------

        The serial number of the specified node

        Example
        -------

        >>> from asyncio import run

        Read the serial number of STU 1

        >>> async def read_serial_number():
        ...     async with Network() as network:
        ...         return await network.get_serial_number('STU 1')
        >>> serial_number = run(read_serial_number())
        >>> isinstance(serial_number, str)
        True
        >>> 0 <= len(serial_number) <= 32
        True

        """

        async def get_serial_number_part(part: int) -> bytearray:
            """Retrieve a part of the serial number"""
            response = await self._request_product_data(
                node=node,
                description=(
                    f"read part {part} of the serial number of node “{node}”"
                ),
                block_command=f"Serial Number {part}",
            )
            return response.data

        serial_number_bytes = bytearray()
        for part in range(1, 5):
            serial_number_bytes.extend(await get_serial_number_part(part))

        return convert_bytes_to_text(serial_number_bytes)

    async def get_product_name(self, node: Union[str, Node]) -> str:
        """Retrieve the product name of a node

        Parameters
        ----------

        node:
            The node which should return its product name

        Returns
        -------

        The product name of the specified node

        Example
        -------

        >>> from asyncio import run

        Read the product name of STU 1

        >>> async def read_product_name():
        ...     async with Network() as network:
        ...         return await network.get_product_name('STU 1')
        >>> product_name = run(read_product_name())
        >>> isinstance(product_name, str)
        True
        >>> 0 <= len(product_name) <= 128
        True

        """

        async def get_product_name_part(part: int) -> bytearray:
            """Retrieve a part of the product name"""
            response = await self._request_product_data(
                node=node,
                description=(
                    f"read part {part} of the product name of node “{node}”"
                ),
                block_command=f"Product Name {part}",
            )
            return response.data

        product_name_bytes = bytearray()
        for part in range(1, 17):
            product_name_bytes.extend(await get_product_name_part(part))

        return convert_bytes_to_text(product_name_bytes)

    async def get_oem_data(self, node: Union[str, Node]) -> bytearray:
        """Retrieve the OEM (free use) data

        Parameters
        ----------

        node:
            The node which should return its OEM data

        Returns
        -------

        The OEM data of the specified node

        Example
        -------

        >>> from asyncio import run

        Read the OEM data of STU 1

        >>> async def read_oem_data():
        ...     async with Network() as network:
        ...         return await network.get_oem_data('STU 1')
        >>> oem_data = run(read_oem_data())
        >>> isinstance(oem_data, bytearray)
        True
        >>> len(oem_data)
        64

        """

        async def get_oem_part(part: int) -> bytearray:
            """Retrieve a part of the OEM data"""
            response = await self._request_product_data(
                node=node,
                description=(
                    f"read part {part} of the OEM data of node “{node}”"
                ),
                block_command=f"OEM Free Use {part}",
            )
            return response.data

        oem_data = bytearray()
        for part in range(1, 9):
            oem_data.extend(await get_oem_part(part))

        return oem_data


# pylint: enable=too-many-public-methods

# -- Main ---------------------------------------------------------------------

if __name__ == "__main__":
    from doctest import run_docstring_examples, testmod

    # To debug a single doctest, please
    # - set `run_all_doctests` to `False`, and
    # - replace `read_eeprom_firmware_version` with the name of the method you
    #   would like to test.
    RUN_ALL_DOCTESTS = False
    if RUN_ALL_DOCTESTS:
        testmod()
    else:
        run_docstring_examples(
            Network.read_streaming_data_single,
            globals(),
            verbose=True,
        )
