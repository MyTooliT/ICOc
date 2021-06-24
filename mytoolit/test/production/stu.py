# -- Imports ------------------------------------------------------------------

from unittest import main as unittest_main

from mytoolit.test.production import TestNode
from mytoolit.test.unit import ExtendedTestRunner
from mytoolit.utility import add_commander_path_to_environment

from mytoolit.old.MyToolItNetworkNumbers import MyToolItNetworkNr
from mytoolit.old.MyToolItCommands import (int_to_mac_address, MyToolItBlock,
                                           MyToolItProductData)

# -- Class --------------------------------------------------------------------


class TestSTU(TestNode):
    """This class contains tests for the Stationary Transceiver Unit (STU)"""

    def _read_data(self):
        """Read data from connected STU"""

        def read_data_old():
            """Read data using the old network class"""
            cls.bluetooth_mac = int_to_mac_address(
                self.can.BlueToothAddress(MyToolItNetworkNr['STU1']))

            index = self.can.cmdSend(MyToolItNetworkNr['STU1'],
                                     MyToolItBlock['Product Data'],
                                     MyToolItProductData['Firmware Version'],
                                     [])
            version = self.can.getReadMessageData(index)[-3:]
            cls.firmware_version = '.'.join(map(str, version))

            cls.release_name = self.can.get_node_release_name('STU1')

        async def read_data_new():
            """Read data using the new network class"""

            node = 'STU 1'
            cls.bluetooth_mac = await self.can.get_mac_address(node)
            cls.firmware_version = await self.can.get_firmware_version(node)
            cls.release_name = await self.can.get_firmware_release_name(node)

        cls = type(self)
        new_network = hasattr(self.can, 'bus')
        self.loop.run_until_complete(
            read_data_new()) if new_network else read_data_old()

    def test__firmware_flash(self):
        """Upload bootloader and application into STU

        Please note the additional underscore in the method name that makes
        sure this test case is executed before all other test cases.
        """

        self._test_firmware_flash()

    def test_connection(self):
        """Check connection to STU"""

        self.loop.run_until_complete(self._test_connection())

    def test_eeprom(self):
        """Test if reading and writing the EEPROM works"""

        async def test_eeprom():
            """Test the EERPOM of the STU"""

            cls = type(self)

            # ========
            # = Name =
            # ========

            read_name = await self.can.read_eeprom_name()
            expected_name = "Valerie"
            self.assertEqual(
                read_name, expected_name,
                f"Read name “{read_name}” does not match expected name " +
                f"“{expected_name}”")

            cls.name = read_name

            # ================
            # = Product Data =
            # ================

            super_class = super(TestSTU, self)
            await super_class._test_eeprom_product_data()

            # ==============
            # = Statistics =
            # ==============

            await super_class._test_eeprom_statistics()

            # =================
            # = EEPROM Status =
            # =================

            await super_class._test_eeprom_status()

        self.loop.run_until_complete(test_eeprom())


# -- Main ---------------------------------------------------------------------


def main():
    add_commander_path_to_environment()
    unittest_main(testRunner=ExtendedTestRunner,
                  module="mytoolit.test.production.stu")


if __name__ == "__main__":
    main()
