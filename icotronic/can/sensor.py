"""Support for sensor devices (SHA, SMH and STH)"""

# -- Imports ------------------------------------------------------------------

from __future__ import annotations

from netaddr import EUI

from icotronic.can.constants import (
    ADVERTISEMENT_TIME_EEPROM_TO_MS,
    DEVICE_NUMBER_SELF_ADDRESSING,
)
from icotronic.can.adc import ADCConfiguration
from icotronic.can.message import Message
from icotronic.can.network import Times
from icotronic.can.streaming import (
    StreamingConfiguration,
    StreamingData,
    StreamingFormat,
)
from icotronic.can.status import State
from icotronic.can.spu import SPU
from icotronic.config import settings

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

        # pylint: disable=protected-access

        await self.spu._request_bluetooth(
            node=node,
            subcommand=3,
            device_number=DEVICE_NUMBER_SELF_ADDRESSING,
            data=bytes_name[:6],
            description=f"set first part of {description}",
        )

        await self.spu._request_bluetooth(
            node=node,
            subcommand=4,
            device_number=DEVICE_NUMBER_SELF_ADDRESSING,
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

        # pylint: disable=protected-access
        response = await self.spu._request_bluetooth(
            node=self.id,
            device_number=DEVICE_NUMBER_SELF_ADDRESSING,
            subcommand=13,
            description="get reduced energy time values of sensor device",
        )
        # pylint: enable=protected-access

        wait_time = int.from_bytes(response.data[2:6], byteorder="little")
        advertisement_time = (
            int.from_bytes(response.data[6:], byteorder="little")
            * ADVERTISEMENT_TIME_EEPROM_TO_MS
        )

        return Times(sleep=wait_time, advertisement=advertisement_time)

    async def set_energy_mode_reduced(
        self, times: Times | None = None
    ) -> None:
        """Writes the time values for the reduced energy mode (mode 1)

        See also:

        - https://mytoolit.github.io/Documentation/#sleep-advertisement-times

        Parameters
        ----------

        times:
            The values for the advertisement time in the reduced energy mode
            in milliseconds and the time until the device will go into the low
            energy mode (mode 1) from the disconnected state – if there is no
            activity – in milliseconds.

            If you do not specify these values then the default values from
            the configuration will be used

        Examples
        --------

        >>> from asyncio import run
        >>> from icotronic.can.connection import Connection


        Read and write the reduced energy time values of a sensor device

        >>> async def read_write_energy_mode_reduced(sleep, advertisement):
        ...     async with Connection() as stu:
        ...         # We assume that at least one sensor device is available
        ...         async with stu.connect_sensor_device(0) as sensor_device:
        ...             await sensor_device.set_energy_mode_reduced(
        ...                 Times(sleep=sleep, advertisement=advertisement))
        ...             times = await sensor_device.get_energy_mode_reduced()
        ...
        ...             # Overwrite changed values with default config values
        ...             await sensor_device.set_energy_mode_reduced()
        ...
        ...             return times
        >>> times = run(read_write_energy_mode_reduced(200_000, 2000))
        >>> times.sleep
        200000
        >>> round(times.advertisement)
        2000

        """

        if times is None:
            time_settings = settings.sensory_device.bluetooth
            times = Times(
                sleep=time_settings.sleep_time_1,
                advertisement=time_settings.advertisement_time_1,
            )

        sleep_time = times.sleep
        advertisement_time = round(
            times.advertisement / ADVERTISEMENT_TIME_EEPROM_TO_MS
        )

        data = list(
            sleep_time.to_bytes(4, "little")
            + advertisement_time.to_bytes(2, "little")
        )

        # pylint: disable=protected-access
        await self.spu._request_bluetooth(
            node=self.id,
            device_number=DEVICE_NUMBER_SELF_ADDRESSING,
            subcommand=14,
            data=data,
            response_data=list(data),
            description="set reduced energy time values of sensor device",
        )
        # pylint: enable=protected-access

    async def get_energy_mode_lowest(self) -> Times:
        """Read the reduced lowest energy mode (mode 2) time values

        See also:

        - https://mytoolit.github.io/Documentation/#sleep-advertisement-times

        Returns
        -------

        A tuple containing the advertisement time in the lowest energy mode in
        milliseconds and the time until the device will switch from the
        reduced energy mode (mode 1) to the lowest energy mode (mode 2) – if
        there is no activity – in milliseconds

        Example
        -------

        >>> from asyncio import run
        >>> from icotronic.can.connection import Connection

        Retrieve the reduced energy time values of a sensor device

        >>> async def read_energy_mode_lowest():
        ...     async with Connection() as stu:
        ...         # We assume that at least one sensor device is available
        ...         async with stu.connect_sensor_device(0) as sensor_device:
        ...             return await sensor_device.get_energy_mode_lowest()
        >>> times = run(read_energy_mode_lowest())
        >>> round(times.advertisement)
        2500
        >>> times.sleep
        259200000

        """

        # pylint: disable=protected-access
        response = await self.spu._request_bluetooth(
            node=self.id,
            device_number=DEVICE_NUMBER_SELF_ADDRESSING,
            subcommand=15,
            description="get lowest energy mode time values of sensor device",
        )
        # pylint: enable=protected-access

        wait_time = int.from_bytes(response.data[2:6], byteorder="little")
        advertisement_time = (
            int.from_bytes(response.data[6:], byteorder="little")
            * ADVERTISEMENT_TIME_EEPROM_TO_MS
        )

        return Times(sleep=wait_time, advertisement=advertisement_time)

    async def set_energy_mode_lowest(self, times: Times | None = None) -> None:
        """Writes the time values for the lowest energy mode (mode 2)

        See also:

        - https://mytoolit.github.io/Documentation/#sleep-advertisement-times

        Parameters
        ----------

        times:
            The values for the advertisement time in the reduced energy mode
            in milliseconds and the time until the device will go into the
            lowest energy mode (mode 2) from the reduced energy mode (mode 1)
            – if there is no activity – in milliseconds.

            If you do not specify these values then the default values from
            the configuration will be used

        Example
        -------

        >>> from asyncio import run
        >>> from icotronic.can.connection import Connection

        Read and write the reduced energy time values of a sensor device

        >>> async def read_write_energy_mode_lowest(sleep, advertisement):
        ...     async with Connection() as stu:
        ...         # We assume that at least one sensor device is available
        ...         async with stu.connect_sensor_device(0) as sensor_device:
        ...             await sensor_device.set_energy_mode_lowest(
        ...                 Times(sleep=sleep, advertisement=advertisement))
        ...             times = await sensor_device.get_energy_mode_lowest()
        ...
        ...             # Overwrite changed values with default config values
        ...             await sensor_device.set_energy_mode_lowest()
        ...
        ...             return times
        >>> times = run(read_write_energy_mode_lowest(200_000, 2000))
        >>> times.sleep
        200000
        >>> round(times.advertisement)
        2000

        """

        if times is None:
            time_settings = settings.sensory_device.bluetooth
            times = Times(
                sleep=time_settings.sleep_time_2,
                advertisement=time_settings.advertisement_time_2,
            )

        sleep_time = times.sleep
        advertisement_time = round(
            times.advertisement / ADVERTISEMENT_TIME_EEPROM_TO_MS
        )

        data = list(
            sleep_time.to_bytes(4, "little")
            + advertisement_time.to_bytes(2, "little")
        )

        # pylint: disable=protected-access
        await self.spu._request_bluetooth(
            node=self.id,
            device_number=DEVICE_NUMBER_SELF_ADDRESSING,
            subcommand=16,
            data=data,
            response_data=list(data),
            description="set reduced energy time values of sensor device",
        )
        # pylint: enable=protected-access

    async def get_mac_address(self) -> EUI:
        """Retrieve the MAC address of the sensor device

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
        ...         # We assume that at least one sensor device is available
        ...         async with stu.connect_sensor_device(0) as sensor_device:
        ...             return await sensor_device.get_mac_address()
        >>> mac_address = run(get_bluetooth_mac())
        >>> isinstance(mac_address, EUI)
        True
        >>> mac_address != EUI(0)
        True

        """

        return await self.spu.get_mac_address(
            self.id, DEVICE_NUMBER_SELF_ADDRESSING
        )

    async def read_streaming_data_single(
        self,
        channels=StreamingConfiguration(first=True, second=True, third=True),
    ) -> StreamingData:
        """Read a single set of raw ADC values from the sensor device

        Parameters
        ----------

        channels:
            Specifies which of the three measurement channels should be
            enabled or disabled

        Returns
        -------

        The latest three ADC values measured by the sensor device

        Examples
        --------

        >>> from asyncio import run
        >>> from icotronic.can.connection import Connection

        Read a single value from all three measurement channels

        >>> async def read_sensor_values():
        ...     async with Connection() as stu:
        ...         # We assume that at least one sensor device is available
        ...         async with stu.connect_sensor_device(0) as sensor_device:
        ...             return await sensor_device.read_streaming_data_single()
        >>> data = run(read_sensor_values())
        >>> len(data.values)
        3
        >>> all([0 <= value <= 0xffff for value in data.values])
        True

        """

        streaming_format = StreamingFormat(
            channels=channels,
            sets=1,
        )

        node = self.id
        # pylint: disable=protected-access
        response = await self.spu._request(
            Message(
                block="Streaming",
                block_command="Data",
                sender=self.spu.id,
                receiver=self.id,
                request=True,
                data=[streaming_format.value],
            ),
            description=f"read single set of streaming values from “{node}”",
        )
        # pylint: enable=protected-access
        values = [
            int.from_bytes(word, byteorder="little")
            for word in (
                response.data[2:4],
                response.data[4:6],
                response.data[6:8],
            )
        ]
        assert len(values) == 2 or len(values) == 3

        data = StreamingData(
            values=values,
            timestamp=response.timestamp,
            counter=response.data[1],
        )

        return data

    async def read_adc_configuration(self) -> ADCConfiguration:
        """Read the current ADC configuration

        Returns
        -------

        The ADC configuration of the sensor node

        Examples
        --------

        >>> from asyncio import run
        >>> from icotronic.can.connection import Connection

        Read ADC sensor config of sensor device with device id 0

        >>> async def read_adc_config():
        ...     async with Connection() as stu:
        ...         # We assume that at least one sensor device is available
        ...         async with stu.connect_sensor_device(0) as sensor_device:
        ...             return await sensor_device.read_adc_configuration()
        >>> run(read_adc_config()) # doctest:+NORMALIZE_WHITESPACE
        Get, Prescaler: 2, Acquisition Time: 8, Oversampling Rate: 64,
        Reference Voltage: 3.3 V

        """

        node = self.id

        message = Message(
            block="Configuration",
            block_command="Get/Set ADC Configuration",
            sender=self.spu.id,
            receiver=node,
            request=True,
            data=[0] * 8,
        )

        # pylint: disable=protected-access
        response = await self.spu._request(
            message, description=f"Read ADC configuration of “{node}”"
        )
        # pylint: enable=protected-access

        return ADCConfiguration(response.data[0:5])


# -- Main ---------------------------------------------------------------------

if __name__ == "__main__":
    from doctest import run_docstring_examples

    run_docstring_examples(
        SensorDevice.read_adc_configuration,
        globals(),
        verbose=True,
    )
