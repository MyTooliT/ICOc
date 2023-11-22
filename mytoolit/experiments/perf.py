# -- Imports ------------------------------------------------------------------

from asyncio import Queue, run
from time import sleep, time
from types import TracebackType
from typing import AsyncIterator, Awaitable, Optional, Type

from can import Listener, Message as CANMessage

from mytoolit.can.identifier import Identifier
from mytoolit.can.message import Message
from mytoolit.can.network import Network

# -- Classes ------------------------------------------------------------------


class AsyncStreamBuffer(Listener):
    """Buffer for streaming data"""

    def __init__(self, first: bool, second: bool, third: bool) -> None:
        """Initialize object using the given arguments

        Parameters
        ----------

        first:
            Specifies if the data of the first measurement channel will be
            collected or not

        second:
            Specifies if the data of the second measurement channel will be
            collected or not

        third:
            Specifies if the data of the third measurement channel will be
            collected or not

        """

        # Expected identifier of received streaming messages
        self.identifier = Identifier(
            block="Streaming",
            block_command="Data",
            sender="STH 1",
            receiver="SPU 1",
            request=False,
        )
        self.first = first
        self.second = second
        self.third = third
        self.queue: Queue[CANMessage] = Queue()

    def __aiter__(self) -> AsyncIterator[CANMessage]:
        """Retrieve iterator for collected data

        Returns
        -------

        An iterator over the received streaming data

        """

        return self

    def __anext__(self) -> Awaitable[CANMessage]:
        """Retrieve next stream data object in collected data

        Returns
        -------

        Retrieved streaming data

        """

        return self.queue.get()

    def on_message_received(self, message: CANMessage) -> None:
        """Handle received messages

        Parameters
        ----------

        message:
            The received CAN message

        """

        self.queue.put_nowait(message)


class DataStreamContextManager:
    """Open and close a data stream from a sensor device"""

    def __init__(
        self, network: Network, first: bool, second: bool, third: bool
    ) -> None:
        """Create a new stream context manager for the given Network

        Parameters
        ----------

        network:
            The CAN network class for which this context manager handles
            sensor device stream data

        first:
            Specifies if the data of the first measurement channel should
            be streamed or not

        second:
            Specifies if the data of the second measurement channel should
            be streamed or not

        third:
            Specifies if the data of the third measurement channel should
            be streamed or not

        """

        self.network = network
        self.reader = AsyncStreamBuffer(first, second, third)

    async def __aenter__(self) -> AsyncStreamBuffer:
        """Open the stream of measurement data

        Returns
        -------

        The stream buffer for the measurement stream

        """

        return await self.open()

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

        await self.close()

    async def open(self) -> AsyncStreamBuffer:
        """Open the stream of measurement data

        Returns
        -------

        The stream buffer for the measurement stream

        """

        reader = self.reader
        await self.network.start_streaming_data(
            reader.first, reader.second, reader.third
        )
        self.network.notifier.add_listener(reader)
        return reader

    async def close(self) -> None:
        """Clean up the resources used by the stream"""

        self.reader.stop()
        self.network.notifier.remove_listener(self.reader)
        await self.network.stop_streaming_data()


class PerfNetwork(Network):
    """Extension of Network class for “performance” tests"""

    def open_data_stream(
        self,
        first: bool = False,
        second: bool = False,
        third: bool = False,
        timeout: float = 5,
    ) -> DataStreamContextManager:
        """Stream sensor data"""

        return DataStreamContextManager(self, first, second, third)


# -- Functions ----------------------------------------------------------------


async def test(identifier):
    async with PerfNetwork() as network:
        await network.reset_node("STU 1")
        await network.connect_sensor_device(identifier)

        node = "STH 1"
        name = await network.get_name(node)
        mac_address = await network.get_mac_address(node)
        print(
            f"Connected to sensor device “{name}” with MAC "
            f"address “{mac_address}”"
        )

        start = time()
        async with network.open_data_stream(first=True) as stream:
            async for data in stream:
                message = Message(data)
                print(
                    f"Received message: {message} from"
                    f" {time() - start:.3f} s ago"
                )
                sleep(10)  # Waste time to keep messages in buffer


# -- Main ---------------------------------------------------------------------

if __name__ == "__main__":
    run(test(0))
