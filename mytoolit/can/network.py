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

        >>> network = Network()
        >>> network.shutdown()

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

    async def reset_node(self, node: Union[str, Node] = 'STH 1') -> None:
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

        listener = ResponseListener(message.identifier())

        notifier = Notifier(self.bus,
                            listeners=[listener],
                            loop=get_running_loop())

        self.bus.send(message.to_python_can())

        try:
            response = await wait_for(listener.on_message(), timeout=1)
            assert response is not None
        except TimeoutError:
            raise NoResponseError(f"Unable to reset node “{node}”")
        finally:
            notifier.stop()

        if response.is_error:
            raise ErrorResponseError(
                f"Received error response for reset request from “{node}”")

    def shutdown(self) -> None:
        """Deallocate all resources for this network connection"""

        self.bus.shutdown()


# -- Main ---------------------------------------------------------------------

if __name__ == '__main__':
    from doctest import testmod

    testmod()
