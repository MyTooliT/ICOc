"""Support for creating a connection to the ICOtronic system"""

# -- Imports ------------------------------------------------------------------

from __future__ import annotations

from sys import platform
from types import TracebackType
from typing import Type

from can import Bus, BusABC, Notifier
from can.interfaces.pcan.pcan import PcanError

from icotronic.can.network import CANInitError, Logger
from icotronic.can.spu import SPU
from icotronic.can.stu import STU
from icotronic.config import settings

# -- Classes ------------------------------------------------------------------


class Connection:
    """Basic class to initialize CAN communication"""

    def __init__(self) -> None:
        """Create a network without initializing the CAN connection

        To actually connect to the CAN bus you need to use the async context
        manager, provided by this class. If you want to manage the connection
        yourself, please just use `__aenter__` and `__aexit__` manually.

        Examples
        --------

        Create a new network (without connecting to the CAN bus)

        >>> network = Connection()

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

    async def __aenter__(self) -> STU:
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
        ...     async with Connection() as network:
        ...         pass
        >>> run(connect_can_context())

        Create and shutdown the connection explicitly

        >>> async def connect_can_manual():
        ...     network = Connection()
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

        return STU(SPU(self.bus, self.notifier))

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

        notifier = self.notifier
        if notifier is not None:
            notifier.stop()

        bus = self.bus
        if bus is not None:
            bus.__exit__(exception_type, exception_value, traceback)
            bus.shutdown()


# -- Main ---------------------------------------------------------------------

if __name__ == "__main__":
    from doctest import testmod

    testmod()
