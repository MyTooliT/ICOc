# -- Imports ------------------------------------------------------------------

from __future__ import annotations

from asyncio import (CancelledError, get_running_loop, sleep, TimeoutError,
                     Queue, wait_for)
from sys import platform
from types import TracebackType
from typing import List, NamedTuple, Optional, Type, Union

from can import Bus, Listener, Message as CANMessage, Notifier
from netaddr import EUI

# Fix imports for script usage
if __name__ == '__main__':
    from pathlib import Path
    from sys import path
    path.append(str(Path(__file__).parent.parent.parent))

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


class ResponseListener(Listener):
    """A listener that reacts to messages containing a certain id"""

    def __init__(
            self, message: Message, expected_data: Union[bytearray,
                                                         List[Optional[int]],
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
        self.bus = Bus(**bus_config)

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

        listener = ResponseListener(message, response_data)
        self.notifier.add_listener(listener)
        self.bus.send(message.to_python_can())

        try:
            response = await wait_for(listener.on_message(), timeout=1)
            assert response is not None
        except TimeoutError:
            raise NoResponseError(f"Unable to {description}")
        finally:
            self.notifier.remove_listener(listener)

        if response.is_error:
            raise ErrorResponseError(
                f"Received erroneous response for request to {description}")

        return response.message

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

    async def get_available_devices_bluetooth(self,
                                              node: Union[str, Node] = 'STU 1'
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
        ...     with Network() as network:
        ...         await network.activate_bluetooth('STU 1')
        ...         # Wait for device scan in node STU 1 to take place
        ...         await sleep(1)
        ...         return await network.get_available_devices_bluetooth(
        ...                     'STU 1')
        >>> run(get_number_bluetooth_devices())
        1

        """

        answer = await self._request_bluetooth(
            node=node,
            subcommand=2,
            description=f"get available Bluetooth devices of node “{node}”")

        available_devices = int(bytearray_to_text(answer.data[2:]))

        return available_devices

    async def get_device_name_bluetooth(self,
                                        node: Union[str, Node] = 'STU 1',
                                        device_number: int = 0) -> str:
        """Retrieve the name of a Bluetooth device

        This also works when the given node is not connected to the Bluetooth
        device. Before you use this method make sure you activated the
        Bluetooth connection on the given node.

        Parameters
        ----------

        node:
            The node which has access to the Bluetooth device

        device_number:
            The number of the Bluetooth device (0 up to the number of
            available devices - 1; 0x00 for self addressing).

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
        ...         await sleep(0.2)
        ...         # We assume that at least one STH is available
        ...         return await network.get_device_name_bluetooth(
        ...                         'STU 1', device_number=0)
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
        ...         await sleep(0.1)
        >>> run(deactivate_bluetooth())

        """

        await self._request_bluetooth(
            node=node,
            subcommand=9,
            description=f"deactivate Bluetooth on “{node}”",
            response_data=6 * [0]  # type: ignore[arg-type]
        )

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
        ...         # Wait for device scan in node STU 1 to take place
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

    async def get_mac_address_bluetooth(self,
                                        node: Union[str, Node] = 'STH 1',
                                        device_number: int = 0xff) -> EUI:
        """Retrieve the Bluetooth MAC address of a connected device

        Parameters
        ----------

        node:
            The node which should retrieve the MAC address

        device_number:
            The number of the Bluetooth device (0 up to the number of
            available devices - 1; 0x00 for self addressing).

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
        ...         mac = await network.get_mac_address_bluetooth('STH 1')
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

    async def connect_sth(self, mac_address: EUI):
        """Connect to an STH using its MAC address"""

        await self.activate_bluetooth('STU 1')

        available_devices = 0
        while available_devices <= 0:
            available_devices = await self.get_available_devices_bluetooth(
                'STU 1')
            await sleep(0.1)

        await self.connect_mac_address_bluetooth(mac_address)

        while not await self.check_connection_device_bluetooth('STU 1'):
            await sleep(0.1)

    def shutdown(self) -> None:
        """Deallocate all resources for this network connection"""

        if self.notifier is not None:
            self.notifier.stop()

        self.bus.shutdown()


# -- Main ---------------------------------------------------------------------

if __name__ == '__main__':
    from doctest import testmod

    testmod()
