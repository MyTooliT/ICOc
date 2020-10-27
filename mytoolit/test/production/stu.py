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
from MyToolItCommands import int_to_mac_address

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
        ]

        return filter_undefined_attributes(cls, possible_attributes)

    def _read_data(self):
        """Read data from connected STU"""

        cls = type(self)

        cls.bluetooth_mac = int_to_mac_address(
            self.can.BlueToothAddress(MyToolItNetworkNr['STU1']))

    def test_test(self):
        pass


# -- Main ---------------------------------------------------------------------

if __name__ == "__main__":
    main(testRunner=ExtendedTestRunner)
