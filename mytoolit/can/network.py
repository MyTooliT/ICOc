# -- Imports ------------------------------------------------------------------

from __future__ import annotations

from asyncio import (CancelledError, get_running_loop, TimeoutError, Queue,
                     wait_for)
from sys import platform
from types import TracebackType
from typing import Union, Optional, NamedTuple, Type

from can import Bus, Listener, Message as CANMessage, Notifier

# Fix imports for script usage
if __name__ == '__main__':
    from pathlib import Path
    from sys import path
    path.append(str(Path(__file__).parent.parent.parent))

from mytoolit.config import settings
from mytoolit.can.identifier import Identifier
from mytoolit.can.message import Message
from mytoolit.can.node import Node
from mytoolit.utility import bytearray_to_text

# -- Classes ------------------------------------------------------------------


class NetworkError(Exception):
    """Exception for errors in the MytooliT network"""


class ErrorResponseError(NetworkError):
    """Exception for error response messages"""


class NoResponseError(NetworkError):
    """Thrown if no response message for a request was received"""


class Response(NamedTuple):
    """Used to store a response (message)"""

    message: CANMessage  # The response message
    is_error: bool  # States if the response was an error or a normal response


class ResponseListener(Listener):
    """A listener that reacts to messages containing a certain id"""

    def __init__(self, identifier: Identifier) -> None:
        """Initialize the listener using the given identifier

        Parameters
        ----------

        identifier
            The identifier of a sent message this listener should react to

        """

        self.queue: Queue[Response] = Queue()
        self.acknowledgment_identifier = identifier.acknowledge()
        self.error_idenftifier = identifier.acknowledge(error=True)

    def on_message_received(self, message: CANMessage) -> None:
        """React to a received message on the bus

        Parameters
        ----------

        message
            The received CAN message the notifier should react to

        """

        identifier = message.arbitration_id
        # Only store CAN messages that contain the expected response message
        # identifier
        error_response = identifier == self.error_idenftifier.value
        normal_response = identifier == self.acknowledgment_identifier.value
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

    async def _request(self, message: Message, description: str) -> CANMessage:
        """Send a request message and wait for the response

        Parameters
        ----------

        message:
            The message containing the request

        description:
            A description of the request used in error messages

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

        listener = ResponseListener(message.identifier())

        notifier = Notifier(self.bus,
                            listeners=[listener],
                            loop=get_running_loop())

        self.bus.send(message.to_python_can())

        try:
            response = await wait_for(listener.on_message(), timeout=1)
            assert response is not None
        except TimeoutError:
            raise NoResponseError(f"Unable to {description}")
        finally:
            notifier.stop()

        if response.is_error:
            raise ErrorResponseError(
                f"Received error response for request to {description}")

        return response.message

    async def _request_bluetooth(
            self,
            node: Union[str, Node],
            subcommand: int,
            description: str,
            device_number: Optional[int] = None) -> CANMessage:
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

        Returns
        -------

        The response message for the given request

        """

        device_number = 0 if device_number is None else device_number
        message = Message(block='System',
                          block_command='Bluetooth',
                          sender=self.sender,
                          receiver=node,
                          request=True,
                          data=[subcommand, device_number] + [0] * 6)

        return await self._request(message, description=description)

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
        await self._request(message, description=f"reset node “{node}”")

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
            description=f"activate Bluetooth of node “{node}”")

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
        ...         await sleep(0.1)
        ...         return await network.get_available_devices_bluetooth(
        ...                     'STU 1')
        >>> run(get_number_bluetooth_devices())
        1

        """

        answer = await self._request_bluetooth(
            node=node,
            subcommand=2,
            description=f"activate Bluetooth of node “{node}”")

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
            The number of the Bluetooth device; The possible Bluetooth device
            numbers include integers from 0 up to the number of available
            devices - 1.

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
        ...         await sleep(0.1)
        ...         # We assume that at least one STH is available
        ...         return await network.get_device_name_bluetooth(
        ...                         'STU 1', device_number=0)
        >>> sth_name = run(get_bluetooth_device_name())
        >>> isinstance(sth_name, str)
        True
        >>> 0 <= len(sth_name) <= 8
        True

        """

        answer = await self._request_bluetooth(
            node=node,
            subcommand=5,
            device_number=device_number,
            description="get first part of device name of device "
            f"“{device_number}” from “{node}”")

        first_part = bytearray_to_text(answer.data[2:])

        answer = await self._request_bluetooth(
            node=node,
            subcommand=6,
            device_number=device_number,
            description="get second part of device name of device "
            f"“{device_number}” from “{node}”")

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
            The number of the Bluetooth device; The possible Bluetooth device
            numbers include integers from 0 up to the number of available
            devices - 1.

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
        ...         # Wait for device scan in node STU 1 to take place
        ...         await sleep(0.1)
        ...         # We assume that at least one STH is available
        ...         status = await network.connect_device_number_bluetooth(
        ...                         'STU 1', device_number=0)
        ...         # Wait for device connection
        ...         await sleep(0.1)
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
            description=f"deactivate Bluetooth on “{node}”")

    async def check_connection_device_bluetooth(
            self,
            node: Union[str, Node] = 'STU 1',
            device_number: int = 0) -> bool:

        response = await self._request_bluetooth(
            node=node,
            subcommand=8,
            description=f"check if device “{device_number}” is connected "
            f"to “{node}”")

        return bool(response.data[2])

    def shutdown(self) -> None:
        """Deallocate all resources for this network connection"""

        self.bus.shutdown()


# -- Main ---------------------------------------------------------------------

if __name__ == '__main__':
    from doctest import testmod

    testmod()
