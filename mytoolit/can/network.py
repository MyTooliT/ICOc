# -- Imports ------------------------------------------------------------------

from __future__ import annotations

from asyncio import (CancelledError, get_running_loop, sleep, TimeoutError,
                     Queue, wait_for)
from struct import pack, unpack
from sys import platform
from time import time
from types import TracebackType
from typing import List, NamedTuple, Optional, Sequence, Type, Union

from can import Bus, Listener, Message as CANMessage, Notifier
from can.interfaces.pcan.pcan import PcanError
from netaddr import EUI

# Fix imports for script usage
if __name__ == '__main__':
    from pathlib import Path
    from sys import path
    path.append(str(Path(__file__).parent.parent.parent))

from mytoolit.eeprom import EEPROMStatus
from mytoolit.config import settings
from mytoolit.can.message import Message
from mytoolit.can.node import Node
from mytoolit.utility import bytearray_to_text

# -- Classes ------------------------------------------------------------------


class NetworkError(Exception):
    """Exception for errors in the MyTooliT network"""


class ErrorResponseError(NetworkError):
    """Exception for erroneous response messages"""


class NoResponseError(NetworkError):
    """Thrown if no response message for a request was received"""


class Response(NamedTuple):
    """Used to store a response (message)"""

    message: CANMessage  # The response message
    is_error: bool  # States if the response was an error or a normal response


class STHDeviceInfo(NamedTuple):
    """Used to store information about a (disconnected) STH"""

    name: str  # The (Bluetooth advertisement) name of the STH
    device_number: int  # The device number of the STH
    mac_address: EUI  # The (Bluetooth) MAC address of the STH
    rssi: int  # The RSSI of the STH

    def __repr__(self) -> str:
        """Return the string representation of an STH"""

        return "🤖 {}".format(", ".join([
            f"Name: {self.name}", f"Device Number: {self.device_number}",
            f"MAC address: {self.mac_address}", f"RSSI: {self.rssi}"
        ]))


