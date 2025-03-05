"""Support for communicating with the Stationary Transceiver Unit (STU)"""

# -- Imports ------------------------------------------------------------------

from __future__ import annotations

from asyncio import sleep
from contextlib import asynccontextmanager
from time import time
from typing import AsyncGenerator

from netaddr import EUI

from icotronic.can.network import STHDeviceInfo
from icotronic.can.node import NodeId
from icotronic.can.sensor import SensorDevice
from icotronic.can.spu import SPU
from icotronic.can.status import State
from icotronic.utility.data import convert_bytes_to_text

# -- Classes ------------------------------------------------------------------


class STU:
    """Communicate and control a connected STU"""

    def __init__(self, spu: SPU) -> None:
        """Initialize the STU

        spu:
            The SPU object that created this STU instance

        Examples
        --------

        >>> from asyncio import run
        >>> from icotronic.can.connection import Connection

        Create an STU object

        >>> async def create_stu():
        ...     async with Connection() as stu:
        ...         pass # call some coroutines of `stu` object
        >>> run(create_stu())

        """

        self.spu = spu
        self.id = NodeId("STU 1")

    async def reset(self) -> None:
        """Reset the STU

        Examples
        --------

        >>> from asyncio import run
        >>> from icotronic.can.connection import Connection

        Reset the current STU

        >>> async def reset():
        ...     async with Connection() as stu:
        ...         await stu.reset()
        >>> run(reset())

        """

        await self.spu.reset_node(self.id)

    async def get_state(self) -> State:
        """Get the current state of the STU

        Examples
        --------

        >>> from asyncio import run
        >>> from icotronic.can.connection import Connection

        Get state of STU 1

        >>> async def get_state():
        ...     async with Connection() as stu:
        ...         return await stu.get_state()
        >>> run(get_state())
        Get State, Location: Application, State: Operating

        """

        return await self.spu.get_state(self.id)

    async def activate_bluetooth(self) -> None:
        """Activate Bluetooth on the STU

        Examples
        --------

        >>> from asyncio import run
        >>> from icotronic.can.connection import Connection

        Activate Bluetooth on the STU

        >>> async def activate():
        ...     async with Connection() as stu:
        ...         await stu.activate_bluetooth()
        >>> run(activate())

        """

        await self.spu._request_bluetooth(  # pylint: disable=protected-access
            node=self.id,
            subcommand=1,
            description=f"activate Bluetooth of node “{self.id}”",
            response_data=6 * [0],  # type: ignore[arg-type]
        )

    async def deactivate_bluetooth(self) -> None:
        """Deactivate Bluetooth on the STU

        Examples
        --------

        >>> from asyncio import run
        >>> from icotronic.can.connection import Connection

        Deactivate Bluetooth on STU 1

        >>> async def deactivate_bluetooth():
        ...     async with Connection() as stu:
        ...         await stu.deactivate_bluetooth()
        >>> run(deactivate_bluetooth())

        """

        await self.spu._request_bluetooth(  # pylint: disable=protected-access
            node=self.id,
            subcommand=9,
            description=f"deactivate Bluetooth on “{self.id}”",
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
        >>> from icotronic.can.connection import Connection

        Get the number of available Bluetooth devices at STU 1

        >>> async def get_number_bluetooth_devices():
        ...     async with Connection() as stu:
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

        # pylint: disable=protected-access
        answer = await self.spu._request_bluetooth(
            node=self.id,
            subcommand=2,
            description=f"get available Bluetooth devices of node “{self.id}”",
        )
        # pylint: enable=protected-access

        available_devices = int(convert_bytes_to_text(answer.data[2:]))

        return available_devices

    async def get_name(self, device_number: int) -> str:
        """Retrieve the name of a sensor device

        Parameters
        ----------

        device_number:
            The number of the Bluetooth device (0 up to the number of
            available devices - 1)

        Returns
        -------

        The (Bluetooth broadcast) name of the device

        Examples
        --------

        >>> from asyncio import run
        >>> from icotronic.can.connection import Connection

        Get Bluetooth advertisement name of device “0” from STU 1

        >>> async def get_bluetooth_device_name():
        ...     async with Connection() as stu:
        ...         await stu.activate_bluetooth()
        ...         # We assume that at least one STH is available
        ...         return await stu.get_name(0)
        >>> name = run(get_bluetooth_device_name())
        >>> isinstance(name, str)
        True
        >>> 0 <= len(name) <= 8
        True

        """

        return await self.spu.get_name(
            node=self.id, device_number=device_number
        )

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

        >>> from asyncio import run
        >>> from icotronic.can.connection import Connection

        Connect to device “0”

        >>> async def connect_bluetooth_device_number():
        ...     async with Connection() as stu:
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

        # pylint: disable=protected-access
        response = await self.spu._request_bluetooth(
            node=self.id,
            subcommand=7,
            device_number=device_number,
            description=f"connect to “{device_number}” from “{self.id}”",
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
        >>> from icotronic.can.connection import Connection

        Check connection of device “0” to STU

        >>> async def check_bluetooth_connection():
        ...     async with Connection() as stu:
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

        # pylint: disable=protected-access
        response = await self.spu._request_bluetooth(
            node=self.id,
            subcommand=8,
            response_data=[None, *(5 * [0])],
            description=(
                f"check if “{self.id}” is connected to a Bluetooth device"
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

        >>> from asyncio import run
        >>> from icotronic.can.connection import Connection

        Retrieve the RSSI of a disconnected STH

        >>> async def get_bluetooth_rssi():
        ...     async with Connection() as stu:
        ...         await stu.activate_bluetooth()
        ...         # We assume that at least one STH is available
        ...         # Get the RSSI of device “0”
        ...         return await stu.get_rssi(0)
        >>> rssi = run(get_bluetooth_rssi())
        >>> -70 < rssi < 0
        True

        """

        return await self.spu.get_rssi(
            node=self.id, device_number=device_number
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

        >>> from asyncio import run
        >>> from icotronic.can.connection import Connection

        Retrieve the MAC address of STH 1

        >>> async def get_bluetooth_mac():
        ...     async with Connection() as stu:
        ...         await stu.activate_bluetooth()
        ...         return await stu.get_mac_address(0)
        >>> mac_address = run(get_bluetooth_mac())
        >>> isinstance(mac_address, EUI)
        True
        >>> mac_address != EUI(0)
        True

        """

        return await self.spu.get_mac_address(self.id, device_number)

    async def get_sensor_devices(self) -> list[STHDeviceInfo]:
        """Retrieve a list of available sensor devices

        Returns
        -------

        A list of available devices including:

        - device number,
        - name,
        - MAC address and
        - RSSI

        for each device

        Examples
        --------

        >>> from asyncio import run, sleep
        >>> from netaddr import EUI
        >>> from icotronic.can.connection import Connection

        Retrieve the list of Bluetooth devices at STU 1

        >>> async def get_sensor_devices():
        ...     async with Connection() as stu:
        ...         # We assume that at least one sensor device is available
        ...         devices = []
        ...         while not devices:
        ...             devices = await stu.get_sensor_devices()
        ...             await sleep(0.1)
        ...
        ...         return devices
        >>> devices = run(get_sensor_devices())
        >>> len(devices) >= 1
        True
        >>> device = devices[0]

        >>> device.device_number
        0

        >>> isinstance(device.name, str)
        True
        >>> 0 <= len(device.name) <= 8
        True

        >>> -80 < device.rssi < 0
        True

        >>> isinstance(device.mac_address, EUI)
        True

        """

        await self.activate_bluetooth()
        available_devices = await self.get_available_devices()
        devices = []
        for device in range(available_devices):
            mac_address = await self.get_mac_address(device)
            rssi = await self.get_rssi(device)
            name = await self.get_name(device)

            devices.append(
                STHDeviceInfo(
                    device_number=device,
                    mac_address=mac_address,
                    name=name,
                    rssi=rssi,
                )
            )

        return devices

    @asynccontextmanager
    async def connect_sensor_device(
        self, identifier: int | str | EUI
    ) -> AsyncGenerator[SensorDevice]:
        """Connect to a sensor device (e.g. SHA, SMH or STH)

        Parameters
        ----------

        identifier:
            The

            - MAC address (`EUI`),
            - name (`str`), or
            - device number (`int`)

            of the sensor device we want to connect to

        Example
        -------

        >>> from asyncio import run
        >>> from icotronic.can.connection import Connection

        Connect to the sensor device with device number `0`

        >>> async def connect_sensor_device():
        ...     async with Connection() as stu:
        ...         async with stu.connect_sensor_device(0):
        ...             connected = await stu.is_connected()
        ...         after = await stu.is_connected()
        ...         return (connected, after)
        >>> run(connect_sensor_device())
        (True, False)

        """

        def get_sensor_device(
            devices: list[STHDeviceInfo], identifier: int | str | EUI
        ) -> STHDeviceInfo | None:
            """Get the MAC address of a sensor device"""

            for device in devices:
                if (
                    isinstance(identifier, str)
                    and device.name == identifier
                    or isinstance(identifier, int)
                    and device.device_number == identifier
                    or device.mac_address == identifier
                ):
                    return device

            return None

        if not isinstance(identifier, (EUI, int, str)):
            raise TypeError(
                "Identifier must be int, str or EUI, not "
                f"{type(identifier).__name__}"
            )

        await self.activate_bluetooth()

        # We wait for a certain amount of time for the connection to the
        # device to take place
        timeout_in_s = 20
        end_time = time() + timeout_in_s

        sensor_device = None
        sensor_devices: list[STHDeviceInfo] = []
        while sensor_device is None:
            if time() > end_time:
                sensor_devices_representation = "\n".join(
                    [repr(device) for device in sensor_devices]
                )
                device_info = (
                    "Found the following sensor devices:\n"
                    f"{sensor_devices_representation}"
                    if len(sensor_devices) > 0
                    else "No sensor devices found"
                )

                identifier_description = (
                    "MAC address"
                    if isinstance(identifier, EUI)
                    else (
                        "device_number"
                        if isinstance(identifier, int)
                        else "name"
                    )
                )
                raise TimeoutError(
                    "Unable to find sensor device with "
                    f"{identifier_description} “{identifier}” in "
                    f"{timeout_in_s} seconds\n\n{device_info}"
                )

            sensor_devices = await self.get_sensor_devices()
            sensor_device = get_sensor_device(sensor_devices, identifier)
            if sensor_device is None:
                await sleep(0.1)

        connection_attempt_time = time()
        disconnected = True
        while disconnected:
            await self.connect_with_device_number(sensor_device.device_number)
            retry_time_s = 3
            end_time_retry = time() + retry_time_s
            while time() < end_time_retry:
                if time() > end_time:
                    connection_time = time() - connection_attempt_time
                    raise TimeoutError(
                        "Unable to connect to sensor device"
                        f" “{sensor_device}” in"
                        f" {connection_time:.3f} seconds"
                    )

                if await self.is_connected():
                    disconnected = False
                    break

                await sleep(0.1)

        try:
            yield SensorDevice(self.spu)
        finally:
            await self.deactivate_bluetooth()


# -- Main ---------------------------------------------------------------------

if __name__ == "__main__":
    from doctest import testmod

    testmod()
