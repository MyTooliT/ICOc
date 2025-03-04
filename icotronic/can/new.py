"""Communicate with the ICOtronic system"""

# -- Imports ------------------------------------------------------------------

from __future__ import annotations

from asyncio import wait_for
from logging import getLogger
from sys import platform
from types import TracebackType
from typing import Type

from can import Bus, BusABC, Message as CANMessage, Notifier
from can.interfaces.pcan.pcan import PcanError
from netaddr import EUI

from icotronic.can.message import Message
from icotronic.can.network import (
    CANInitError,
    ErrorResponseError,
    Logger,
    NoResponseError,
    ResponseListener,
)
from icotronic.can.node import NodeId
from icotronic.can.status import State
from icotronic.config import settings
from icotronic.utility.data import convert_bytes_to_text

# -- Classes ------------------------------------------------------------------


class CANNetwork:
    """Basic class to initialize CAN communication"""

    def __init__(self) -> None:
        """Create a network without initializing the CAN connection

        To actually connect to the CAN bus you need to use the async context
        manager, provided by this class. If you want to manage the connection
        yourself, please just use `__aenter__` and `__aexit__` manually.

        Examples
        --------

        Create a new network (without connecting to the CAN bus)

        >>> network = CANNetwork()

        """

        self.configuration = (
            settings.can.linux
            if platform == "linux"
            else (
                settings.can.mac
                if platform == "darwin"
                else settings.can.windows
            )
        )
        self.bus: BusABC | None = None
        self.notifier: Notifier | None = None

    async def __aenter__(self) -> SPU:
        """Initialize the network

        Returns
        -------

        An network object that can be used to communicate with the STU

        Raises
        ------

        `CANInitError` if the CAN initialization fails

        Examples
        --------

        >>> from asyncio import run

        Use a context manager to handle the cleanup process automatically

        >>> async def connect_can_context():
        ...     async with CANNetwork() as network:
        ...         pass
        >>> run(connect_can_context())

        Create and shutdown the connection explicitly

        >>> async def connect_can_manual():
        ...     network = CANNetwork()
        ...     connected = await network.__aenter__()
        ...     await network.__aexit__(None, None, None)
        >>> run(connect_can_manual())

        """

        try:
            self.bus = Bus(  # pylint: disable=abstract-class-instantiated
                channel=self.configuration.get("channel"),
                interface=self.configuration.get("interface"),
                bitrate=self.configuration.get("bitrate"),
            )  # type: ignore[abstract]
        except (PcanError, OSError) as error:
            raise CANInitError(
                f"Unable to initialize CAN connection: {error}\n\n"
                "Possible reason:\n\n"
                "• CAN adapter is not connected to the computer"
            ) from error

        self.bus.__enter__()

        self.notifier = Notifier(self.bus, listeners=[Logger()])

        return SPU(self.bus, self.notifier)

    async def __aexit__(
        self,
        exception_type: Type[BaseException] | None,
        exception_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Disconnect CAN connection and clean up resources

        Parameters
        ----------

        exception_type:
            The type of the exception in case of an exception

        exception_value:
            The value of the exception in case of an exception

        traceback:
            The traceback in case of an exception

        """

        bus = self.bus
        if bus is not None:
            bus.__exit__(exception_type, exception_value, traceback)
            bus.shutdown()

        notifier = self.notifier
        if notifier is not None:
            notifier.stop()


# pylint: disable=too-few-public-methods


class SPU:
    """Communicate with the ICOtronic system acting as SPU"""

    def __init__(self, bus: BusABC, notifier: Notifier) -> None:
        """Create an SPU instance using the given arguments

        We strongly recommend you use the context manager interface of the
        `CANNetwork` class to create objects of this type.

        Parameters
        ----------

        bus:
            A CAN bus object used to communicate with the STU

        notifier:
            A notifier class that listens to the communication of `bus`

        Examples
        --------

        >>> from asyncio import run

        Create a new CAN network connection using context manager interface

        >>> async def create_connection():
        ...     async with CANNetwork() as spu:
        ...         # Use `spu.stu` to communicate with the STU
        ...         pass
        >>> run(create_connection())

        """

        self.bus = bus
        self.notifier = notifier
        self.sender = NodeId("SPU 1")
        self.streaming = False
        self.stu = STU(self)

    # pylint: disable=too-many-arguments, too-many-positional-arguments

    async def _request(
        self,
        message: Message,
        description: str,
        response_data: bytearray | list[int | None] | None = None,
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
        node: str | NodeId,
        subcommand: int,
        description: str,
        device_number: int | None = None,
        data: list[int] | None = None,
        response_data: list[int | None] | None = None,
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
        expected_data: list[int | None]
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

    # pylint: enable=too-many-arguments, too-many-positional-arguments

    # ==========
    # = System =
    # ==========

    async def _reset_node(self, node: str | NodeId) -> None:
        """Reset the specified node

        Parameters
        ----------

        node:
            The node to reset

        Examples
        --------

        >>> from asyncio import run

        Reset node, which is not connected

        >>> async def reset():
        ...     async with CANNetwork() as spu:
        ...         await spu._reset_node('STH 1')
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

    async def _get_state(self, node: str | NodeId = "STU 1") -> State:
        """Get the current state of the specified node

        Parameters
        ----------

        node:
            The node which should return its state

        Returns
        -------

        The state of the given node

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


# pylint: enable=too-few-public-methods


class STU:
    """Communicate and control a connected STU"""

    def __init__(self, spu: SPU) -> None:
        """Initialize the STU

        spu:
            The SPU object that created this STU instance

        """

        self.spu = spu
        self.sender = NodeId("STU 1")

    async def reset(self) -> None:
        """Reset the STU

        Examples
        --------

        >>> from asyncio import run

        Reset the current STU

        >>> async def reset():
        ...     async with CANNetwork() as spu:
        ...         await spu.stu.reset()
        >>> run(reset())

        """

        await self.spu._reset_node(  # pylint: disable=protected-access
            self.sender
        )

    async def get_state(self) -> State:
        """Get the current state of the STU

        Examples
        --------

        >>> from asyncio import run

        Get state of STU 1

        >>> async def get_state():
        ...     async with CANNetwork() as spu:
        ...         return await spu.stu.get_state()
        >>> run(get_state())
        Get State, Location: Application, State: Operating

        """

        return await self.spu._get_state(  # pylint: disable=protected-access
            self.sender
        )

    async def activate_bluetooth(self) -> None:
        """Activate Bluetooth on the STU

        Examples
        --------

        >>> from asyncio import run

        Activate Bluetooth on the STU

        >>> async def activate():
        ...     async with CANNetwork() as spu:
        ...         await spu.stu.activate_bluetooth()
        >>> run(activate())

        """

        node = self.sender
        await self.spu._request_bluetooth(  # pylint: disable=protected-access
            node=node,
            subcommand=1,
            description=f"activate Bluetooth of node “{node}”",
            response_data=6 * [0],  # type: ignore[arg-type]
        )

    async def deactivate_bluetooth(self) -> None:
        """Deactivate Bluetooth on the STU

        Examples
        --------

        >>> from asyncio import run, sleep

        Deactivate Bluetooth on STU 1

        >>> async def deactivate_bluetooth():
        ...     async with CANNetwork() as spu:
        ...         await spu.stu.deactivate_bluetooth()
        >>> run(deactivate_bluetooth())

        """

        node = self.sender
        await self.spu._request_bluetooth(  # pylint: disable=protected-access
            node=node,
            subcommand=9,
            description=f"deactivate Bluetooth on “{node}”",
            response_data=6 * [0],  # type: ignore[arg-type]
        )

    async def get_available_devices(self) -> int:
        """Retrieve the number of available sensor devices

        Returns
        -------

        The number of available sensor devices

        Examples
        --------

        >>> from asyncio import run, sleep

        Get the number of available Bluetooth devices at STU 1

        >>> async def get_number_bluetooth_devices():
        ...     async with CANNetwork() as spu:
        ...         stu = spu.stu
        ...         await stu.activate_bluetooth()
        ...
        ...         # We assume at least one STH is available
        ...         number_sths = 0
        ...         while number_sths <= 0:
        ...             number_sths = await stu.get_available_devices()
        ...             await sleep(0.1)
        ...
        ...         return number_sths
        >>> run(get_number_bluetooth_devices()) >= 0
        1

        """

        node = self.sender
        # pylint: disable=protected-access
        answer = await self.spu._request_bluetooth(
            node=node,
            subcommand=2,
            description=f"get available Bluetooth devices of node “{node}”",
        )
        # pylint: enable=protected-access

        available_devices = int(convert_bytes_to_text(answer.data[2:]))

        return available_devices

    async def connect_with_device_number(self, device_number: int = 0) -> bool:
        """Connect to a Bluetooth device using a device number

        Parameters
        ----------

        device_number:
            The number of the Bluetooth device (0 up to the number of
            available devices - 1)

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

        Connect to device “0”

        >>> async def connect_bluetooth_device_number():
        ...     async with CANNetwork() as spu:
        ...         stu = spu.stu
        ...         await stu.activate_bluetooth()
        ...         # We assume that at least one STH is available
        ...         connected = before = await stu.is_connected()
        ...         while not connected:
        ...             connected = await stu.connect_with_device_number(0)
        ...         await stu.deactivate_bluetooth()
        ...         after = await stu.is_connected()
        ...         # Return status of Bluetooth device connect response
        ...         return before, connected, after
        >>> run(connect_bluetooth_device_number())
        (False, True, False)

        """

        node = "STU 1"
        # pylint: disable=protected-access
        response = await self.spu._request_bluetooth(
            node=node,
            subcommand=7,
            device_number=device_number,
            description=f"connect to “{device_number}” from “{node}”",
        )
        # pylint: enable=protected-access

        return bool(response.data[2])

    async def is_connected(self) -> bool:
        """Check if the STU is connected to a Bluetooth device

        Returns
        -------

        - True, if a Bluetooth device is connected to the node
        - False, otherwise

        Example
        -------

        >>> from asyncio import run, sleep

        Check connection of device “0” to STU

        >>> async def check_bluetooth_connection():
        ...     async with CANNetwork() as spu:
        ...         stu = spu.stu
        ...         await stu.activate_bluetooth()
        ...         await sleep(0.1)
        ...         connected_start = await stu.is_connected()
        ...
        ...         # We assume that at least one STH is available
        ...         await stu.connect_with_device_number(0)
        ...         # Wait for device connection
        ...         connected_between = False
        ...         while not connected_between:
        ...             connected_between = await stu.is_connected()
        ...             await sleep(0.1)
        ...             await stu.connect_with_device_number(0)
        ...
        ...         # Deactivate Bluetooth connection
        ...         await stu.deactivate_bluetooth()
        ...         # Wait until device is disconnected
        ...         await sleep(0.1)
        ...         connected_after = await stu.is_connected()
        ...
        ...         return connected_start, connected_between, connected_after
        >>> run(check_bluetooth_connection())
        (False, True, False)

        """

        node = "STU 1"
        # pylint: disable=protected-access
        response = await self.spu._request_bluetooth(
            node=node,
            subcommand=8,
            response_data=[None, *(5 * [0])],
            description=(
                f"check if “{node}” is connected to a Bluetooth device"
            ),
        )
        # pylint: enable=protected-access

        return bool(response.data[2])

    async def get_rssi(self, device_number: int):
        """Retrieve the RSSI (Received Signal Strength Indication) of an STH

        Parameters
        ----------

        device_number:
            The number of the Bluetooth device (0 up to the number of
            available devices)

        Returns
        -------

        The RSSI of the device

        Examples
        --------

        >>> from asyncio import run, sleep

        Retrieve the RSSI of a disconnected STH

        >>> async def get_bluetooth_rssi():
        ...     async with CANNetwork() as spu:
        ...         stu = spu.stu
        ...         await stu.activate_bluetooth()
        ...         # We assume that at least one STH is available
        ...         # Get the RSSI of device “0”
        ...         return await stu.get_rssi(0)
        >>> rssi = run(get_bluetooth_rssi())
        >>> -70 < rssi < 0
        True

        """

        node = "STU 1"
        # pylint: disable=protected-access
        response = await self.spu._request_bluetooth(
            node=node,
            device_number=device_number,
            subcommand=12,
            description=f"get RSSI of “{device_number}” from “{node}”",
        )
        # pylint: enable=protected-access

        return int.from_bytes(
            response.data[2:3], byteorder="little", signed=True
        )

    async def get_mac_address(self, device_number: int) -> EUI:
        """Retrieve the MAC address of a sensor device

        Note: Bluetooth needs to be activated before calling this coroutine,
              otherwise an incorrect MAC address will be returned.

        Parameters
        ----------

        device_number:
            The number of the Bluetooth device (0 up to the number of
            available devices - 1)

        Returns
        -------

        The MAC address of the specified sensor device

        Example
        -------

        >>> from asyncio import run, sleep

        Retrieve the MAC address of STH 1

        >>> async def get_bluetooth_mac():
        ...     async with CANNetwork() as spu:
        ...         stu = spu.stu
        ...         await stu.activate_bluetooth()
        ...         return await stu.get_mac_address(0)
        >>> mac_address = run(get_bluetooth_mac())
        >>> isinstance(mac_address, EUI)
        True
        >>> mac_address != EUI(0)
        True

        """

        node = "STU 1"
        # pylint: disable=protected-access
        response = await self.spu._request_bluetooth(
            node=node,
            device_number=device_number,
            subcommand=17,
            description=f"get MAC address of “{device_number}” from “{node}”",
        )
        # pylint: enable=protected-access

        return EUI(":".join(f"{byte:02x}" for byte in response.data[:1:-1]))


# -- Main ---------------------------------------------------------------------

if __name__ == "__main__":
    from doctest import testmod

    testmod()