class ResponseListener(Listener):
    """A listener that reacts to messages containing a certain id"""

    def __init__(
        self, message: Message, expected_data: Union[bytearray,
                                                     Sequence[Optional[int]],
                                                     None]) -> None:
        """Initialize the listener using the given identifier

        Parameters
        ----------

            The sent message this listener should react to
        message:

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

    def on_message_received(self, message: CANMessage) -> None:
        """React to a received message on the bus

        Parameters
        ----------

        message:
            The received CAN message the notifier should react to

        """

        identifier = message.arbitration_id
        error_response = identifier == self.error_identifier.value
        normal_response = identifier == self.acknowledgment_identifier.value

        # We only store CAN messages that contain the expected (error) response
        # message identifier

        # Also set an error response, if the retrieved message data does not
        # match the expected data
        expected_data = self.expected_data
        if normal_response and expected_data:
            error_response |= any(
                expected != data
                for expected, data in zip(expected_data, message.data)
                if expected is not None)

        if error_response or normal_response:
            self.queue.put_nowait(
                Response(message=message, is_error=error_response))

    async def on_message(self) -> Optional[Response]:
        """Return answer messages for the specified message identifier


        Returns
        -------

        A response containing

        - the response message for the message with the identifier given at
          object creation, and
        - the error status of the response message

        """

        try:
            return await self.queue.get()
        except CancelledError:
            return None


class Network:
    """Basic class to communicate with STU and STH devices"""

    def __init__(self, sender: Union[str, Node] = 'SPU 1') -> None:
        """Create a new network from the given arguments

        Please note, that you have to clean up used resources after you use
        this class using the method `shutdown`. Since this class implements
        the context manager interface we recommend you use a with statement to
        handle the cleanup phase automatically.

        Parameters
        ----------

        sender:
            The default sender of the network

        Examples
        --------

        Create and shutdown the network explicitly

        >>> network = Network()
        >>> network.shutdown()

        Use a context manager to handle the cleanup process automatically

        >>> with Network() as network:
        ...     pass

        """

        configuration = (settings.can.linux
                         if platform == 'linux' else settings.can.windows)
        bus_config = {
            key.lower(): value
            for key, value in configuration.items()
        }
        try:
            self.bus = Bus(**bus_config)
        except (PcanError, OSError) as error:
            raise NetworkError(
                f"Unable to initialize CAN connection: {error}\n\n"
                "Possible reason:\n\n"
                "• CAN adapter is not connected to the computer")

        # We create the notifier when we need it for the first time, since
        # there might not be an active loop when you create the network object
        self.notifier = None
        self.sender = Node(sender)

    def __enter__(self) -> Network:
        """Initialize the network

        Returns
        -------

        An initialized network object

        """

        return self

    def __exit__(self, exception_type: Optional[Type[BaseException]],
                 exception_value: Optional[BaseException],
                 traceback: Optional[TracebackType]) -> None:
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

        self.shutdown()

    async def _request(
        self,
        message: Message,
        description: str,
        response_data: Union[bytearray, List[Union[int, None]], None] = None
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


        Returns
        -------

        The response message for the given request

        Throws
        ------

        NoResponseError:
            If the receiver did not respond to the message after a certain
            amount of time (1s)

        ErrorResponseError:
            If the receiver answered with an error message

        """

        # If there is no notifier yet, create it
        if self.notifier is None:
            self.notifier = Notifier(self.bus,
                                     listeners=[],
                                     loop=get_running_loop())
        assert self.notifier is not None

        for attempt in range(5):

            listener = ResponseListener(message, response_data)
            self.notifier.add_listener(listener)
            self.bus.send(message.to_python_can())

            try:
                response = await wait_for(listener.on_message(), timeout=1)
                assert response is not None
            except TimeoutError:
                continue
            finally:
                self.notifier.remove_listener(listener)

            if response.is_error:
                raise ErrorResponseError(
                    "Received erroneous response for request to "
                    f"{description}: {Message(response.message)}")

            return response.message

        raise NoResponseError(f"Unable to {description}")

    async def _request_bluetooth(
            self,
            node: Union[str, Node],
            subcommand: int,
            description: str,
            device_number: Optional[int] = None,
            data: Optional[List[int]] = None,
            response_data: Optional[List[Optional[int]]] = None) -> CANMessage:
        """Send a request for a certain Bluetooth command

        Parameters
        ----------

        node:
            The node on which the Bluetooth command should be executed

        subcommand:
            The number of the Bluetooth subcommand

        subcommand:
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
        message = Message(block='System',
                          block_command='Bluetooth',
                          sender=self.sender,
                          receiver=node,
                          request=True,
                          data=[subcommand, device_number] + data)

        # The bluetooth subcommand and device number should be the same in the
        # response message
        expected_data: List[Optional[int]] = list(message.data[:2])
        if response_data is not None:
            expected_data.extend(response_data)

        return await self._request(message,
                                   description=description,
                                   response_data=expected_data)

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
        ...     with Network() as network:
        ...         await network.reset_node('STU 1')
        >>> run(reset())

        Reset node, which is not connected

        >>> async def reset():
        ...     with Network() as network:
        ...         await network.reset_node('STH 1')
        >>> run(reset()) # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
            ...
        NoResponseError: Unable to reset node “STH 1”

        """

        message = Message(block='System',
                          block_command='Reset',
                          sender=self.sender,
                          receiver=node,
                          request=True)
        await self._request(message,
                            description=f"reset node “{node}”",
                            response_data=message.data)

    # =============
    # = Bluetooth =
    # =============

    async def activate_bluetooth(self, node: Union[str, Node] = 'STU 1'):
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
        ...     with Network() as network:
        ...         await network.activate_bluetooth('STU 1')
        >>> run(activate())

        """

        await self._request_bluetooth(
            node=node,
            subcommand=1,
            description=f"activate Bluetooth of node “{node}”",
            response_data=6 * [0]  # type: ignore[arg-type]
        )

    async def deactivate_bluetooth(self,
                                   node: Union[str, Node] = 'STU 1') -> None:
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
        ...     with Network() as network:
        ...         # Deactivate Bluetooth connection
        ...         await network.deactivate_bluetooth('STU 1')
        ...         # Wait until device is disconnected
        ...         await sleep(0.2)
        >>> run(deactivate_bluetooth())

        """

        await self._request_bluetooth(
            node=node,
            subcommand=9,
            description=f"deactivate Bluetooth on “{node}”",
            response_data=6 * [0]  # type: ignore[arg-type]
        )

    async def get_available_devices(self,
                                    node: Union[str, Node] = 'STU 1') -> int:
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
        ...     with Network() as network:
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
            description=f"get available Bluetooth devices of node “{node}”")

        available_devices = int(bytearray_to_text(answer.data[2:]))

        return available_devices

    async def get_name(self,
                       node: Union[str, Node] = 'STU 1',
                       device_number: int = 0) -> str:
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
           own name.

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

        Get Bluetooth advertisement name of device “0” from STU 1

        >>> async def get_bluetooth_device_name():
        ...     with Network() as network:
        ...         await network.activate_bluetooth('STU 1')
        ...         # Wait for device scan in node STU 1 to take place
        ...         await sleep(1)
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
            description=f"get first part of {description}")

        first_part = bytearray_to_text(answer.data[2:])

        answer = await self._request_bluetooth(
            node=node,
            subcommand=6,
            device_number=device_number,
            description=f"get second part of {description}")

        second_part = bytearray_to_text(answer.data[2:])

        return first_part + second_part

    async def get_mac_address(self,
                              node: Union[str, Node] = 'STH 1',
                              device_number: int = 0xff) -> EUI:
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
           own device number.

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
        ...     with Network() as network:
        ...         await network.activate_bluetooth('STU 1')
        ...         # We assume that at least one STH is available
        ...         await network.connect_device_number_bluetooth(
        ...                         'STU 1', device_number=0)
        ...
        ...         while not (await
        ...                   network.check_connection_device_bluetooth()):
        ...             await sleep(0.1)
        ...
        ...         mac = await network.get_mac_address('STH 1')
        ...
        ...         # Deactivate Bluetooth connection
        ...         await network.deactivate_bluetooth('STU 1')
        ...         # Wait until device is disconnected
        ...         await sleep(0.1)
        ...         return mac
        >>> mac_address = run(get_bluetooth_mac())
        >>> isinstance(mac_address, EUI)
        True

        """

        response = await self._request_bluetooth(
            node=node,
            subcommand=17,
            description=f"get MAC address of “{device_number}” from “{node}”")

        return EUI(":".join(f"{byte:02x}" for byte in response.data[:1:-1]))

    async def get_rssi(self,
                       node: Union[str, Node] = 'STH 1',
                       device_number: int = 0xff):
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
        ...     with Network() as network:
        ...         await network.activate_bluetooth('STU 1')
        ...
        ...         # We assume that at least one STH is available
        ...         # Get the RSSI of device “0”
        ...         rssi = await network.get_rssi('STU 1', 0)
        ...
        ...         # Deactivate Bluetooth connection
        ...         await network.deactivate_bluetooth('STU 1')
        ...
        ...         return rssi
        >>> rssi = run(get_bluetooth_rssi())
        >>> -70 < rssi < 0
        True

        """

        response = await self._request_bluetooth(
            node=node,
            subcommand=12,
            description=f"get RSSI of “{device_number}” from “{node}”")

        return int.from_bytes(response.data[2:3],
                              byteorder='little',
                              signed=True)

    async def get_sths(self,
                       node: Union[str,
                                   Node] = 'STU 1') -> List[STHDeviceInfo]:
        """Retrieve a list of available STHs

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

        >>> async def get_sths():
        ...     with Network() as network:
        ...
        ...         # We assume that at least one STH is available
        ...         devices = []
        ...         while not devices:
        ...             devices = await network.get_sths()
        ...             await sleep(0.1)
        ...
        ...         return devices
        >>> sths = run(get_sths())
        >>> len(sths) >= 1
        True
        >>> sth = sths[0]

        >>> sth.device_number
        0

        >>> isinstance(sth.name, str)
        True
        >>> 0 <= len(sth.name) <= 8
        True

        >>> -70 < sth.rssi < 0
        True

        >>> isinstance(sth.mac_address, EUI)
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
                STHDeviceInfo(device_number=device,
                              mac_address=mac_address,
                              name=name,
                              rssi=rssi))

        return devices

    async def connect_device_number_bluetooth(self,
                                              node: Union[str, Node] = 'STU 1',
                                              device_number: int = 0) -> bool:
        """Connect to a Bluetooth device using a device number

        Parameters
        ----------

        node:
            The node which should connect to the Bluetooth device

        device_number:
            The number of the Bluetooth device (0 up to the number of
            available devices - 1; 0x00 for self addressing).

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
        ...     with Network() as network:
        ...         await network.activate_bluetooth('STU 1')
        ...         # We assume that at least one STH is available
        ...         status = False
        ...         while not status:
        ...             status = await network.connect_device_number_bluetooth(
        ...                         'STU 1', device_number=0)
        ...
        ...         # Deactivate Bluetooth connection
        ...         await network.deactivate_bluetooth('STU 1')
        ...         # Wait until device is disconnected
        ...         await sleep(0.1)
        ...         # Return status of Bluetooth device connect response
        ...         return status
        >>> run(connect_bluetooth_device_number())
        True

        """

        response = await self._request_bluetooth(
            node=node,
            subcommand=7,
            device_number=device_number,
            description=f"connect to “{device_number}” from “{node}”")

        return bool(response.data[2])

    async def connect_mac_address_bluetooth(self,
                                            mac_address: EUI,
                                            node: Union[str, Node] = 'STU 1'
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
            description=f"connect to device “{mac_address}” from “{node}”")

    async def check_connection_device_bluetooth(self,
                                                node: Union[str,
                                                            Node] = 'STU 1'
                                                ) -> bool:
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
        ...     with Network() as network:
        ...         await network.activate_bluetooth('STU 1')
        ...         await sleep(0.1)
        ...         connected_start = (await
        ...             network.check_connection_device_bluetooth('STU 1'))
        ...
        ...         # We assume that at least one STH is available
        ...         await network.connect_device_number_bluetooth(
        ...                         'STU 1', device_number=0)
        ...
        ...         # Wait for device connection
        ...         connected_between = False
        ...         while not connected_between:
        ...             connected_between = (
        ...                 await network.check_connection_device_bluetooth())
        ...             await sleep(0.1)
        ...
        ...         # Deactivate Bluetooth connection
        ...         await network.deactivate_bluetooth('STU 1')
        ...         # Wait until device is disconnected
        ...         await sleep(0.1)
        ...         connected_after = (await
        ...             network.check_connection_device_bluetooth('STU 1'))
        ...
        ...         return connected_start, connected_between, connected_after
        >>> run(check_bluetooth_connection())
        (False, True, False)

        """

        response = await self._request_bluetooth(
            node=node,
            subcommand=8,
            response_data=[None, *(5 * [0])],
            description=f"check if “{node}” is connected to a Bluetooth device"
        )

        return bool(response.data[2])

    async def connect_sth(self, identifier: Union[int, str, EUI]) -> None:
        """Connect to an STH

        Parameters
        ----------

        identifier:
            The

            - MAC address (`EUI`),
            - name (`str`), or
            - device number (`int`)

            of the STH we want to connect to

        Example
        -------

        >>> from asyncio import run

        Connect to the STH with device number `0`

        >>> async def connect_sth():
        ...     with Network() as network:
        ...         await network.connect_sth(0)
        ...         return await network.check_connection_device_bluetooth()
        >>> run(connect_sth())
        True

        """

        def get_mac_address(sths: List[STHDeviceInfo],
                            identifier: Union[int, str, EUI]) -> Optional[EUI]:
            """Get the MAC address of an STH"""

            for sth in sths:
                if (isinstance(identifier, str) and sth.name == identifier
                        or isinstance(identifier, int)
                        and sth.device_number == identifier
                        or sth.mac_address == identifier):
                    return sth.mac_address

            return None

        if not (isinstance(identifier, str) or isinstance(identifier, int)
                or isinstance(identifier, EUI)):
            raise TypeError("Identifier must be int, str or EUI, not "
                            f"{type(identifier).__name__}")

        await self.deactivate_bluetooth('STU 1')  # Disconnect from STH
        await self.activate_bluetooth('STU 1')

        # We wait a maximum of 5 seconds for the connection to the STH to take
        # place
        timeout_in_s = 5
        end_time = time() + timeout_in_s

        mac_address = None
        sths: List[STHDeviceInfo] = []
        while mac_address is None:
            if time() > end_time:
                sths_representation = '\n'.join([repr(sth) for sth in sths])
                sth_info = (f"Found the following STHs:\n{sths_representation}"
                            if len(sths) > 0 else "No STHs found")

                raise TimeoutError(
                    "Unable to find STH with {} “{}” in {} seconds".format(
                        "MAC address" if isinstance(identifier, EUI) else
                        "device_number" if isinstance(identifier, int) else
                        "name", identifier, timeout_in_s) + f"\n\n{sth_info}")

            sths = await self.get_sths()
            mac_address = get_mac_address(sths, identifier)
            if mac_address is None:
                await sleep(0.1)

        await self.connect_mac_address_bluetooth(mac_address)
        while not await self.check_connection_device_bluetooth('STU 1'):
            if time() > end_time:
                raise TimeoutError(
                    "Unable to connect to STH with MAC address "
                    f"“{mac_address}” in {timeout_in_s} seconds")

            await sleep(0.1)

    # ==========
    # = EEPROM =
    # ==========

    async def read_eeprom(self,
                          address: int,
                          offset: int,
                          length: int,
                          node: Union[str, Node] = 'STU 1') -> List[int]:
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
        ...     with Network() as network:
        ...         return await network.read_eeprom(address=0, offset=1,
        ...                                          length=8, node='STU 1')
        >>> data = run(read_eeprom())
        >>> len(data)
        8
        >>> all((0 <= byte <= 255 for byte in data))
        True

        """

        read_data = []
        reserved = [0] * 5
        data_start = 4  # Start index of data in response message

        while length > 0:
            # Read at most 4 bytes of data at once
            read_length = 4 if length > 4 else length
            message = Message(block='EEPROM',
                              block_command='Read',
                              sender=self.sender,
                              receiver=Node(node),
                              request=True,
                              data=[address, offset, read_length, *reserved])
            response = await self._request(
                message, description=f"read EEPROM data from “{node}”")

            data_end = data_start + read_length
            read_data.extend(response.data[data_start:data_end])
            length -= read_length
            offset += read_length

        return read_data

    async def read_eeprom_float(self,
                                address: int,
                                offset: int,
                                node: Union[str, Node] = 'STU 1') -> float:
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

        Read slope of acceleration for x-axis of STH 1

        >>> async def read_slope():
        ...     with Network() as network:
        ...         await network.connect_sth(0)
        ...         slope = await network.read_eeprom_float(
        ...             address=8, offset=0, node='STH 1')
        ...         await network.deactivate_bluetooth('STU 1')
        ...         return slope
        >>> slope = run(read_slope())
        >>> isinstance(slope, float)
        True

        """

        data = await self.read_eeprom(address, offset, length=4, node=node)
        return unpack('<f', bytearray(data))[0]

    async def read_eeprom_int(self,
                              address: int,
                              offset: int,
                              length: int,
                              signed: bool = False,
                              node: Union[str, Node] = 'STU 1') -> int:
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
        ...     with Network() as network:
        ...         return await network.read_eeprom_int(
        ...             address=5, offset=8, length=4, node='STU 1')
        >>> operating_time = run(read_operating_time())
        >>> operating_time >= 0
        True

        """

        return int.from_bytes(await self.read_eeprom(address, offset, length,
                                                     node),
                              'little',
                              signed=True)

    async def read_eeprom_text(self,
                               address: int,
                               offset: int,
                               length: int,
                               node: Union[str, Node] = 'STU 1') -> str:
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
        ...     with Network() as network:
        ...         return await network.read_eeprom_text(
        ...             address=0, offset=1, length=8, node='STU 1')
        >>> name = run(read_name_eeprom())
        >>> 0 <= len(name) <= 8
        True
        >>> isinstance(name, str)
        True

        """

        data = await self.read_eeprom(address, offset, length, node)
        data_without_null = []
        for byte in data:
            if byte == 0:
                break
            data_without_null.append(byte)

        return "".join(map(chr, data_without_null))

    async def write_eeprom(self,
                           address: int,
                           offset: int,
                           data: List[int],
                           length: Optional[int] = None,
                           node: Union[str, Node] = 'STU 1') -> None:
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
        ...     with Network() as network:
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
                block='EEPROM',
                block_command='Write',
                sender=self.sender,
                receiver=Node(node),
                request=True,
                data=[address, offset, write_length, *reserved, *write_data])
            await self._request(message,
                                description=f"write EEPROM data in “{node}”")

            data = data[4:]
            offset += write_length

    async def write_eeprom_float(self,
                                 address: int,
                                 offset: int,
                                 value: float,
                                 node: Union[str, Node] = 'STU 1') -> None:
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
        ...     with Network() as network:
        ...         await network.write_eeprom_float(
        ...             address=10, offset=0, value=value, node='STU 1')
        ...         return await network.read_eeprom_float(
        ...             address=10, offset=0, node='STU 1')
        >>> value = 42.5
        >>> read_value = run(write_and_read_float(value))
        >>> value == read_value
        True

        """

        data = list(pack('f', value))
        await self.write_eeprom(address, offset, data, node=node)

    async def write_eeprom_int(self,
                               address: int,
                               offset: int,
                               value: int,
                               length: int,
                               signed: bool = False,
                               node: Union[str, Node] = 'STU 1') -> None:
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
        ...     with Network() as network:
        ...         await network.write_eeprom_int(address=10, offset=0,
        ...                 value=value, length=8, signed=True, node='STU 1')
        ...         return await network.read_eeprom_int(address=10, offset=0,
        ...                 length=8, signed=True, node='STU 1')
        >>> value = -1337
        >>> read_value = run(write_and_read_int(value))
        >>> value == read_value
        True

        """

        data = list(value.to_bytes(length, byteorder='little', signed=signed))
        await self.write_eeprom(address, offset, data, node=node)

    async def write_eeprom_text(self,
                                address: int,
                                offset: int,
                                text: str,
                                length: int,
                                node: Union[str, Node] = 'STU 1') -> None:
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
        ...     with Network() as network:
        ...         await network.write_eeprom_text(address=10, offset=11,
        ...                 text=text, length=len(text), node='STU 1')
        ...         return await network.read_eeprom_text(
        ...             address=10, offset=11, length=len(text), node='STU 1')
        >>> run(write_and_read_text("something"))
        'something'

        """

        data = list(map(ord, list(text)))
        await self.write_eeprom(address, offset, data, length, node)

    async def read_eeprom_status(self,
                                 node: Union[str,
                                             Node] = 'STU 1') -> EEPROMStatus:
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
        ...     with Network() as network:
        ...         return await network.read_eeprom_status(node='STU 1')
        >>> isinstance(run(read_status_byte()), EEPROMStatus)
        True

        """

        return EEPROMStatus((await self.read_eeprom(address=0,
                                                    offset=0,
                                                    length=1,
                                                    node=node)).pop())

    async def write_eeprom_status(self,
                                  value: Union[int, EEPROMStatus],
                                  node: Union[str, Node] = 'STU 1') -> None:
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
        ...     with Network() as network:
        ...         await network.write_eeprom_status(
        ...             EEPROMStatus('Initialized'), node='STU 1')
        ...         return await network.read_eeprom_status(node='STU 1')
        >>> status = run(write_read_status_byte())
        >>> status.is_initialized()
        True

        """

        await self.write_eeprom_int(address=0,
                                    offset=0,
                                    length=1,
                                    value=EEPROMStatus(value).value)

    async def read_eeprom_name(self, node: Union[str, Node] = 'STU 1') -> str:
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
        ...     with Network() as network:
        ...         return await network.read_eeprom_name(node='STU 1')
        >>> isinstance(run(read_name()), str)
        True

        """

        return await self.read_eeprom_text(address=0,
                                           offset=1,
                                           length=8,
                                           node=node)

    def shutdown(self) -> None:
        """Deallocate all resources for this network connection"""

        if self.notifier is not None:
            self.notifier.stop()

        self.bus.shutdown()


# -- Main ---------------------------------------------------------------------

if __name__ == '__main__':
    from doctest import testmod

    testmod()
