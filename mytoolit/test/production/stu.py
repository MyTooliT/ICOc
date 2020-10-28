# -- Imports ------------------------------------------------------------------

from os.path import abspath, dirname
from sys import path as module_path
from unittest import main

# Add path for custom libraries
repository_root = dirname(dirname(dirname(dirname(abspath(__file__)))))
module_path.append(repository_root)

from mytoolit.test.production import (TestNode, create_attribute,
                                      filter_undefined_attributes)
from mytoolit.unittest import ExtendedTestRunner

from MyToolItNetworkNumbers import MyToolItNetworkNr
from MyToolItCommands import (int_to_mac_address, MyToolItBlock,
                              MyToolItProductData)

# -- Class --------------------------------------------------------------------


class TestSTU(TestNode):
    """This class contains tests for the Stationary Transceiver Unit (STU)"""

    @classmethod
    def _collect_node_data(cls):
        """Collect data about STU

        Returns
        -------

        An iterable of defined STU attributes stored in simple name space
        objects
        """

        possible_attributes = [
            create_attribute("Bluetooth Address", "{cls.bluetooth_mac}"),
            create_attribute("Firmware Version", "{cls.firmware_version}"),
            create_attribute("Release Name", "{cls.release_name}", pdf=False),
        ]

        return filter_undefined_attributes(cls, possible_attributes)

    def _read_data(self):
        """Read data from connected STU"""

        cls = type(self)

        cls.bluetooth_mac = int_to_mac_address(
            self.can.BlueToothAddress(MyToolItNetworkNr['STU1']))

        index = self.can.cmdSend(MyToolItNetworkNr['STU1'],
                                 MyToolItBlock['ProductData'],
                                 MyToolItProductData['FirmwareVersion'], [])
        version = self.can.getReadMessageData(index)[-3:]
        cls.firmware_version = '.'.join(map(str, version))

        cls.release_name = self.can.get_node_release_name('STU1')

    def test__firmware_flash(self):
        """Upload bootloader and application into STU

        Please note the additional underscore in the method name that makes
        sure this test case is executed before all other test cases.
        """

        self._test_firmware_flash('STU')


# -- Main ---------------------------------------------------------------------

if __name__ == "__main__":
    main(testRunner=ExtendedTestRunner)
