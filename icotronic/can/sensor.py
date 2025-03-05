"""Support for sensor devices (SHA, SMH and STH)"""

# -- Imports ------------------------------------------------------------------

from __future__ import annotations

from icotronic.can.constants import ADVERTISEMENT_TIME_EEPROM_TO_MS
from icotronic.can.network import Times
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

        >>> from asyncio import run, sleep
        >>> from icotronic.can.connection import Connection

        Reset a sensor device

        >>> async def reset():
        ...     async with Connection() as stu:
        ...         # We assume that at least one sensor device is available
        ...         async with stu.connect_sensor_device(0) as sensor_device:
        ...             await sensor_device.reset()
        ...             # Wait some time for reset to take place
        ...             await sleep(1)
        >>> run(reset())

        """

        await self.spu.reset_node(self.id)

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

        return await self.spu.get_state(self.id)

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

        return await self.spu.get_name(node=self.id, device_number=0xFF)

    async def set_name(self, name: str) -> None:
        """Set the name of a sensor device

        Parameters
        ----------

        name:
            The new name for the device

        Examples
        --------

        >>> from asyncio import run
        >>> from icotronic.can.connection import Connection

        Change the name of a sensor device

        >>> async def test_naming(name):
        ...     async with Connection() as stu:
        ...         # We assume that at least one sensor device is available
        ...         # and that this device currently does not have the name
        ...         # specified in the variable `name`.
        ...         async with stu.connect_sensor_device(0) as sensor_device:
        ...             before = await sensor_device.get_name()
        ...             await sensor_device.set_name(name)
        ...             updated = await sensor_device.get_name()
        ...             await sensor_device.set_name(before)
        ...             after = await sensor_device.get_name()
        ...             return before, updated, after
        >>> before, updated, after = run(test_naming("Hello"))
        >>> before != "Hello"
        True
        >>> updated
        'Hello'
        >>> before == after
        True

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

        node = self.id
        # Use 0 bytes at end of names that are shorter than 8 bytes
        bytes_name.extend([0] * (8 - length_name))
        description = f"name of “{node}”"
        self_addressing = 0xFF

        # pylint: disable=protected-access

        await self.spu._request_bluetooth(
            node=node,
            subcommand=3,
            device_number=self_addressing,
            data=bytes_name[:6],
            description=f"set first part of {description}",
        )

        await self.spu._request_bluetooth(
            node=node,
            subcommand=4,
            device_number=self_addressing,
            data=bytes_name[6:] + [0] * 4,
            description=f"set second part of {description}",
        )

        # pylint: enable=protected-access

    async def get_energy_mode_reduced(self) -> Times:
        """Read the reduced energy mode (mode 1) sensor device time values

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

        >>> from asyncio import run
        >>> from icotronic.can.connection import Connection

        Retrieve the reduced energy time values of a sensor device

        >>> async def read_energy_mode_reduced():
        ...     async with Connection() as stu:
        ...         # We assume that at least one sensor device is available
        ...         async with stu.connect_sensor_device(0) as sensor_device:
        ...             return await sensor_device.get_energy_mode_reduced()
        >>> times = run(read_energy_mode_reduced())
        >>> round(times.advertisement)
        1250
        >>> times.sleep
        300000

        """

        self_addressing = 0xFF
        # pylint: disable=protected-access
        response = await self.spu._request_bluetooth(
            node=self.id,
            device_number=self_addressing,
            subcommand=13,
            description="read reduced energy time values of sensor device",
        )
        # pylint: enable=protected-access

        wait_time = int.from_bytes(response.data[2:6], byteorder="little")
        advertisement_time = (
            int.from_bytes(response.data[6:], byteorder="little")
            * ADVERTISEMENT_TIME_EEPROM_TO_MS
        )

        return Times(sleep=wait_time, advertisement=advertisement_time)


# -- Main ---------------------------------------------------------------------

if __name__ == "__main__":
    from doctest import run_docstring_examples

    run_docstring_examples(
        SensorDevice.get_energy_mode_reduced,
        globals(),
        verbose=True,
    )
