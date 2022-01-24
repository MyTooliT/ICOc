# -- Imports ------------------------------------------------------------------

from time import sleep

from mytoolit.can import Node
from mytoolit.config import settings
from mytoolit.test.production import create_attribute, TestNode

from mytoolit.old.MyToolItCommands import (
    MyToolItBlock,
    MyToolItProductData,
    int_to_mac_address,
)

# -- Classes ------------------------------------------------------------------


class TestSensorNode(TestNode):
    """This class contains support code for sensor devices (SMH & STH)"""

    possible_attributes = TestNode.possible_attributes + [
        create_attribute("Ratio Noise Maximum",
                         "{cls.ratio_noise_max:.3f} dB"),
        create_attribute("Sleep Time 1", "{cls.sleep_time_1} ms", pdf=False),
        create_attribute("Advertisement Time 1",
                         "{cls.advertisement_time_1} ms",
                         pdf=False),
        create_attribute("Sleep Time 2", "{cls.sleep_time_2} ms", pdf=False),
        create_attribute("Advertisement Time 2",
                         "{cls.advertisement_time_2} ms",
                         pdf=False),
    ]

    def _connect_device(self, name: str) -> None:
        """Create a connection to the device with the specified name

        Parameters
        ----------

        name:
            The (Bluetooth advertisement) name of the sensor device

        """

        # Connect to STU
        super()._connect()
        # Connect to STH
        new_network = hasattr(self.can, 'bus')
        self.loop.run_until_complete(
            self.can.connect_sth(name)) if new_network else (
                self.can.bBlueToothConnectPollingName(
                    Node('STU 1').value, name, log=False))

    def _read_data(self):
        """Read data from connected sensor device"""

        def read_data_old():
            """Read data using the old network class"""

            cls.bluetooth_mac = int_to_mac_address(
                self.can.BlueToothAddress(Node('STH 1').value))
            cls.bluetooth_rssi = self.can.BlueToothRssi(Node('STH 1').value)

            index = self.can.cmdSend(
                Node('STH 1').value, MyToolItBlock['Product Data'],
                MyToolItProductData['Firmware Version'], [])
            version = self.can.getReadMessageData(index)[-3:]

            cls.firmware_version = '.'.join(map(str, version))

        async def read_data_new():
            """Read data using the old network class"""

            node = 'STH 1'
            cls.bluetooth_mac = await self.can.get_mac_address(node)
            cls.bluetooth_rssi = await self.can.get_rssi(node)
            cls.firmware_version = await self.can.get_firmware_version(node)

        cls = type(self)

        new_network = hasattr(self.can, 'bus')
        self.loop.run_until_complete(
            read_data_new()) if new_network else read_data_old()

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

        self.loop.run_until_complete(self._test_connection('STH 1'))

    async def _test_eeprom_sleep_advertisement_times(self):
        """Test if reading and writing of sleep/advertisement times works"""

        async def read_write_time(read_function, write_function, variable,
                                  description, milliseconds):
            await write_function(milliseconds)
            milliseconds_read = round(await read_function())
            setattr(type(self), variable, milliseconds_read)
            self.assertEqual(
                milliseconds_read, milliseconds,
                f"{description} {milliseconds_read} ms does not match "
                f" written value of {milliseconds} ms")

        await read_write_time(
            read_function=self.can.read_eeprom_sleep_time_1,
            write_function=self.can.write_eeprom_sleep_time_1,
            variable='sleep_time_1',
            description="Sleep Time 1",
            milliseconds=settings.sensory_device.bluetooth.sleep_time_1)

        await read_write_time(
            read_function=self.can.read_eeprom_advertisement_time_1,
            write_function=self.can.write_eeprom_advertisement_time_1,
            variable='advertisement_time_1',
            description="Advertisement Time 1",
            milliseconds=settings.sensory_device.bluetooth.advertisement_time_1
        )

        await read_write_time(
            read_function=self.can.read_eeprom_sleep_time_2,
            write_function=self.can.write_eeprom_sleep_time_2,
            variable='sleep_time_2',
            description="Sleep Time 2",
            milliseconds=settings.sensory_device.bluetooth.sleep_time_2)

        await read_write_time(
            read_function=self.can.read_eeprom_advertisement_time_2,
            write_function=self.can.write_eeprom_advertisement_time_2,
            variable='advertisement_time_2',
            description="Advertisement Time 2",
            milliseconds=settings.sensory_device.bluetooth.advertisement_time_2
        )
