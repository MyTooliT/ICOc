# -- Imports ------------------------------------------------------------------

from os import environ, pathsep
from unittest import main as unittest_main

from mytoolit.config import settings
from mytoolit.test.production import TestNode
from mytoolit.test.unit import ExtendedTestRunner

from mytoolit.old.MyToolItNetworkNumbers import MyToolItNetworkNr
from mytoolit.old.MyToolItCommands import (int_to_mac_address, MyToolItBlock,
                                           MyToolItProductData)

# -- Class --------------------------------------------------------------------


class TestSTU(TestNode):
    """This class contains tests for the Stationary Transceiver Unit (STU)"""

    def _read_data(self):
        """Read data from connected STU"""

        cls = type(self)

        cls.bluetooth_mac = int_to_mac_address(
            self.can.BlueToothAddress(MyToolItNetworkNr['STU1']))

        index = self.can.cmdSend(MyToolItNetworkNr['STU1'],
                                 MyToolItBlock['Product Data'],
                                 MyToolItProductData['Firmware Version'], [])
        version = self.can.getReadMessageData(index)[-3:]
        cls.firmware_version = '.'.join(map(str, version))

        cls.release_name = self.can.get_node_release_name('STU1')

    def test__firmware_flash(self):
        """Upload bootloader and application into STU

        Please note the additional underscore in the method name that makes
        sure this test case is executed before all other test cases.
        """

        self._test_firmware_flash()

    def test_connection(self):
        """Check connection to STU"""

        self._test_connection()

    def test_eeprom(self):
        """Test if reading and writing the EEPROM works"""

        cls = type(self)

        # ========
        # = Name =
        # ========

        read_name = self.can.read_eeprom_name()
        expected_name = "Valerie"
        self.assertEqual(
            read_name, expected_name,
            f"Read name “{read_name}” does not match expected name " +
            f"“{expected_name}”")

        cls.name = read_name

        # ================
        # = Product Data =
        # ================

        super()._test_eeprom_product_data()

        # ==============
        # = Statistics =
        # ==============

        super()._test_eeprom_statistics()

        # =================
        # = EEPROM Status =
        # =================

        super()._test_eeprom_status()


# -- Main ---------------------------------------------------------------------


def main():
    # Add path to Simplicity Commander (`commander`) — We do this to ensure,
    # that we can call the command directly, without adding the path before
    # the tool’s name.
    environ['PATH'] += (pathsep + pathsep.join(settings.commands.path.windows))

    unittest_main(testRunner=ExtendedTestRunner,
                  module="mytoolit.test.production.stu")


if __name__ == "__main__":
    main()
