# -- Imports ------------------------------------------------------------------

from __future__ import annotations

from asyncio import get_running_loop, sleep, Queue, wait_for
from sys import platform
from types import TracebackType
from typing import Union, Optional, Type

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


class UnexpectedResponseError(Exception):
    """Exception for unexpected response messages"""


class ResetManager(Listener):

    def __init__(self):
        self.queue = Queue()

    def on_message_received(self, message: CANMessage):
        self.queue.put_nowait(message)

    async def on_message(self):
        return await self.queue.get()


class Network:
    """Basic class to communicate with STU and STH devices"""

    def __init__(self, sender: Union[str, Node] = 'SPU 1') -> None:
        """Create a new network from the given arguments

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

        Example
        -------

        >>> from asyncio import run

        >>> async def reset():
        ...     with Network(sender='SPU 1') as network:
        ...         await network.reset_node('STU 1')
        >>> run(reset())

        """

        message = Message(block='System',
                          block_command='Reset',
                          sender=self.sender,
                          receiver=node,
                          request=True)

        listener = ResetManager()

        notifier = Notifier(self.bus,
                            listeners=[listener],
                            loop=get_running_loop())

        ack_message = message.acknowledge()
        self.bus.send(message.to_python_can())

        answer = await wait_for(listener.on_message(), timeout=1)
        notifier.stop()

        if ack_message.id() != answer.arbitration_id:
            self.shutdown()
            raise UnexpectedResponseError(
                f"Received “{Identifier(answer.arbitration_id)}” instead of "
                f"“{ack_message.identifier()}”")

        await sleep(2)  # Wait until the node is up again

    def shutdown(self) -> None:
        """Deallocate all resources for this network connection"""

        self.bus.shutdown()


# -- Main ---------------------------------------------------------------------

if __name__ == '__main__':
    from doctest import testmod

    testmod()
