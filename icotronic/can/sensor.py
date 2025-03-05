"""Support for sensor devices (SHA, SMH and STH)"""

# -- Imports ------------------------------------------------------------------

from __future__ import annotations

from icotronic.can.status import State
from icotronic.can.spu import SPU

# -- Classes ------------------------------------------------------------------


class SensorDevice:
    """Communicate and control a connected sensor device (SHA, STH, SMH)"""

    def __init__(self, spu: SPU) -> None:
        """Initialize the sensor device

        spu:
            The SPU object used to connect to this sensor node

        """

        self.spu = spu
        self.id = "STH 1"

    async def reset(self) -> None:
        """Reset the sensor device

        Examples
        --------

        >>> from asyncio import run
        >>> from icotronic.can.connection import Connection

        Reset a sensor device

        >>> async def reset():
        ...     async with Connection() as stu:
        ...         # We assume that at least one sensor device is available
        ...         async with stu.connect_sensor_device(0) as sensor_device:
        ...             await sensor_device.reset()
        >>> run(reset())

        """

        await self.spu._reset_node(self.id)  # pylint: disable=protected-access

    async def get_state(self) -> State:
        """Get the current state of the sensor device

        Returns
        -------

        The operating state of the sensor device

        Examples
        --------

        >>> from asyncio import run
        >>> from icotronic.can.connection import Connection

        Get state of sensor device

        >>> async def get_state():
        ...     async with Connection() as stu:
        ...         # We assume that at least one sensor device is available
        ...         async with stu.connect_sensor_device(0) as sensor_device:
        ...             return await sensor_device.get_state()
        >>> run(get_state())
        Get State, Location: Application, State: Operating

        """

        return await self.spu._get_state(  # pylint: disable=protected-access
            self.id
        )

    async def get_name(self) -> str:
        """Retrieve the name of the sensor device

        Returns
        -------

        The (Bluetooth broadcast) name of the device

        Examples
        --------

        >>> from asyncio import run
        >>> from icotronic.can.connection import Connection

        Get Bluetooth advertisement name of device “0”

        >>> async def get_sensor_device_name():
        ...     async with Connection() as stu:
        ...         # We assume that at least one sensor device is available
        ...         async with stu.connect_sensor_device(0) as sensor_device:
        ...             return await sensor_device.get_name()
        >>> name = run(get_sensor_device_name())
        >>> isinstance(name, str)
        True
        >>> 0 <= len(name) <= 8
        True

        """

        return await self.spu._get_name(  # pylint: disable=protected-access
            node=self.id, device_number=0xFF
        )


# -- Main ---------------------------------------------------------------------

if __name__ == "__main__":
    from doctest import run_docstring_examples

    run_docstring_examples(
        SensorDevice.get_name,
        globals(),
        verbose=True,
    )
