# -- Imports ------------------------------------------------------------------

from mytoolit.can import Node
from mytoolit.config import settings
from mytoolit.test.production import TestNode

from mytoolit.old.MyToolItCommands import (
    MyToolItBlock,
    MyToolItProductData,
    int_to_mac_address,
)

# -- Classes ------------------------------------------------------------------


class TestSensorDevice(TestNode):
    """This class contains support code for sensor devices (SMH & STH)"""

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
        cls.name = settings.sth_name()

        new_network = hasattr(self.can, 'bus')
        self.loop.run_until_complete(
            read_data_new()) if new_network else read_data_old()
