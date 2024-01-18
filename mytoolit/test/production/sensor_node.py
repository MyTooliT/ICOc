"""Shared test code for sensory nodes in the ICOtronic system"""

# -- Imports ------------------------------------------------------------------

from time import sleep

from mytoolit.config import settings
from mytoolit.can.node import Node
from mytoolit.test.production.node import TestNode

# -- Classes ------------------------------------------------------------------


class TestSensorNode(TestNode):
    """This class contains support code for sensor node (SMH & STH)

    You are not supposed to use this class directly, but instead use it as
    superclass for your test class. For more information, please take a look
    at the documentation of `TestNode`.

    """

    @classmethod
    def setUpClass(cls):
        """Set up data for whole test"""

        super().setUpClass()

        cls.add_attribute("Serial Number", "{cls.serial_number}", pdf=True)
        cls.add_attribute(
            "Ratio Noise Maximum", "{cls.ratio_noise_max:.3f} dB"
        )
        cls.add_attribute("Sleep Time 1", "{cls.sleep_time_1} ms", pdf=False)
        cls.add_attribute(
            "Advertisement Time 1", "{cls.advertisement_time_1} ms", pdf=False
        )
        cls.add_attribute("Sleep Time 2", "{cls.sleep_time_2} ms", pdf=False)
        cls.add_attribute(
            "Advertisement Time 2", "{cls.advertisement_time_2} ms", pdf=False
        )

    def _connect_device(self, name: str) -> None:
        """Create a connection to the device with the specified name

        Parameters
        ----------

        name:
            The (Bluetooth advertisement) name of the sensor device

        """

        super()._connect()  # Connect to STU
        self.loop.run_until_complete(self.can.connect_sensor_device(name))

    def _read_data(self):
        """Read data from connected sensor device"""

        async def read_data():
            """Read data using the new network class"""

            node = "STH 1"
            cls.bluetooth_mac = await self.can.get_mac_address(node)
            cls.bluetooth_rssi = await self.can.get_rssi(node)
            cls.firmware_version = await self.can.get_firmware_version(node)

        cls = type(self)
        self.loop.run_until_complete(read_data())

    def _test_connection_device(self):
        """Check connection to sensor device

        This tests sends a command from the STU (with the identifier of SPU1)
        to the STH/Smh and checks if the acknowledgment message from the STH
        contains the same data as the sent message (, except for switched
        sender/receiver and flipped acknowledgment bit).
        """

        # The sensor devices need a little more time to switch from the
        # “Startup” to the “Operating” state
        sleep(1)

        self.loop.run_until_complete(self._test_connection("STH 1"))

    async def _test_name(self, receiver: Node, name: str) -> str:
        """Check if writing and reading back the name of a sensor device works

        Parameters
        ----------

        receiver:
            The node where the name should be updated

        name:
            The text that should be used as name for the sensor device

        Returns
        -------

        Read back name

        """

        await self.can.write_eeprom_name(name, receiver)
        read_name = await self.can.read_eeprom_name(receiver)

        self.assertEqual(
            name,
            read_name,
            f"Written name “{name}” does not match read name “{read_name}”",
        )

        return read_name

    async def _test_eeprom_sleep_advertisement_times(self):
        """Test if reading and writing of sleep/advertisement times works"""

        async def read_write_time(
            read_function, write_function, variable, description, milliseconds
        ):
            await write_function(milliseconds)
            milliseconds_read = round(await read_function())
            setattr(type(self), variable, milliseconds_read)
            self.assertEqual(
                milliseconds_read,
                milliseconds,
                f"{description} {milliseconds_read} ms does not match "
                f" written value of {milliseconds} ms",
            )

        await read_write_time(
            read_function=self.can.read_eeprom_sleep_time_1,
            write_function=self.can.write_eeprom_sleep_time_1,
            variable="sleep_time_1",
            description="Sleep Time 1",
            milliseconds=settings.sensory_device.bluetooth.sleep_time_1,
        )

        await read_write_time(
            read_function=self.can.read_eeprom_advertisement_time_1,
            write_function=self.can.write_eeprom_advertisement_time_1,
            variable="advertisement_time_1",
            description="Advertisement Time 1",
            milliseconds=(
                settings.sensory_device.bluetooth.advertisement_time_1
            ),
        )

        await read_write_time(
            read_function=self.can.read_eeprom_sleep_time_2,
            write_function=self.can.write_eeprom_sleep_time_2,
            variable="sleep_time_2",
            description="Sleep Time 2",
            milliseconds=settings.sensory_device.bluetooth.sleep_time_2,
        )

        await read_write_time(
            read_function=self.can.read_eeprom_advertisement_time_2,
            write_function=self.can.write_eeprom_advertisement_time_2,
            variable="advertisement_time_2",
            description="Advertisement Time 2",
            milliseconds=(
                settings.sensory_device.bluetooth.advertisement_time_2
            ),
        )
